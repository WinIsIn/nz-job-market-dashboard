"""
Orchestrates the full ETL pipeline: fetch → transform → load.

Run with:  python -m src.pipeline
"""

import sys
from pathlib import Path

# Allow running as `python -m src.pipeline` from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetch import fetch_jobs
from src.transform import transform_jobs
from src.load import load_jobs

DB_PATH = "data/jobs.db"

# Broad query covering the main NZ tech role families
SEARCH_QUERY = "data analyst OR data engineer OR software engineer OR python OR SQL"
SEARCH_LOCATIONS = ["auckland", "wellington", "christchurch"]


def run_pipeline() -> None:
    print("=== NZ Tech Job Market Pipeline ===\n")

    all_raw: list[dict] = []

    for location in SEARCH_LOCATIONS:
        print(f"Fetching jobs in {location.title()}...")
        raw = fetch_jobs(query=SEARCH_QUERY, location=location, pages=3)
        all_raw.extend(raw)
        print(f"  Subtotal: {len(raw)} jobs\n")

    print(f"Total raw jobs fetched: {len(all_raw)}")

    df = transform_jobs(all_raw)
    print(f"After transformation: {len(df)} valid records")

    loaded = load_jobs(df, db_path=DB_PATH)
    print(f"Loaded {loaded} records into {DB_PATH}")
    print("\nPipeline complete.")


if __name__ == "__main__":
    run_pipeline()
