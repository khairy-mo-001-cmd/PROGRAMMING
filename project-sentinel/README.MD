# 🛰️ Project Sentinel: Near-Earth Object Monitoring & Triage Pipeline

Project Sentinel is an end-to-end Python data pipeline for monitoring Near-Earth Objects (NEOs) using NASA's NeoWs API.

The pipeline fetches NEO close-approach data, cleans and enriches it, joins it with a simulated ground-station log, calculates operational risk features, stores the final results in SQLite, and exports a clean dataset for Power BI reporting.

## Project Goal

Astronomical monitoring produces many close-approach observations. Reviewing every object manually is inefficient.

Project Sentinel creates an operational triage workflow that helps prioritize which objects deserve immediate review based on object size and miss distance.

## Data Source

- **Source:** [NASA NeoWs API](https://api.nasa.gov/neo/rest/v1/feed)
- **Data type:** Near-Earth Object close-approach observations
- **Ingestion method:** Live REST API requests and JSON parsing
- **Current pipeline window:** Two sequential 7-day API windows

> The `ground_station_log.csv` file is simulated. It is included to demonstrate data-cleaning, missing-value handling, and data-joining skills.

## Pipeline Workflow

```text
NASA NeoWs API
   ↓
Python data extraction
   ↓
Raw ID extraction + simulated ground-station log
   ↓
Cleaning, deduplication, and feature engineering
   ↓
SQLite database + cleaned CSV export
   ↓
Power BI dashboard
```

## Key Features

- Fetches live NEO data from NASA's API.
- Deduplicates NEO records across API windows.
- Handles missing and invalid values safely.
- Imputes missing absolute magnitude values using the cohort median.
- Joins NEO observations with a simulated dirty ground-station log.
- Calculates operational risk features.
- Stores every completed pipeline execution in SQLite.
- Exports a clean CSV dataset for Power BI analysis.

## Engineered Features

| Feature | Description |
|---|---|
| `miss_distance_lunar` | Earth miss distance expressed in Lunar Distances (LD). |
| `size_to_distance_ratio` | Ratio of maximum estimated diameter to miss distance. |
| `scaled_size_to_distance_ratio` | Min-Max scaled risk indicator between 0 and 1. |
| `approach_category` | Close-approach category: `very_close`, `close`, `moderate`, or `distant`. |
| `priority_watch` | Operational triage flag for objects at least 0.14 km wide and within 10 Lunar Distances. |
| `confidence_score` | Simulated ground-station confidence value used for data-quality analysis. |

## Sentinel Priority Rule

An object is placed in the immediate review queue when:

```text
max_diameter_km >= 0.14
AND
miss_distance_lunar <= 10
```

This rule is designed for operational prioritization during the current observation window. It is not a replacement for NASA's long-term orbital hazard classification.

## Latest Pipeline Result

The latest completed run produced:

| Metric | Result |
|---|---:|
| Cleaned NEO observations | 66 |
| NASA potentially hazardous objects | 13 |
| Sentinel priority objects | 1 |
| Operational workload reduction | 98.48% |

The workload reduction is calculated as:

```text
1 - (Priority Objects / Total Processed Objects)
```

In this run, Sentinel reduced the immediate manual-review queue from 66 objects to 1 priority object.

## Validation Insight

The NASA field `is_potentially_hazardous_asteroid` and Sentinel's `priority_watch` flag answer different questions:

- **NASA classification:** Long-term potential hazard classification supplied by NASA.
- **Sentinel classification:** Immediate operational triage based on size and current miss distance.

An object may be marked as potentially hazardous by NASA but not be a current Sentinel priority if it is not passing sufficiently close during the selected observation window.

## SQLite Database

The pipeline creates the database automatically at:

```text
data/sentinel.db
```

It contains two tables:

| Table | Purpose |
|---|---|
| `pipeline_runs` | Stores metadata for each completed pipeline run. |
| `neo_observations` | Stores the cleaned and engineered NEO records for every run. |

This design preserves historical pipeline runs instead of overwriting earlier results.

## Power BI Dashboard

The Power BI dashboard includes:

- Total Near-Earth Objects.
- NASA hazardous-object count.
- Sentinel priority queue count.
- Operational workload reduction.
- Average miss distance in Lunar Distances.
- Risk map: object size versus miss distance.
- Close-approach distribution.
- Priority review queue.
- Comparison of NASA classification and Sentinel priority rules.

## How to Run

### 1. Install the required package

```powershell
py -m pip install requests
```

### 2. Run the pipeline

```powershell
py .\src\pipeline.py
```

### 3. Generated outputs

```text
data/
├── processed/
│   └── clean_data.csv
└── sentinel.db
```

## Repository Structure

```text
project-sentinel/
│
├── data/
│   ├── raw/
│   │   ├── extracted_ids.txt
│   │   └── ground_station_log.csv
│   ├── processed/
│   │   └── clean_data.csv
│   └── sentinel.db
│
├── notebooks/
│   └── exploration.ipynb
│
├── src/
│   ├── database.py
│   └── pipeline.py
│
├── generate_sentinel_log.py
└── README.MD
```

## Tools Used

- Python
- SQLite
- NASA NeoWs API
- Power BI
- CSV
- Git and GitHub

## Author

Khairy Mohammed  
