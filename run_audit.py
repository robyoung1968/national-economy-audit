import os
import json
import requests
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# --- CONFIGURATION ---
PROJECT_ID = "march-2026-projects"
DATASET_ID = "national_economy_staging"

# 1. AUTHENTICATION
service_account_info = json.loads(os.environ.get('GCP_SA_KEY'))
credentials = service_account.Credentials.from_service_account_info(service_account_info)
client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

# 2. HELPER FUNCTIONS
def fetch_treasury_debt(days=90):
    url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
    params = {'sort': '-record_date', 'page[size]': days}
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        df = pd.DataFrame(response.json()['data'])
        df['record_date'] = pd.to_datetime(df['record_date'])
        df['tot_pub_debt_out_amt'] = pd.to_numeric(df['tot_pub_debt_out_amt'])
        return df[['record_date', 'tot_pub_debt_out_amt']]
    except Exception as e:
        print(f"Error fetching Treasury: {e}")
        return pd.DataFrame()

def fetch_fred_data(series_id):
    api_key = os.environ.get('FRED_API_KEY')
    # Starts at 2008-01-01 to ensure a full year of 2008 data for 2009 YoY calculations
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json&observation_start=2008-01-01"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        df = pd.DataFrame(response.json()['observations'])
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        return df[['date', 'value']]
    except Exception as e:
        print(f"Error fetching {series_id}: {e}")
        return pd.DataFrame()

def upload_to_bq(df, table_name):
    if not df.empty:
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        client.load_table_from_dataframe(df, table_id, job_config=job_config).result()
        print(f"Successfully uploaded: {table_name}")

# --- EXECUTION ---

# A. Fetch Data
print("Fetching daily/monthly data...")
debt_df = fetch_treasury_debt(90)
cpi_df = fetch_fred_data('CPIAUCSL')
u3_df = fetch_fred_data('UNRATE')
u6_df = fetch_fred_data('U6RATE')

print("Fetching annual Phase 2 data...")
# We rename 'value' immediately so we can merge these later
gdp_df = fetch_fred_data('GDPCA').rename(columns={'value': 'real_gdp', 'date': 'record_date'})
net_exports_df = fetch_fred_data('NETEXP').rename(columns={'value': 'net_exports', 'date': 'record_date'})
goods_df = fetch_fred_data('IEAXGS').rename(columns={'value': 'goods_balance', 'date': 'record_date'})
services_df = fetch_fred_data('IEAXS').rename(columns={'value': 'services_balance', 'date': 'record_date'})

# B. Upload Individual Monthly/Daily Tables
upload_to_bq(debt_df, "treasury_debt_historical")
upload_to_bq(cpi_df, "fred_cpi_historical")
upload_to_bq(u3_df, "fred_unemployment_u3_historical")
upload_to_bq(u6_df, "fred_unemployment_u6_historical")

# C. Merge Annual Indicators into a Single Table
if not gdp_df.empty:
    print("Merging annual indicators...")
    annual_df = pd.merge(gdp_df, net_exports_df, on='record_date', how='outer')
    annual_df = pd.merge(annual_df, goods_df, on='record_date', how='outer')
    annual_df = pd.merge(annual_df, services_df, on='record_date', how='outer')
    
    # Add regime for dashboard consistency
    annual_df['regime'] = 'Historical'
    
    upload_to_bq(annual_df, "annual_economy_indicators")

# Add this at the end of your run_audit.py
# Assuming 'final_df' is your combined indicators dataframe
annual_df.to_json('economic_data.json', orient='records', date_format='iso')
print("Local JSON file created for GitHub Dashboard.")

import datetime

# Create a small dictionary or add to your dataframe
# This ensures the JSON file is technically "different" every day
export_data = {
    "last_updated": datetime.datetime.now().isoformat(),
    "data": annual_df.to_dict(orient='records')
}

import json
import datetime
from decimal import Decimal

# Helper to handle dates and decimals in JSON
def json_serial(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

# Create the export package
export_data = {
    "last_updated": datetime.datetime.now().isoformat(),
    "data": annual_df.to_dict(orient='records')
}

# Write the file using our helper
with open('economic_data.json', 'w') as f:
    json.dump(export_data, f, default=json_serial)

print("Local JSON file created successfully with serialized dates.")

print("Local JSON file created with timestamp.")

print("All tasks complete. Data Refresh Success.")

