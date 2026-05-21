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
# GDP (Quarterly, Annualized Rates)
gdp_nominal_obs = fetch_fred_data('GDP')     # For Nominal GDP scale volume
gdp_real_obs = fetch_fred_data('GDPC1')       # For Headline Real GDP growth rates

# Total Trade Balance (Quarterly, Annualized Rate)
total_trade_obs = fetch_fred_data('NETEXP')

# Component Trade (Monthly Balance of Payments)
goods_obs = fetch_fred_data('BOPGTB')
services_obs = fetch_fred_data('BOPSTB')

# --- AGGREGATE DATA BY YEAR ---
gdp_nom_final = aggregate_yearly(gdp_nominal_obs, mode='average')
gdp_real_final = aggregate_yearly(gdp_real_obs, mode='average')
total_final = aggregate_yearly(total_trade_obs, mode='average')

# Use 'sum' for monthly series to capture cumulative raw values
goods_raw = aggregate_yearly(goods_obs, mode='sum')
services_raw = aggregate_yearly(services_obs, mode='sum')

# Dynamic calculation check for the active calendar year
current_year = str(datetime.datetime.now().year)

annual_economy = []
for year in sorted(gdp_nom_final.keys(), reverse=True):
    # Convert Millions to Billions for monthly component trade data
    g_val = goods_raw.get(year, 0) / 1000
    s_val = services_raw.get(year, 0) / 1000
    
    # PATH 1: Handle Current-Year Linear Annualization for Monthly Subsets
    if year == current_year:
        # Determine how many unique monthly values have been populated so far this year
        months_reported = len([o for o in goods_obs if o['date'].startswith(current_year) and o['value'] not in ['.', '']])
        
        # Apply a proportional run-rate multiplier if the year is active and incomplete
        if 0 < months_reported < 12:
            g_val = (g_val / months_reported) * 12
            s_val = (s_val / months_reported) * 12

    # Pull pre-annualized Net Exports total from FRED, fallback to sum of parts
    t_val = total_final.get(year, g_val + s_val)
    
    # Calculate inflation-adjusted Real Headline growth rate using the GDPC1 series
    real_growth = 0.0
    current_real = gdp_real_final.get(year)
    prev_year = str(int(year) - 1)
    prev_real = gdp_real_final.get(prev_year)
    
    if current_real and prev_real:
        real_growth = (current_real - prev_real) / prev_real

    # Populate verified database schema objects
    annual_economy.append({
        "year": year,
        "gdp_nominal": gdp_nom_final.get(year, 0),
        "gdp_growth_real": real_growth,   # Replaces old nominal math key
        "trade_total": t_val,
        "trade_goods": g_val,
        "trade_services": s_val
    })

# --- PIPELINE DEPLOYMENT WRITE ---
os.makedirs('data', exist_ok=True)
with open('data/annual_data.json', 'w') as f:  # Aligned to match your repository file
    json.dump(annual_economy, f, indent=4)

print(f"Annual Update Complete: {len(annual_economy)} records. Sample 2024 Real Growth: {gdp_real_final.get('2024')}")
