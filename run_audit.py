import os, json, requests, datetime

def fetch_treasury_debt(limit=5000):
    # Daily data requires a much higher limit to reach back to 2008
    url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
    params = {
        'sort': '-record_date', 
        'page[size]': limit,
        'filter': 'record_date:gte:2008-01-01'
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        # We only need one debt point per month to align with FRED
        # This logic takes the last available debt entry for any given month
        raw_data = response.json()['data']
        monthly_debt = {}
        for d in raw_data:
            month_key = d['record_date'][:7] # YYYY-MM
            if month_key not in monthly_debt:
                monthly_debt[month_key] = float(d['tot_pub_debt_out_amt'])
        return monthly_debt
    except Exception as e:
        print(f"Treasury Error: {e}")
        return {}

def fetch_fred_series(series_id, limit=300):
    api_key = os.environ.get('FRED_API_KEY')
    # FRED is monthly, so a limit of 300 is plenty for 17 years
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json&sort_order=desc&limit={limit}&observation_start=2008-01-01"
    try:
        res = requests.get(url).json()
        return [{"value": float(obs['value']), "date": obs['date']} for obs in res['observations'] if obs['value'] != '.']
    except Exception as e:
        print(f"FRED Error: {e}")
        return []

# EXECUTION
debt_map = fetch_treasury_debt()
cpi_data = fetch_fred_series('CPIAUCSL')
u3_data = fetch_fred_series('UNRATE')
u6_data = fetch_fred_series('U6RATE')

economy_data = []
for cpi in cpi_data:
    month_key = cpi['date'][:7]
    
    # Match values based on the YYYY-MM key
    u3_val = next((d['value'] for d in u3_data if d['date'][:7] == month_key), 0)
    u6_val = next((d['value'] for d in u6_data if d['date'][:7] == month_key), 0)
    
    economy_data.append({
        "month_date": cpi['date'],
        "avg_monthly_debt": debt_map.get(month_key, 0),
        "u3_rate": u3_val,
        "u6_rate": u6_val,
        "cpi_index": cpi['value']
    })

with open('economic_data.json', 'w') as f:
    json.dump(economy_data, f, indent=4)
