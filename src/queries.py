"""
SQL query helpers that return pandas DataFrames for use in the dashboard.

Each function accepts an optional db_path so tests can point at a fixture database.
"""

import importlib.util
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

DEFAULT_DB = "data/jobs.db"


def ensure_db(db_path: str = DEFAULT_DB) -> None:
    """
    Seed the database with demo data if it doesn't exist.

    Streamlit Cloud starts with a clean filesystem on every deploy, so the
    SQLite file produced locally is never present. Loading the seed script via
    importlib (rather than a package import) avoids needing __init__.py in
    scripts/ and keeps the seeding logic in one canonical place.
    """
    if Path(db_path).exists():
        return

    project_root = Path(__file__).parent.parent
    seed_path = project_root / "scripts" / "seed_demo_data.py"

    # Make sure src/ is on sys.path so the seed script's own imports resolve
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    spec = importlib.util.spec_from_file_location("seed_demo_data", seed_path)
    seeder = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(seeder)  # type: ignore[union-attr]
    seeder.main()


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_jobs_by_role_type(db_path: str = DEFAULT_DB) -> pd.DataFrame:
    """Return job count grouped by normalised role type."""
    with _connect(db_path) as conn:
        return pd.read_sql_query(
            "SELECT role_type, COUNT(*) AS job_count FROM jobs GROUP BY role_type ORDER BY job_count DESC",
            conn,
        )


def get_top_skills(n: int = 15, db_path: str = DEFAULT_DB) -> pd.DataFrame:
    """
    Return the n most frequently mentioned skills across all job descriptions.

    Skills are stored as comma-separated strings, so we explode them in Python
    rather than trying to parse CSV inside SQLite.
    """
    with _connect(db_path) as conn:
        df = pd.read_sql_query("SELECT skills FROM jobs WHERE skills != ''", conn)

    if df.empty:
        return pd.DataFrame(columns=["skill", "count"])

    all_skills: list[str] = []
    for skills_str in df["skills"]:
        all_skills.extend(s.strip() for s in skills_str.split(",") if s.strip())

    counts = Counter(all_skills).most_common(n)
    return pd.DataFrame(counts, columns=["skill", "count"])


def get_jobs_by_city(db_path: str = DEFAULT_DB) -> pd.DataFrame:
    """Return job count grouped by city."""
    with _connect(db_path) as conn:
        return pd.read_sql_query(
            "SELECT location AS city, COUNT(*) AS job_count FROM jobs GROUP BY location ORDER BY job_count DESC",
            conn,
        )


def get_salary_by_role(db_path: str = DEFAULT_DB) -> pd.DataFrame:
    """
    Return average salary_min and salary_max per role type.

    Excludes rows where both salary fields are NULL so the chart only shows
    roles with meaningful salary data.
    """
    with _connect(db_path) as conn:
        return pd.read_sql_query(
            """
            SELECT
                role_type,
                ROUND(AVG(salary_min), 0) AS avg_salary_min,
                ROUND(AVG(salary_max), 0) AS avg_salary_max
            FROM jobs
            WHERE salary_min IS NOT NULL OR salary_max IS NOT NULL
            GROUP BY role_type
            ORDER BY avg_salary_min DESC
            """,
            conn,
        )


def get_hiring_companies(n: int = 10, db_path: str = DEFAULT_DB) -> pd.DataFrame:
    """Return the top n companies ordered by number of active listings."""
    with _connect(db_path) as conn:
        return pd.read_sql_query(
            f"""
            SELECT company, COUNT(*) AS job_count
            FROM jobs
            WHERE company != 'Unknown'
            GROUP BY company
            ORDER BY job_count DESC
            LIMIT {n}
            """,
            conn,
        )


def get_jobs_over_time(db_path: str = DEFAULT_DB) -> pd.DataFrame:
    """
    Return weekly job posting counts for the last 8 weeks.

    SQLite's strftime is used to bucket by ISO week so the x-axis is human-readable.
    """
    with _connect(db_path) as conn:
        return pd.read_sql_query(
            """
            SELECT
                strftime('%Y-W%W', created) AS week,
                COUNT(*) AS job_count
            FROM jobs
            WHERE created IS NOT NULL AND created != 'None'
            GROUP BY week
            ORDER BY week DESC
            LIMIT 8
            """,
            conn,
        )


def get_last_updated(db_path: str = DEFAULT_DB) -> str:
    """Return the most recent scraped_at timestamp as a formatted date string."""
    try:
        with _connect(db_path) as conn:
            row = conn.execute("SELECT MAX(scraped_at) FROM jobs").fetchone()
            if row and row[0]:
                return row[0][:10]
    except Exception:
        pass
    return "Unknown"


def get_summary_stats(db_path: str = DEFAULT_DB) -> dict:
    """Return scalar KPIs used by the metric cards in the dashboard header."""
    with _connect(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]

        avg_salary_row = conn.execute(
            "SELECT AVG((COALESCE(salary_min,0) + COALESCE(salary_max,0)) / 2.0) "
            "FROM jobs WHERE salary_min IS NOT NULL OR salary_max IS NOT NULL"
        ).fetchone()
        avg_salary = round(avg_salary_row[0]) if avg_salary_row and avg_salary_row[0] else None

        top_city_row = conn.execute(
            "SELECT location FROM jobs GROUP BY location ORDER BY COUNT(*) DESC LIMIT 1"
        ).fetchone()
        top_city = top_city_row[0] if top_city_row else "N/A"

    # Most in-demand skill comes from the Python-side skill counter
    skills_df = get_top_skills(n=1, db_path=db_path)
    top_skill = skills_df.iloc[0]["skill"] if not skills_df.empty else "N/A"

    return {
        "total_jobs": total,
        "avg_salary": avg_salary,
        "top_city": top_city,
        "top_skill": top_skill,
    }
