# --- replaces the Colab-specific userdata with standard environment variables that GitHub Actions can read.
import os
import json
import requests
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# --- CONFIGURATION ---
PROJECT_ID = "march-2026-projects"
DATASET_ID = "national_economy_data"

# 1. AUTHENTICATION
# GitHub will provide the GCP_SA_KEY as an environment variable
service_account_info = json.loads(os.environ.get('GCP_SA_KEY'))
credentials = service_account.Credentials.from_service_account_info(service_account_info)
client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

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
    # Observation start set to 2008-01-01 for CPI buffer logic
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

# --- EXECUTION ---
# 1. Fetch
debt_df = fetch_treasury_debt(90)
cpi_df = fetch_fred_data('CPIAUCSL')
u3_df = fetch_fred_data('UNRATE')
u6_df = fetch_fred_data('U6RATE')

# 2. Upload
def upload_to_bq(df, table_name):
    if not df.empty:
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        client.load_table_from_dataframe(df, table_id, job_config=job_config).result()
        print(f"Uploaded {table_name}")

upload_to_bq(debt_df, "treasury_debt_raw")
upload_to_bq(cpi_df, "fred_cpi_raw")
upload_to_bq(u3_df, "fred_u3_raw")
upload_to_bq(u6_df, "fred_u6_raw")

print("Data Refresh Complete.")