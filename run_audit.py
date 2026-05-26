import os, json, requests

def fetch_treasury_debt(limit=5000):
    url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
    params = {'sort': '-record_date', 'page[size]': limit, 'filter': 'record_date:gte:2008-01-01'}
    try:
        response = requests.get(url, params=params, timeout=15)
        raw_data = response.json().get('data', [])
        monthly_debt = {}
        for d in raw_data:
            month_key = d['record_date'][:7]
            if month_key not in monthly_debt:
                monthly_debt[month_key] = float(d['tot_pub_debt_out_amt'])
        return monthly_debt
    except: 
        return {}

def fetch_fred_series(series_id, limit=300):
    api_key = os.environ.get('FRED_API_KEY')
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json&sort_order=desc&limit={limit}&observation_start=2008-01-01"
    try:
        res = requests.get(url, timeout=15).json()
        return [{"value": float(obs['value']), "date": obs['date']} for obs in res.get('observations', []) if obs['value'] != '.']
    except: 
        return []

# Fetch datasets
debt_map = fetch_treasury_debt()
cpi_data = fetch_fred_series('CPIAUCSL')
u3_data = fetch_fred_series('UNRATE')
u6_data = fetch_fred_series('U6RATE')

# CRITICAL SECURITY GUARD: Do not overwrite the database if an API fetch failed blank
if not debt_map or not cpi_data or not u3_data or not u6_data:
    print("CRITICAL: One or more upstream macro APIs returned an empty response.")
    print(f"Status - Debt: {bool(debt_map)}, CPI: {len(cpi_data)}, U3: {len(u3_data)}, U6: {len(u6_data)}")
    print("Aborting run to protect historical database integrity.")
    exit(1) # Force GitHub Actions to fail loudly so you get an email notification

economy_data = []
for cpi in cpi_data:
    month_key = cpi['date'][:7]
    u3_val = next((d['value'] for d in u3_data if d['date'][:7] == month_key), 0.0)
    u6_val = next((d['value'] for d in u6_data if d['date'][:7] == month_key), 0.0)
    
    economy_data.append({
        "month_date": cpi['date'],
        "avg_monthly_debt": debt_map.get(month_key, 0.0),
        "u3_rate": float(u3_val),
        "u6_rate": float(u6_val),
        "cpi_index": float(cpi['value']) # Fixed: Explicitly casting to float
    })

# Write out the clean, validated array
with open('economic_data.json', 'w') as f:
    json.dump(economy_data, f, indent=4)

print(f"Success: Telemetry matrix updated with {len(economy_data)} historical rows.")
