"""
Project Sentinel: Automated Near-Earth Object (NEO) Clean Pipeline.

This pipeline executes direct data processing on clean NASA NeoWs API feeds:
1. Fetches close-approach data from NASA's NeoWs API.
2. Cleans, imputes, and parses raw NEO fields directly.
3. Engineers critical risk features (e.g., lunar miss distance, priority watch flag).
4. Scales normalized features using Min-Max scaling.
5. Saves the processed clean dataset to 'data/processed/clean_data.csv'.
"""

import csv
from pathlib import Path
import requests
import os 


# Constants & Configuration
API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
BASE_URL = "https://api.nasa.gov/neo/rest/v1/feed"
PROCESSED_DATA_DIR = Path("data/processed")
OUTPUT_FILE_PATH = PROCESSED_DATA_DIR / "clean_data.csv"

# Date ranges (6 weekly windows)
DATE_WINDOWS = [
    ("2026-08-01", "2026-08-08"),
    ("2026-08-08", "2026-08-14"),
    ("2026-08-15", "2026-08-21"),
    ("2026-07-15", "2026-07-21"),
    ("2026-07-08", "2026-07-14"),
    ("2026-07-01", "2026-07-07"),
]


def fetch_nasa_neo_data(
    api_key: str = API_KEY, date_windows: list = DATE_WINDOWS
) -> list:
    """Fetches near-earth objects data directly from NASA's NeoWs feed API."""
    all_asteroids = []
    print("🌐 Initiating NASA NeoWs API calls...")

    for start_date, end_date in date_windows:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "api_key": api_key,
        }
        try:
            response = requests.get(BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            for _, asteroids in data.get("near_earth_objects", {}).items():
                all_asteroids.extend(asteroids)

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Warning: Request failed for window {start_date} to {end_date}: {e}")

    print(f"✅ Successfully fetched {len(all_asteroids)} raw asteroid records.")
    return all_asteroids


def process_clean_data(raw_asteroids: list) -> list:
    """Parses clean API data, engineers target/risk features, and applies Min-Max scaling."""
    
    # Deduplicate raw asteroids by ID
    unique_asteroids = {}
    for ast in raw_asteroids:
        ast_id = str(ast.get("id", "")).strip()
        if ast_id and ast_id not in unique_asteroids:
            unique_asteroids[ast_id] = ast

    # Imputation fallback: Calculate median for missing absolute magnitude
    magnitudes = [
        float(ast["absolute_magnitude_h"])
        for ast in unique_asteroids.values()
        if ast.get("absolute_magnitude_h") is not None
    ]
    magnitudes.sort()
    median_magnitude = magnitudes[len(magnitudes) // 2] if magnitudes else 0.0

    clean_master_records = []

    for neo_id, nasa_info in unique_asteroids.items():
        approaches = nasa_info.get("close_approach_data", [])
        if not approaches:
            continue

        first_app = approaches[0]
        approach_date = first_app.get("close_approach_date")

        try:
            speed = float(
                first_app.get("relative_velocity", {}).get("kilometers_per_hour", 0)
            )
        except (ValueError, TypeError):
            speed = 0.0

        try:
            miss_dist = float(
                first_app.get("miss_distance", {}).get("kilometers", 0)
            )
        except (ValueError, TypeError):
            miss_dist = 0.0

        diameter_info = (
            nasa_info.get("estimated_diameter", {}).get("kilometers", {})
        )
        min_d = float(diameter_info.get("estimated_diameter_min", 0.0))
        max_d = float(diameter_info.get("estimated_diameter_max", 0.0))
        avg_d = (min_d + max_d) / 2.0

        abs_mag = nasa_info.get("absolute_magnitude_h")
        try:
            abs_mag = float(abs_mag) if abs_mag is not None else median_magnitude
        except (ValueError, TypeError):
            abs_mag = median_magnitude

        # Feature Engineering
        miss_distance_lunar = miss_dist / 384400.0 if miss_dist > 0 else 0.0
        priority_watch = 1 if (max_d >= 0.14 and miss_distance_lunar <= 10) else 0
        size_to_dist_ratio = (max_d / miss_distance_lunar) if miss_distance_lunar > 0 else 0.0

        if miss_distance_lunar <= 5:
            approach_category = "very_close"
        elif miss_distance_lunar <= 20:
            approach_category = "close"
        elif miss_distance_lunar <= 60:
            approach_category = "moderate"
        else:
            approach_category = "distant"

        record = {
            "asteroid_id": neo_id,
            "name": nasa_info.get("name"),
            "is_hazardous": nasa_info.get("is_potentially_hazardous_asteroid", False),
            "absolute_magnitude_h": round(abs_mag, 2),
            "estimated_diameter_min_km": round(min_d, 4),
            "estimated_diameter_max_km": round(max_d, 4),
            "avg_diameter_km": round(avg_d, 4),
            "close_approach_date": approach_date,
            "close_approach_speed_kph": round(speed, 2),
            "miss_distance_km": round(miss_dist, 2),
            "miss_distance_lunar": round(miss_distance_lunar, 4),
            "size_to_distance_ratio": size_to_dist_ratio,
            "approach_category": approach_category,
            "priority_watch": priority_watch,
        }
        clean_master_records.append(record)

    # Min-Max Scaling for size_to_distance_ratio
    if clean_master_records:
        ratios = [rec["size_to_distance_ratio"] for rec in clean_master_records]
        min_r, max_r = min(ratios), max(ratios)

        for rec in clean_master_records:
            scaled = (
                (rec["size_to_distance_ratio"] - min_r) / (max_r - min_r)
                if max_r != min_r
                else 0.0
            )
            rec["scaled_size_to_distance_ratio"] = round(scaled, 6)
            rec["size_to_distance_ratio"] = round(rec["size_to_distance_ratio"], 6)

    return clean_master_records


def run_pipeline() -> None:
    """Executes the clean Project Sentinel Data Pipeline."""
    print("🚀 Starting Clean Project Sentinel Data Pipeline...\n")

    raw_asteroids = fetch_nasa_neo_data()

    if not raw_asteroids:
        print("❌ Error: No raw records were fetched. Pipeline aborted.")
        return

    cleaned_records = process_clean_data(raw_asteroids)

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = list(cleaned_records[0].keys())

    with open(OUTPUT_FILE_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_records)

    print(f"\n💾 Cleaned data saved successfully to: {OUTPUT_FILE_PATH}")
    print(f"📊 Processed Records Count: {len(cleaned_records)}")

    # Summary Metrics
    n_total = len(cleaned_records)
    n_flagged = sum(1 for r in cleaned_records if r["priority_watch"] == 1)
    workload_reduction = (1 - (n_flagged / n_total)) * 100 if n_total > 0 else 0

    print(f"🎯 Flagged Priority Objects: {n_flagged}")
    print(f"📉 Workload Reduction Metric: {workload_reduction:.2f}%")
    print("\n✅ Pipeline execution completed successfully!")


if __name__ == "__main__":
    run_pipeline()