import os, json, requests
import datetime

def fetch_fred_data(series_id):
    api_key = os.environ.get('FRED_API_KEY')
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json&sort_order=desc&observation_start=2008-01-01"
    try:
        res = requests.get(url).json()
        return res.get('observations', [])
    except Exception as e:
        print(f"Error fetching {series_id}: {e}")
        return []

def aggregate_yearly(observations, mode='average'):
    yearly_map = {}
    for obs in observations:
        if obs['value'] == '.' or obs['value'] == "": continue
        year = obs['date'][:4]
        if year not in yearly_map: yearly_map[year] = []
        yearly_map[year].append(float(obs['value']))
    
    final_data = {}
    for year, values in yearly_map.items():
        if not values: continue
        if mode == 'sum':
            final_data[year] = sum(values)
        else:
            final_data[year] = sum(values) / len(values)
    return final_data

# --- FETCH DATA SERIES ---
gdp_nominal_obs = fetch_fred_data('GDP')     # For Nominal GDP scale volume
gdp_real_obs = fetch_fred_data('GDPC1')       # For Headline Real GDP growth rates
total_trade_obs = fetch_fred_data('NETEXP')

# Component Trade (Monthly Balance of Payments)
goods_obs = fetch_fred_data('BOPGTB')
services_obs = fetch_fred_data('BOPSTB')

# --- AGGREGATE DATA BY YEAR ---
gdp_nom_final = aggregate_yearly(gdp_nominal_obs, mode='average')
gdp_real_final = aggregate_yearly(gdp_real_obs, mode='average')
total_final = aggregate_yearly(total_trade_obs, mode='average')

goods_raw = aggregate_yearly(goods_obs, mode='sum')
services_raw = aggregate_yearly(services_obs, mode='sum')

# Dynamic calculation check for the active calendar year
current_year = str(datetime.datetime.now().year)

annual_economy = []
for year in sorted(gdp_nom_final.keys(), reverse=True):
    g_val = goods_raw.get(year, 0) / 1000
    s_val = services_raw.get(year, 0) / 1000
    
    # Handle Current-Year Linear Annualization for Monthly Subsets
    if year == current_year:
        months_reported = len([o for o in goods_obs if o['date'].startswith(current_year) and o['value'] not in ['.', '']])
        if 0 < months_reported < 12:
            g_val = (g_val / months_reported) * 12
            s_val = (s_val / months_reported) * 12

    t_val = total_final.get(year, g_val + s_val)
    
    # Calculate inflation-adjusted Real Headline growth rate
    real_growth = 0.0
    current_real = gdp_real_final.get(year)
    prev_year = str(int(year) - 1)
    prev_real = gdp_real_final.get(prev_year)
    
    if current_real and prev_real:
        real_growth = (current_real - prev_real) / prev_real

    annual_economy.append({
        "year": year,
        "gdp_nominal": gdp_nom_final.get(year, 0),
        "gdp_growth_real": real_growth,
        "trade_total": t_val,
        "trade_goods": g_val,
        "trade_services": s_val
    })

# --- PIPELINE DEPLOYMENT WRITE ---
# Saved straight to the root directory file to match repository setup
with open('annual_data.json', 'w') as f:
    json.dump(annual_economy, f, indent=4)

print(f"Annual Update Complete: {len(annual_economy)} records. Sample 2024 Real Growth: {gdp_real_final.get('2024')}")
