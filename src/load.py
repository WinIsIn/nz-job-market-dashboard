"""
Persists a cleaned jobs DataFrame into SQLite using upsert semantics.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    id           TEXT PRIMARY KEY,
    title        TEXT,
    role_type    TEXT,
    company      TEXT,
    location     TEXT,
    salary_min   REAL,
    salary_max   REAL,
    description  TEXT,
    skills       TEXT,
    category     TEXT,
    created      TEXT,
    redirect_url TEXT,
    scraped_at   TEXT
);
"""


def load_jobs(df: pd.DataFrame, db_path: str = "data/jobs.db") -> int:
    """
    Upsert jobs into SQLite and return the number of rows written.

    Uses INSERT OR REPLACE so re-running the pipeline on the same data is idempotent.
    The database file and parent directory are created automatically if they don't exist.
    """
    if df.empty:
        return 0

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    df = df.copy()
    df["scraped_at"] = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(db_path) as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()

        # Use pandas to_sql with a temporary staging table, then upsert — this is
        # simpler than building parameterised INSERT OR REPLACE statements manually.
        df.to_sql("jobs_staging", conn, if_exists="replace", index=False)

        conn.execute("""
            INSERT OR REPLACE INTO jobs
            SELECT * FROM jobs_staging
        """)
        conn.execute("DROP TABLE IF EXISTS jobs_staging")
        conn.commit()

    return len(df)
