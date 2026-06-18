"""
Generates 200 realistic fake NZ tech jobs and loads them into the database.

Run this to populate the dashboard without needing an Adzuna API key.
"""

import sys
import random
from pathlib import Path
from datetime import date, timedelta

# Allow running from any working directory
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.load import load_jobs

# ── Configuration ─────────────────────────────────────────────────────────────

SEED = 42
NUM_JOBS = 200
DB_PATH = "data/jobs.db"

random.seed(SEED)

NZ_COMPANIES = [
    "Xero", "Fisher & Paykel", "ANZ Bank", "Spark NZ", "Vodafone NZ",
    "Datacom", "Orion Health", "Vista Group", "PwC New Zealand",
    "Deloitte New Zealand", "KPMG New Zealand", "Air New Zealand",
    "Trade Me", "Pushpay", "Serko", "Soul Machines", "Westpac NZ",
    "ASB Bank", "BNZ", "Ministry of Education", "Stats NZ", "Kiwibank",
    "Genesis Energy", "Meridian Energy", "Fonterra",
]

ROLE_CONFIGS = {
    "Data Analyst": {
        "titles": [
            "Data Analyst", "Senior Data Analyst", "Business Intelligence Analyst",
            "Analytics Analyst", "Junior Data Analyst", "BI Analyst",
        ],
        "skills": ["Python", "SQL", "Tableau", "Power BI", "Excel", "R", "pandas"],
        "salary_range": (65_000, 110_000),
        "weight": 30,
    },
    "Data Engineer": {
        "titles": [
            "Data Engineer", "Senior Data Engineer", "Analytics Engineer",
            "ETL Developer", "Data Platform Engineer", "Staff Data Engineer",
        ],
        "skills": ["Python", "SQL", "dbt", "Spark", "AWS", "Azure", "Git", "pandas"],
        "salary_range": (80_000, 130_000),
        "weight": 20,
    },
    "Software Engineer": {
        "titles": [
            "Software Engineer", "Senior Software Engineer", "Backend Developer",
            "Full Stack Developer", "Python Developer", "DevOps Engineer",
            "Frontend Developer", "Lead Software Engineer",
        ],
        "skills": ["Python", "JavaScript", "TypeScript", "Node.js", "Git", "AWS", "Azure", "SQL"],
        "salary_range": (75_000, 130_000),
        "weight": 30,
    },
    "Business Analyst": {
        "titles": [
            "Business Analyst", "Senior Business Analyst", "Systems Analyst",
            "Product Analyst", "IT Business Analyst",
        ],
        "skills": ["SQL", "Excel", "Power BI", "Tableau", "Python"],
        "salary_range": (70_000, 105_000),
        "weight": 12,
    },
    "Other": {
        "titles": [
            "Data Scientist", "ML Engineer", "QA Engineer", "Product Manager",
            "Scrum Master", "IT Support Analyst",
        ],
        "skills": ["Python", "SQL", "Git", "AWS"],
        "salary_range": (65_000, 115_000),
        "weight": 8,
    },
}

# Auckland gets ~60% of jobs; Wellington ~25%; Christchurch ~15%
CITY_WEIGHTS = {"Auckland": 60, "Wellington": 25, "Christchurch": 15}

DESCRIPTION_TEMPLATES = [
    "We are looking for a {title} to join our team in {city}. "
    "You will work with {skills_prose} to deliver high-quality data solutions. "
    "Experience with {skills_prose2} is a bonus. Join a collaborative team at {company}.",

    "{company} is seeking a passionate {title} to help us build the future of data. "
    "Must-have skills: {skills_prose}. Nice to have: {skills_prose2}. "
    "Based in {city} with flexible working options.",

    "Exciting opportunity for a {title} at {company}. "
    "You'll use {skills_prose} daily in a fast-paced environment. "
    "Experience with {skills_prose2} preferred. {city}-based role.",
]


def _random_date_in_last_8_weeks() -> str:
    """Return a random date within the last 8 weeks, weighted toward more recent dates."""
    days_ago = int(random.triangular(0, 56, 7))  # triangular skews toward recent
    return (date.today() - timedelta(days=days_ago)).isoformat()


def _build_description(title: str, company: str, city: str, skills: list[str]) -> str:
    template = random.choice(DESCRIPTION_TEMPLATES)
    skill_sample = random.sample(skills, min(len(skills), 4))
    return template.format(
        title=title,
        company=company,
        city=city,
        skills_prose=", ".join(skill_sample[:2]),
        skills_prose2=", ".join(skill_sample[2:]) or skill_sample[0],
    )


def generate_jobs() -> list[dict]:
    roles = list(ROLE_CONFIGS.keys())
    role_weights = [ROLE_CONFIGS[r]["weight"] for r in roles]
    cities = list(CITY_WEIGHTS.keys())
    city_weights = list(CITY_WEIGHTS.values())

    jobs: list[dict] = []

    for i in range(NUM_JOBS):
        role = random.choices(roles, weights=role_weights)[0]
        cfg = ROLE_CONFIGS[role]

        title = random.choice(cfg["titles"])
        company = random.choice(NZ_COMPANIES)
        city = random.choices(cities, weights=city_weights)[0]
        skills = random.sample(cfg["skills"], min(len(cfg["skills"]), random.randint(3, 6)))
        salary_min = random.randint(*[s // 1000 for s in cfg["salary_range"]]) * 1000
        # salary_max is 10–25% above salary_min; ~20% of jobs have no salary listed
        has_salary = random.random() > 0.20
        description = _build_description(title, company, city, skills)

        job = {
            "id": f"demo_{i:04d}",
            "title": title,
            "role_type": role,
            "company": company,
            "location": city,
            "salary_min": salary_min if has_salary else None,
            "salary_max": int(salary_min * random.uniform(1.10, 1.25)) if has_salary else None,
            "description": description,
            "skills": ",".join(skills),
            "category": "IT Jobs",
            "created": _random_date_in_last_8_weeks(),
            "redirect_url": f"https://www.adzuna.co.nz/jobs/details/demo_{i:04d}",
        }
        jobs.append(job)

    return jobs


def main() -> None:
    print(f"Generating {NUM_JOBS} demo NZ tech jobs...")
    jobs = generate_jobs()
    df = pd.DataFrame(jobs)
    loaded = load_jobs(df, db_path=DB_PATH)
    print(f"Seeded {loaded} records into {DB_PATH}")

    # Quick sanity check
    role_counts = df["role_type"].value_counts().to_dict()
    city_counts = df["location"].value_counts().to_dict()
    print(f"\nRole distribution: {role_counts}")
    print(f"City distribution: {city_counts}")


if __name__ == "__main__":
    main()
