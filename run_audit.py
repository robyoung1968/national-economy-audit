import os, json, requests, datetime, math

def fetch_treasury_debt(limit=24):
    url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
    try:
        response = requests.get(url, params={'sort': '-record_date', 'page[size]': limit}, timeout=15)
        return [{"value": float(d['tot_pub_debt_out_amt']), "date": d['record_date']} for d in response.json()['data']]
    except: return []

def fetch_fred_series(series_id, limit=24):
    api_key = os.environ.get('FRED_API_KEY')
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json&sort_order=desc&limit={limit}"
    try:
        res = requests.get(url).json()
        return [{"value": float(obs['value']), "date": obs['date']} for obs in res['observations'] if obs['value'] != '.']
    except: return []

# EXECUTION
print("Rebuilding Classic Data Package...")
debt_data = fetch_treasury_debt()
u3_data = fetch_fred_series('UNRATE')
u6_data = fetch_fred_series('U6RATE')
cpi_data = fetch_fred_series('CPIAUCSL')

# ZIP DATA BY DATE (Matching the Reference index.htm's expected structure)
economy_data = []
for i in range(len(cpi_data)):
    try:
        # We use CPI dates as the anchor
        date_str = cpi_data[i]['date']
        economy_data.append({
            "month_date": date_str,
            "avg_monthly_debt": debt_data[i]['value'] if i < len(debt_data) else 0,
            "u3_rate": u3_data[i]['value'] / 100 if i < len(u3_data) else 0,
            "u6_rate": u6_data[i]['value'] / 100 if i < len(u6_data) else 0,
            "cpi_index": cpi_data[i]['value']
        })
    except: continue

with open('economic_data.json', 'w') as f:
    json.dump(economy_data, f, indent=4)
print(f"Success: {len(economy_data)} months packaged.")
