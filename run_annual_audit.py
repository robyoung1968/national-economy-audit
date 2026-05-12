import os, json, requests
from datetime import datetime

def fetch_fred_annual(series_id):
    api_key = os.environ.get('FRED_API_KEY')
    # Fetching from 2005 to ensure we have enough padding for any YoY calcs if needed
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json&sort_order=desc&observation_start=2005-01-01"
    try:
        res = requests.get(url).json()
        return {obs['date'][:4]: float(obs['value']) for obs in res.get('observations', []) if obs['value'] != '.'}
    except:
        return {}

# GDP is usually Billions of Dollars, Annual
gdp_data = fetch_fred_annual('GDP') 
# Trade Balance (Net Exports), Annual
trade_data = fetch_fred_annual('NETEXP')

annual_economy = []
# Use GDP years as the master list
for year in sorted(gdp_data.keys(), reverse=True):
    if int(year) < 2008: continue  # Keep it focused on the relevant timeframe
    
    annual_economy.append({
        "year": year,
        "gdp_nominal": gdp_data.get(year, 0),
        "trade_balance": trade_data.get(year, 0)
    })

with open('annual_data.json', 'w') as f:
    json.dump(annual_economy, f, indent=4)

print(f"Annual Update Complete: {len(annual_economy)} years processed.")
