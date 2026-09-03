#!/usr/bin/env python3
"""
src/pipeline.py — Project Sentinel: Automated Near-Earth Object Triage Pipeline.

Author: Khairy Mohammed (Data Engineering Intern @ IBM)
Reviewer: Lead Data Engineer @ IBM

This module provides a pure-Python (no pandas/numpy) end-to-end data pipeline:
 1. Scrapes total cataloged NEOs count from NASA Planetary Defense page.
 2. Fetches 14 days of live NEO close-approach data from NASA NeoWs API (chained requests).
 3. Extracts unique IDs and triggers synthetic ground-station log generation.
 4. Cleans, imputes missing values (median absolute magnitude), and filters empty cohorts.
 5. Performs feature engineering (size_to_distance_ratio, approach_category, priority_watch).
 6. Joins with dirty ground station logs using safe lookup mechanisms.
 7. Performs Min-Max scaling on size_to_distance_ratio.
 8. Computes validation crosstab against NASA's hazardous flag.
 9. Exports the final cleaned dataset to data/processed/clean_data.csv.
"""

import csv
from pathlib import Path
import sys
import requests
from database import save_pipeline_results


try:
    from generate_sentinel_log import generate_sentinel_log
except ImportError:
    # Fallback if imported from inside src/
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from generate_sentinel_log import generate_sentinel_log

# Directories setup
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"

EXTRACTED_IDS_PATH = DATA_RAW_DIR / "extracted_ids.txt"
LOG_CSV_PATH = DATA_RAW_DIR / "ground_station_log.csv"
CLEAN_CSV_PATH = DATA_PROCESSED_DIR / "clean_data.csv"


# ==========================================
# Helper Functions
# ==========================================

def safe_float(value, default=None):
    """Safely cast string/numeric values to float, handling dirty entries."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    
    val_str = str(value).strip()
    if not val_str or val_str.upper() in ["N/A", "NULL", "NONE", "UNKNOWN"]:
        return default
    try:
        return float(val_str)
    except ValueError:
        return default


def compute_median(values):
    """Computes median using pure Python native sorting."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    return sorted_vals[n // 2]


# ==========================================
# Phase 1: Web Scraping & API Data Acquisition
# ==========================================

def scrape_total_known_neos() -> int:
    """Scrapes total cataloged NEO count from NASA Planetary Defense page."""
    url = "https://science.nasa.gov/science-research/planetary-science/planetary-defense/near-earth-asteroids/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    anchor_phrase = "Total number of discovered near-Earth asteroids"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html_text = response.text
        
        if anchor_phrase in html_text:
            idx = html_text.index(anchor_phrase)
            # Take a 50-character window prior to the anchor
            snippet = html_text[max(0, idx - 50):idx]
            colon_idx = snippet.rfind(":")
            if colon_idx != -1:
                number_str = snippet[:colon_idx].strip().split()[-1].replace(",", "")
                val = int(number_str)
                print(f"[Web Scrape] Successfully extracted total_known_neos: {val:,}")
                return val
    except Exception as e:
        print(f"[Web Scrape Warning] Could not extract live count ({e}). Using fallback baseline.")
    
    fallback_val = 35000
    print(f"[Web Scrape] Using default fallback: {fallback_val:,}")
    return fallback_val


def fetch_nasa_neows_data(api_key: str = "DEMO_KEY") -> list:
    """Fetches 14 days of NEO data using 2 chained 7-day windows."""
    base_url = "https://api.nasa.gov/neo/rest/v1/feed"
    # NASA API limit: max 7 days per call -> Chain 2 calls (14 days total)
    date_windows = [
        ("2026-08-01", "2026-08-07"),
        ("2026-08-08", "2026-08-14")
    ]
    
    all_records = []
    print("[API] Starting NASA NeoWs data acquisition...")
    
    for start_d, end_d in date_windows:
        params = {
            "start_date": start_d,
            "end_date": end_d,
            "api_key": api_key
        }
        try:
            res = requests.get(base_url, params=params, timeout=15)
            res.raise_for_status()
            data = res.json()
            
            # near_earth_objects is a dict keyed by date string
            neo_dict = data.get("near_earth_objects", {})
            window_count = 0
            for date_str, items in neo_dict.items():
                for item in items:
                    all_records.append(item)
                    window_count += 1
            print(f"[API] Fetched {window_count} records for window {start_d} -> {end_d}")
            
        except requests.exceptions.RequestException as err:
            print(f"[API Error] Network request failed for range {start_d} to {end_d}: {err}")
            raise
            
    print(f"[API] Total raw records retrieved: {len(all_records)}")
    return all_records


# ==========================================
# Phase 2 & 3: Data Processing & Pipeline
# ==========================================

def run_pipeline(api_key: str = "DEMO_KEY"):
    """Executes the full end-to-end Project Sentinel data pipeline."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    

    total_known_neos = scrape_total_known_neos()

    
    raw_records = fetch_nasa_neows_data(api_key=api_key)
    

    extracted_ids = [str(r["neo_reference_id"]) for r in raw_records if "neo_reference_id" in r]

    unique_ids = list(dict.fromkeys(extracted_ids))
    EXTRACTED_IDS_PATH.write_text("\n".join(unique_ids), encoding="utf-8")
    print(f"[Log Step] Extracted {len(unique_ids)} unique IDs to {EXTRACTED_IDS_PATH}")
    

    generate_sentinel_log(unique_ids, output_path=LOG_CSV_PATH, seed=42)
    

    filtered_records = []
    valid_abs_mags = []
    
    for r in raw_records:
        ca_data = r.get("close_approach_data", [])

        if not ca_data:
            continue
            
        ca = ca_data[0] 


        diam_km_max = safe_float(r.get("estimated_diameter", {}).get("kilometers", {}).get("estimated_diameter_max"))
        diam_km_min = safe_float(r.get("estimated_diameter", {}).get("kilometers", {}).get("estimated_diameter_min"))
        
        miss_km = safe_float(ca.get("miss_distance", {}).get("kilometers"))
        miss_lunar = safe_float(ca.get("miss_distance", {}).get("lunar"))
        rel_vel_kph = safe_float(ca.get("relative_velocity", {}).get("kilometers_per_hour"))
        
        abs_mag = safe_float(r.get("absolute_magnitude_h"))
        if abs_mag is not None:
            valid_abs_mags.append(abs_mag)
            
        is_pha = bool(r.get("is_potentially_hazardous_asteroid", False))
        neo_id = str(r.get("neo_reference_id", "")).strip()
        name = str(r.get("name", "")).strip()
        
        filtered_records.append({
            "neo_id": neo_id,
            "name": name,
            "max_diameter_km": diam_km_max,
            "min_diameter_km": diam_km_min,
            "miss_distance_km": miss_km,
            "miss_distance_lunar": miss_lunar,
            "relative_velocity_kph": rel_vel_kph,
            "absolute_magnitude_h": abs_mag,
            "is_potentially_hazardous_asteroid": is_pha,
            "num_close_approaches": len(ca_data),
            "total_known_neos": total_known_neos
        })
        
    print(f"[Cohort Filter] Retained {len(filtered_records)} / {len(raw_records)} records.")
    

    cohort_median_mag = compute_median(valid_abs_mags)
    for rec in filtered_records:
        if rec["absolute_magnitude_h"] is None:
            rec["absolute_magnitude_h"] = cohort_median_mag


    for rec in filtered_records:
        d_max = rec["max_diameter_km"] if rec["max_diameter_km"] is not None else 0.0
        dist_lunar = rec["miss_distance_lunar"] if rec["miss_distance_lunar"] is not None else 9999.0
        

        rec["size_to_distance_ratio"] = d_max / dist_lunar if dist_lunar > 0 else 0.0
        

        if dist_lunar <= 5.0:
            rec["approach_category"] = "very_close"
        elif dist_lunar <= 20.0:
            rec["approach_category"] = "close"
        elif dist_lunar <= 60.0:
            rec["approach_category"] = "moderate"
        else:
            rec["approach_category"] = "distant"


        if d_max >= 0.14 and dist_lunar <= 10.0:
            rec["priority_watch"] = 1
        else:
            rec["priority_watch"] = 0

    log_map = {}
    if LOG_CSV_PATH.exists():
        with LOG_CSV_PATH.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                nid = str(row.get("neo_id", "")).strip()
                obs = str(row.get("observatory_code", "")).strip()
                score = safe_float(row.get("confidence_score"))
                log_map[nid] = {
                    "observatory_code": obs if obs else "UNKNOWN",
                    "confidence_score": score
                }

    for rec in filtered_records:
        log_entry = log_map.get(rec["neo_id"], {})
        rec["observatory_code"] = log_entry.get("observatory_code", "UNMATCHED")
        rec["confidence_score"] = log_entry.get("confidence_score", None)


    ratios = [r["size_to_distance_ratio"] for r in filtered_records]
    min_x = min(ratios) if ratios else 0.0
    max_x = max(ratios) if ratios else 1.0
    range_x = max_x - min_x
    
    for rec in filtered_records:
        if range_x > 0:
            rec["scaled_size_to_distance_ratio"] = round((rec["size_to_distance_ratio"] - min_x) / range_x, 6)
        else:
            rec["scaled_size_to_distance_ratio"] = 0.0


    total_objs = len(filtered_records)
    flagged_objs = sum(1 for r in filtered_records if r["priority_watch"] == 1)
    workload_reduction = (1 - (flagged_objs / total_objs)) * 100 if total_objs > 0 else 0.0
    
    print("\n" + "="*50)
    print("PIPELINE EXECUTION SUMMARY & METRICS")
    print("="*50)
    print(f"• Total Processed Cohort (n_total): {total_objs}")
    print(f"• Priority Flagged (priority_watch=1): {flagged_objs}")
    print(f"• Headline ROI Metric: Workload Cut by {workload_reduction:.2f}%")
    run_id, database_path = save_pipeline_results(
        records=filtered_records,
        raw_record_count=len(raw_records),
    )

    print(f"[Database] Run {run_id} saved to: {database_path}")
    # 2x2 Crosstab
    crosstab = {(True, 1): 0, (True, 0): 0, (False, 1): 0, (False, 0): 0}
    for r in filtered_records:
        pair = (r["is_potentially_hazardous_asteroid"], r["priority_watch"])
        crosstab[pair] = crosstab.get(pair, 0) + 1
        
    print("\n[Validation Check: 2x2 Crosstab Matrix]")
    print(f"  NASA Hazardous (True)  & Priority (1) : {crosstab[(True, 1)]}")
    print(f"  NASA Hazardous (True)  & Routine  (0) : {crosstab[(True, 0)]}")
    print(f"  NASA Normal    (False) & Priority (1) : {crosstab[(False, 1)]}")
    print(f"  NASA Normal    (False) & Routine  (0) : {crosstab[(False, 0)]}")
    print("="*50 + "\n")


    fieldnames = [
        "neo_id", "name", "max_diameter_km", "min_diameter_km", 
        "miss_distance_km", "miss_distance_lunar", "relative_velocity_kph", 
        "absolute_magnitude_h", "is_potentially_hazardous_asteroid", 
        "num_close_approaches", "total_known_neos", "size_to_distance_ratio", 
        "scaled_size_to_distance_ratio", "approach_category", "priority_watch", 
        "observatory_code", "confidence_score"
    ]
    
    with CLEAN_CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_records)
        
    print(f"[Output Success] Clean dataset saved to: {CLEAN_CSV_PATH}")


if __name__ == "__main__":

    run_pipeline(api_key="DEMO_KEY")