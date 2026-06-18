"""
Fetches job listings from the Adzuna Jobs API for NZ tech roles.
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/nz/search"


def fetch_jobs(query: str, location: str, pages: int = 3) -> list[dict]:
    """
    Fetch raw job listings from the Adzuna API across multiple pages.

    Sleeps 1 s between pages to stay within the free-tier rate limit.
    Returns an empty list instead of raising on API errors so the pipeline
    can degrade gracefully when credentials are missing or the network is down.
    """
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    if not app_id or not app_key:
        print("WARNING: ADZUNA_APP_ID / ADZUNA_APP_KEY not set. Skipping API fetch.")
        return []

    all_jobs: list[dict] = []

    for page in range(1, pages + 1):
        url = f"{ADZUNA_BASE_URL}/{page}"
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": 50,
            "what": query,
            "where": location,
            "content-type": "application/json",
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            all_jobs.extend(results)
            print(f"  Page {page}: fetched {len(results)} jobs")

            if len(results) < 50:
                # Fewer results than requested means we've hit the last page
                break

        except requests.exceptions.HTTPError as e:
            print(f"  HTTP error on page {page}: {e}")
            break
        except requests.exceptions.RequestException as e:
            print(f"  Network error on page {page}: {e}")
            break
        except ValueError:
            print(f"  Invalid JSON on page {page}")
            break

        time.sleep(1)  # Adzuna free tier allows ~1 req/s

    return all_jobs
