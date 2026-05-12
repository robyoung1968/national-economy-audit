import os, json, requests

def fetch_fred_data(series_id):
    api_key = os.environ.get('FRED_API_KEY')
    # Removed limit to ensure we get all historical quarterly points
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
            # Sum for quarterly/monthly trade values
            final_data[year] = sum(values)
        else:
            # Average for annualized GDP
            final_data[year] = sum(values) / len(values)
    return final_data

# GDP (Quarterly, Annualized Rate)
gdp_obs = fetch_fred_data('GDP') 
# Trade Components (Quarterly Net Balances)
# Using 'NETEXP' for total, 'GNETB' for goods, 'SNETB' for services
total_trade_obs = fetch_fred_data('NETEXP')
goods_obs = fetch_fred_data('GNETB')
services_obs = fetch_fred_data('SNETB')

gdp_final = aggregate_yearly(gdp_obs, mode='average')
total_final = aggregate_yearly(total_trade_obs, mode='average') # NETEXP is already annualized
goods_final = aggregate_yearly(goods_obs, mode='average') 
services_final = aggregate_yearly(services_obs, mode='average')

annual_economy = []
for year in sorted(gdp_final.keys(), reverse=True):
    # GDP and NETEXP are already in Billions
    # Goods and Services (GNETB/SNETB) are in Billions too
    g_val = goods_final.get(year, 0)
    s_val = services_final.get(year, 0)
    t_val = total_final.get(year, g_val + s_val) # Fallback to sum if NETEXP missing
    
    annual_economy.append({
        "year": year,
        "gdp_nominal": gdp_final[year],
        "trade_total": t_val,
        "trade_goods": g_val,
        "trade_services": s_val
    })

with open('annual_data.json', 'w') as f:
    json.dump(annual_economy, f, indent=4)

print(f"Annual Update Complete: {len(annual_economy)} records. Sample 2024 Trade: {total_final.get('2024')}")
