import os
import json
import logging
import requests
from datetime import datetime

# Configure logging for GitHub Actions / CI environment
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

FRED_API_KEY = os.environ.get("FRED_API_KEY")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
OUTPUT_JSON = "economic_data.json"
START_DATE = "2008-01-01"

# Existing FRED & BLS series mappings retained
EXISTING_SERIES = {
    "cpi_index": "CPIAUCSL",
    "u3_rate": "UNRATE",
    "u6_rate": "U6RATE",
    "lfpr_rate": "CIVPART",
    "not_in_labor_force": "LNS15000000",
    "long_term_unemp_count": "UEMP27OV",
    "long_term_unemp_pct": "LNS13025703",
    "job_openings_rate": "JTSJOR",
    "quits_rate": "JTSQUR",
    "initial_claims_monthly_avg": "ICSA",
    "continued_claims_monthly_avg": "CCSA"
}

# New employment series to append
NEW_EMPLOYMENT_SERIES = {
    "PAYEMS": "PAYEMS",     # Total Nonfarm
    "USPRIV": "USPRIV",     # Total Private
    "USGOOD": "USGOOD",     # Goods-Producing
    "SRVPRD": "SRVPRD",     # Service-Providing
    "USSERV": "USSERV",     # Private Services
    "USGOVT": "USGOVT"      # Government (Fallback calculated if API fails/missing)
}

# Combine all series endpoints
ALL_SERIES_TO_FETCH = {**EXISTING_SERIES, **NEW_EMPLOYMENT_SERIES}


def fetch_fred_series(series_id: str, start_date: str = "2008-01-01") -> dict:
    """Fetches observation data from FRED API for a given series ID."""
    if not FRED_API_KEY:
        logging.warning(f"FRED_API_KEY not set. Skipping fetch for {series_id}.")
        return {}

    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
        "frequency": "m"  # Monthly
    }

    try:
        response = requests.get(FRED_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        series_data = {}
        for obs in data.get("observations", []):
            date_str = obs["date"]
            val_str = obs["value"]
            if val_str != ".":  # Filter out missing FRED observation markers
                series_data[date_str] = float(val_str)
        
        logging.info(f"Fetched {len(series_data)} records for series '{series_id}'")
        return series_data

    except Exception as e:
        logging.error(f"Error fetching series '{series_id}': {e}")
        return {}


def load_existing_dataset(filepath: str) -> dict:
    """Loads existing JSON file, maintaining dictionary mapping by month_date."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
                if isinstance(raw, list):
                    return {row["month_date"]: row for row in raw if "month_date" in row}
                elif isinstance(raw, dict):
                    return raw
        except Exception as e:
            logging.warning(f"Could not parse existing {filepath}: {e}. Initializing clean map.")
    return {}


def update_economic_data():
    """Main execution function to fetch all series and update economic_data.json."""
    logging.info("Starting run_audit.py execution...")
    
    # Preserve existing data entries (including avg_monthly_debt, Treasury data, etc.)
    dataset_by_date = load_existing_dataset(OUTPUT_JSON)
    
    # 1. Fetch data for all defined FRED series
    fetched_results = {}
    for field_name, series_id in ALL_SERIES_TO_FETCH.items():
        fetched_results[field_name] = fetch_fred_series(series_id, START_DATE)

    # 2. Gather all unique dates across incoming data and existing data
    all_dates = set(dataset_by_date.keys())
    for series_dict in fetched_results.values():
        all_dates.update(series_dict.keys())

    # 3. Merge incoming metrics without overwriting existing non-FRED fields
    for date_key in sorted(all_dates):
        if date_key not in dataset_by_date:
            dataset_by_date[date_key] = {"month_date": date_key}
        
        # Ingest/update FRED values
        for field_name in ALL_SERIES_TO_FETCH.keys():
            if date_key in fetched_results[field_name]:
                dataset_by_date[date_key][field_name] = fetched_results[field_name][date_key]

        # Explicit fallback calculation for USGOVT (PAYEMS - USPRIV)
        payems = dataset_by_date[date_key].get("PAYEMS")
        uspriv = dataset_by_date[date_key].get("USPRIV")
        
        if dataset_by_date[date_key].get("USGOVT") is None and payems is not None and uspriv is not None:
            dataset_by_date[date_key]["USGOVT"] = round(payems - uspriv, 3)

    # 4. Save sorted output list back to economic_data.json
    final_output = [dataset_by_date[d] for d in sorted(dataset_by_date.keys())]
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)
    
    logging.info(f"Audit update complete. Output written to {OUTPUT_JSON} ({len(final_output)} total rows).")


if __name__ == "__main__":
    update_economic_data()
