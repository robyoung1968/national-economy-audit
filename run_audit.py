import os, json, requests, datetime

def fetch_treasury_debt(limit=250):
    url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
    params = {
        'sort': '-record_date', 
        'page[size]': limit,
        'filter': 'record_date:gte:2008-01-01'
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        return [{"value": float(d['tot_pub_debt_out_amt']), "date": d['record_date']} for d in response.json()['data']]
    except: return []

def fetch_fred_series(series_id, limit=250):
    api_key = os.environ.get('FRED_API_KEY')
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json&sort_order=desc&limit={limit}&observation_start=2008-01-01"
    try:
        res = requests.get(url).json()
        return [{"value": float(obs['value']), "date": obs['date']} for obs in res['observations'] if obs['value'] != '.']
    except: return []

# EXECUTION
debt_data = fetch_treasury_debt()
u3_data = fetch_fred_series('UNRATE')
u6_data = fetch_fred_series('U6RATE')
cpi_data = fetch_fred_series('CPIAUCSL')

economy_data = []
for i in range(len(cpi_data)):
    date_str = cpi_data[i]['date']
    debt_val = next((d['value'] for d in debt_data if d['date'][:7] == date_str[:7]), 0)
    u3_val = next((d['value'] for d in u3_data if d['date'][:7] == date_str[:7]), 0)
    u6_val = next((d['value'] for d in u6_data if d['date'][:7] == date_str[:7]), 0)
    
    economy_data.append({
        "month_date": date_str,
        "avg_monthly_debt": debt_val,
        "u3_rate": u3_val,
        "u6_rate": u6_val,
        "cpi_index": cpi_data[i]['value']
    })

with open('economic_data.json', 'w') as f:
    json.dump(economy_data, f, indent=4)
