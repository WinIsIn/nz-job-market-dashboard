# NZ Tech Job Market Dashboard

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-FF4B4B?logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.22-3F4F75?logo=plotly&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-2.2-150458?logo=pandas&logoColor=white)

A data pipeline and analytics dashboard that tracks NZ tech job listings across Auckland, Wellington, and Christchurch. Raw job data is fetched from the Adzuna Jobs API, stored in a local SQLite database, and visualised in an interactive Streamlit dashboard with role breakdowns, salary analysis, skill frequency, and hiring trends.

---

## Screenshots

> Add screenshot here

---

## Tech Stack

| Layer | Tool |
|---|---|
| Data source | Adzuna Jobs API |
| HTTP client | `requests` |
| Data processing | `pandas` |
| Storage | SQLite (`sqlite3`) |
| Dashboard | `Streamlit` + `Plotly Express` |
| Config | `python-dotenv` |

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/your-username/nz-job-market-dashboard.git
cd nz-job-market-dashboard
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Add API credentials (optional — skip to use demo data)

```bash
cp .env.example .env
# Edit .env and add your Adzuna app_id and app_key
# Register free at https://developer.adzuna.com/
```

### 3a. Seed demo data (no API key needed)

```bash
python scripts/seed_demo_data.py
```

### 3b. Or run the live pipeline (requires .env)

```bash
python -m src.pipeline
```

### 4. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

Open http://localhost:8501 in your browser.

---

## Project Structure

```
nz-job-market-dashboard/
├── .env.example          # API credential template
├── .gitignore
├── requirements.txt
├── data/
│   └── jobs.db           # SQLite database (auto-created)
├── src/
│   ├── fetch.py          # Adzuna API client
│   ├── transform.py      # pandas cleaning & enrichment
│   ├── load.py           # SQLite upsert logic
│   ├── pipeline.py       # ETL orchestrator
│   └── queries.py        # SQL query functions
├── dashboard/
│   └── app.py            # Streamlit dashboard
└── scripts/
    └── seed_demo_data.py # 200 realistic fake NZ jobs
```

---

## Key Insights

> Add key insights after running with live data

- Most in-demand skills: …
- Salary ranges by role: …
- City breakdown: …

---

## Data Source

Job listings sourced from the [Adzuna Jobs API](https://developer.adzuna.com/) — free tier, no scraping.

---

## Live Demo

> Add link here
