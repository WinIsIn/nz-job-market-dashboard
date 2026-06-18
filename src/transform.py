"""
Cleans and enriches raw Adzuna job dicts into a structured DataFrame.
"""

import re
from datetime import datetime
import pandas as pd


# --- Title normalisation ---------------------------------------------------

ROLE_KEYWORDS: dict[str, list[str]] = {
    "Data Analyst": ["data analyst", "analytics analyst", "business intelligence analyst", "bi analyst"],
    "Data Engineer": ["data engineer", "etl developer", "data pipeline", "analytics engineer"],
    "Software Engineer": ["software engineer", "software developer", "backend developer",
                          "frontend developer", "full stack", "fullstack", "web developer",
                          "python developer", "devops"],
    "Business Analyst": ["business analyst", "systems analyst", "product analyst", "ba "],
}

SKILL_KEYWORDS: list[str] = [
    "Python", "SQL", "R", "Excel", "Tableau", "Power BI", "pandas",
    "dbt", "Spark", "AWS", "Azure", "Git", "JavaScript", "TypeScript", "Node.js",
]


def _normalise_title(title: str) -> str:
    """Map a raw job title to one of our five standard role buckets."""
    lower = title.lower()
    for role, keywords in ROLE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return role
    return "Other"


def _extract_skills(description: str) -> str:
    """Return a comma-separated string of skills found in the job description."""
    if not description:
        return ""
    found = [skill for skill in SKILL_KEYWORDS if re.search(rf"\b{re.escape(skill)}\b", description, re.IGNORECASE)]
    return ",".join(found)


def _annual_salary(value: float | None, contract_type: str) -> float | None:
    """
    Convert hourly rates to annual equivalents assuming 2080 working hours/year.
    Adzuna sometimes reports hourly salaries — the contract_type field signals this.
    """
    if value is None:
        return None
    if contract_type and "hour" in contract_type.lower():
        return round(value * 2080, 2)
    return value


def _parse_location(location_dict: dict) -> str:
    """Pull a clean city name out of Adzuna's nested location object."""
    areas = location_dict.get("area", [])
    # Adzuna returns areas from broadest → narrowest; the last entry is the city
    if areas:
        city = areas[-1].strip()
        # Normalise to the three main NZ cities we care about
        for known in ("Auckland", "Wellington", "Christchurch"):
            if known.lower() in city.lower():
                return known
        return city
    return location_dict.get("display_name", "Unknown")


# --------------------------------------------------------------------------

def transform_jobs(raw_jobs: list[dict]) -> pd.DataFrame:
    """
    Transform a list of raw Adzuna job dicts into a clean, analysis-ready DataFrame.

    Handles missing salary / location gracefully so a single bad record doesn't
    drop the whole batch.
    """
    if not raw_jobs:
        return pd.DataFrame()

    records: list[dict] = []

    for job in raw_jobs:
        contract_type = job.get("contract_type") or ""
        salary_min_raw = job.get("salary_min")
        salary_max_raw = job.get("salary_max")

        record = {
            "id": job.get("id", ""),
            "title": job.get("title", ""),
            "role_type": _normalise_title(job.get("title", "")),
            "company": job.get("company", {}).get("display_name", "Unknown"),
            "location": _parse_location(job.get("location", {})),
            "salary_min": _annual_salary(salary_min_raw, contract_type),
            "salary_max": _annual_salary(salary_max_raw, contract_type),
            "description": job.get("description", ""),
            "skills": _extract_skills(job.get("description", "")),
            "category": job.get("category", {}).get("label", ""),
            "created": job.get("created", "")[:10] if job.get("created") else None,
            "redirect_url": job.get("redirect_url", ""),
        }
        records.append(record)

    df = pd.DataFrame(records)

    # Drop rows with no ID — they can't be upserted safely
    df = df[df["id"] != ""].copy()

    # Ensure salary columns are numeric (Adzuna occasionally returns strings)
    df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce")
    df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce")

    # Parse created date
    df["created"] = pd.to_datetime(df["created"], errors="coerce").dt.date.astype(str)

    return df
