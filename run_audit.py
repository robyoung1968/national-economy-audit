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

# --- REVISED HISTORICAL PROCESSING LOOP ---

# 1. Dynamically gather every unique YYYY-MM present across all datasets
all_months = set()
all_months.update(debt_map.keys())
all_months.update(obs['date'][:7] for obs in cpi_data)
all_months.update(obs['date'][:7] for obs in u3_data)
all_months.update(obs['date'][:7] for obs in u6_data)

# Sort chronologically so we can reliably carry forward baseline variables 
sorted_months = sorted(list(all_months))

# Initialize state trackers for carry-forward fallback logic
last_known_debt = 0.0
last_known_cpi = 0.0
last_known_u3 = 0.0
last_known_u6 = 0.0

economy_data = []

# Loop sequentially to build out the true telemetry timeline matrices
for month_key in sorted_months:
    # Match observations for the current loop month or retain last known value
    cpi_match = next((d for d in cpi_data if d['date'][:7] == month_key), None)
    u3_match = next((d for d in u3_data if d['date'][:7] == month_key), None)
    u6_match = next((d for d in u6_data if d['date'][:7] == month_key), None)
    
    # Update state trackers if data exists, otherwise fall back to previous month's rate
    if month_key in debt_map: last_known_debt = debt_map[month_key]
    if cpi_match:            last_known_cpi = cpi_match['value']
    if u3_match:             last_known_u3 = u3_match['value']
    if u6_match:             last_known_u6 = u6_match['value']
    
    # Generate the standard standardized string representation for the date field
    # If a FRED observation matches, use its precise YYYY-MM-DD date, else construct an audit baseline
    precise_date = cpi_match['date'] if cpi_match else (u3_match['date'] if u3_match else f"{month_key}-01")
    
    economy_data.append({
        "month_date": precise_date,
        "avg_monthly_debt": last_known_debt,
        "cpi_index": last_known_cpi,
        "u3_rate": last_known_u3,
        "u6_rate": last_known_u6
    })

# Invert array order to preserve the dashboard's descending chronology (Newest first)
economy_data.reverse()

# Write final optimized arrays out to storage layers
with open('economic_data.json', 'w') as f:
    json.dump(economy_data, f, indent=4)

print(f"Pipeline executed successfully. Matrix generated with {len(economy_data)} historical rows.")
print(f"Success: Telemetry matrix updated with {len(economy_data)} historical rows.")
