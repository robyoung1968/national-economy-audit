import os, json, requests, datetime, math
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# --- CONFIGURATION ---
PROJECT_ID = "march-2026-projects"
DATASET_ID = "national_economy_staging"

# AUTHENTICATION
service_account_info = json.loads(os.environ.get('GCP_SA_KEY'))
credentials = service_account.Credentials.from_service_account_info(service_account_info)
client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

def fetch_treasury_debt():
    url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
    try:
        response = requests.get(url, params={'sort': '-record_date', 'page[size]': 1}, timeout=15)
        data = response.json()['data'][0]
        return {"value": float(data['tot_pub_debt_out_amt']), "date": data['record_date']}
    except: return {"value": 0, "date": "N/A"}

def fetch_fred_latest(series_id):
    api_key = os.environ.get('FRED_API_KEY')
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json&sort_order=desc&limit=1"
    try:
        obs = requests.get(url).json()['observations'][0]
        # Handle cases where FRED returns '.' for a value
        val = obs['value']
        return {"value": float(val) if val != '.' else 0, "date": obs['date']}
    except: return {"value": 0, "date": "N/A"}

# EXECUTION
print("Refreshing Monthly Audit Data...")
debt = fetch_treasury_debt()
u3 = fetch_fred_latest('UNRATE')
u6 = fetch_fred_latest('U6RATE')
cpi = fetch_fred_latest('CPIAUCSL')

# FORMATTING PAYLOAD
payload = {
    "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    "metrics": [
        {"label": "Total National Debt", "value": debt['value'], "sub": f"As of {debt['date']}", "type": "currency"},
        {"label": "Unemployment (U3)", "value": u3['value'], "sub": f"Released {u3['date']}", "type": "percent"},
        {"label": "Real Unemployment (U6)", "value": u6['value'], "sub": f"Released {u6['date']}", "type": "percent"},
        {"label": "Consumer Price Index", "value": cpi['value'], "sub": f"Ref: {cpi['date']}", "type": "number"}
    ]
}

# EXPORT
with open('economic_data.json', 'w') as f:
    json.dump(payload, f, indent=4)
print("Success: Monthly JSON generated.")
