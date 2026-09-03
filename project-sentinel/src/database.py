import sqlite3
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "sentinel.db"


def initialize_database(connection):
    """Create the database tables if they do not already exist."""

    connection.execute("PRAGMA foreign_keys = ON")

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            executed_at_utc TEXT NOT NULL,
            raw_record_count INTEGER NOT NULL,
            processed_record_count INTEGER NOT NULL,
            priority_count INTEGER NOT NULL,
            total_known_neos INTEGER
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS neo_observations (
            observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            neo_id TEXT NOT NULL,
            name TEXT,
            max_diameter_km REAL,
            min_diameter_km REAL,
            miss_distance_km REAL,
            miss_distance_lunar REAL,
            relative_velocity_kph REAL,
            absolute_magnitude_h REAL,
            is_potentially_hazardous_asteroid INTEGER NOT NULL,
            num_close_approaches INTEGER,
            total_known_neos INTEGER,
            size_to_distance_ratio REAL,
            scaled_size_to_distance_ratio REAL,
            approach_category TEXT,
            priority_watch INTEGER NOT NULL,
            observatory_code TEXT,
            confidence_score REAL,
            FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id)
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_neo_observations_run_id
        ON neo_observations (run_id)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_neo_observations_priority_watch
        ON neo_observations (priority_watch)
        """
    )


def save_pipeline_results(records, raw_record_count):
    """
    Save one completed pipeline run and all its cleaned NEO observations.
    Returns the new run ID and database path.
    """

    if not records:
        raise ValueError("No cleaned records were provided for database storage.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    executed_at_utc = datetime.now(timezone.utc).isoformat()
    processed_record_count = len(records)
    priority_count = sum(
        1 for record in records if record.get("priority_watch") == 1
    )
    total_known_neos = records[0].get("total_known_neos")

    with sqlite3.connect(DB_PATH) as connection:
        initialize_database(connection)

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO pipeline_runs (
                executed_at_utc,
                raw_record_count,
                processed_record_count,
                priority_count,
                total_known_neos
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                executed_at_utc,
                raw_record_count,
                processed_record_count,
                priority_count,
                total_known_neos,
            ),
        )

        run_id = cursor.lastrowid

        rows_to_insert = []

        for record in records:
            rows_to_insert.append(
                (
                    run_id,
                    record.get("neo_id"),
                    record.get("name"),
                    record.get("max_diameter_km"),
                    record.get("min_diameter_km"),
                    record.get("miss_distance_km"),
                    record.get("miss_distance_lunar"),
                    record.get("relative_velocity_kph"),
                    record.get("absolute_magnitude_h"),
                    1 if record.get("is_potentially_hazardous_asteroid") else 0,
                    record.get("num_close_approaches"),
                    record.get("total_known_neos"),
                    record.get("size_to_distance_ratio"),
                    record.get("scaled_size_to_distance_ratio"),
                    record.get("approach_category"),
                    record.get("priority_watch"),
                    record.get("observatory_code"),
                    record.get("confidence_score"),
                )
            )

        cursor.executemany(
            """
            INSERT INTO neo_observations (
                run_id,
                neo_id,
                name,
                max_diameter_km,
                min_diameter_km,
                miss_distance_km,
                miss_distance_lunar,
                relative_velocity_kph,
                absolute_magnitude_h,
                is_potentially_hazardous_asteroid,
                num_close_approaches,
                total_known_neos,
                size_to_distance_ratio,
                scaled_size_to_distance_ratio,
                approach_category,
                priority_watch,
                observatory_code,
                confidence_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows_to_insert,
        )

    return run_id, DB_PATH