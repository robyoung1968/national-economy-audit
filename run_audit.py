import os, json, requests, datetime, math

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
        res = requests.get(url).json()
        obs = res['observations'][0]
        return {"value": float(obs['value']), "date": obs['date']}
    except: return {"value": 0, "date": "N/A"}

# EXECUTION
debt = fetch_treasury_debt()
u3 = fetch_fred_latest('UNRATE')
u6 = fetch_fred_latest('U6RATE')
cpi = fetch_fred_latest('CPIAUCSL')

# PACKAGING: Reverting to the "List of Records" format used in your original index.htm
# We create a list with one record (the latest) to satisfy the original HTML's logic
payload = [{
    "month_date": debt['date'],
    "avg_monthly_debt": debt['value'],
    "u3_rate": u3['value'] / 100, # Original HTML expected decimal (0.04) for percentFormat
    "u6_rate": u6['value'] / 100,
    "cpi_index": cpi['value']
}]

with open('economic_data.json', 'w') as f:
    json.dump(payload, f, indent=4)
