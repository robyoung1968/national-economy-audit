import os, json, requests

def fetch_fred_data(series_id):
    api_key = os.environ.get('FRED_API_KEY')
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key_key={api_key}&file_type=json&sort_order=desc&observation_start=2008-01-01"
    try:
        res = requests.get(url).json()
        return res.get('observations', [])
    except:
        return []

def aggregate_yearly(observations, mode='average'):
    yearly_map = {}
    for obs in observations:
        if obs['value'] == '.': continue
        year = obs['date'][:4]
        if year not in yearly_map: yearly_map[year] = []
        yearly_map[year].append(float(obs['value']))
    
    final_data = {}
    for year, values in yearly_map.items():
        if mode == 'sum':
            final_data[year] = sum(values)
        else: # Average for GDP (Annualized Rates)
            final_data[year] = sum(values) / len(values)
    return final_data

# Fetching Net Goods and Net Services
gdp_obs = fetch_fred_data('GDP') 
goods_obs = fetch_fred_data('BOPGNET') # Net Goods
services_obs = fetch_fred_data('BOPSNET') # Net Services

gdp_final = aggregate_yearly(gdp_obs, mode='average')
goods_final = aggregate_yearly(goods_obs, mode='sum')
services_final = aggregate_yearly(services_obs, mode='sum')

annual_economy = []
for year in sorted(gdp_final.keys(), reverse=True):
    # Data is in Millions, convert to Billions
    g_billions = goods_final.get(year, 0) / 1000
    s_billions = services_final.get(year, 0) / 1000
    
    annual_economy.append({
        "year": year,
        "gdp_nominal": gdp_final[year],
        "trade_total": g_billions + s_billions,
        "trade_goods": g_billions,
        "trade_services": s_billions
    })

with open('annual_data.json', 'w') as f:
    json.dump(annual_economy, f, indent=4)
