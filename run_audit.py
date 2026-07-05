import os, json, requests
from collections import defaultdict

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

def fetch_fred_series(series_id, limit=1000):  # Increased limit slightly to handle weekly series back to 2008
    api_key = os.environ.get('FRED_API_KEY')
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json&sort_order=desc&limit={limit}&observation_start=2008-01-01"
    try:
        res = requests.get(url, timeout=15).json()
        return [{"value": float(obs['value']), "date": obs['date']} for obs in res.get('observations', []) if obs['value'] != '.']
    except: 
        return []

def aggregate_weekly_to_monthly(weekly_data):
    """Computes monthly averages and ongoing MTD averages from raw weekly FRED observations."""
    monthly_groups = defaultdict(list)
    for obs in weekly_data:
        month_key = obs['date'][:7]
        monthly_groups[month_key].append(obs['value'])
    
    # Calculate the mean for each month group
    return {month_key: round(sum(values) / len(values), 2) for month_key, values in monthly_groups.items()}

# Fetch core existing datasets
debt_map = fetch_treasury_debt()
cpi_data = fetch_fred_series('CPIAUCSL')
u3_data = fetch_fred_series('UNRATE')
u6_data = fetch_fred_series('U6RATE')

# Fetch new expanded employment datasets
lfpr_data = fetch_fred_series('CIVPART')
not_lf_data = fetch_fred_series('LNS15000000')
lt_count_data = fetch_fred_series('UEMP27OV')
lt_pct_data = fetch_fred_series('LNS13025703')
jts_job_data = fetch_fred_series('JTSJOR')
jts_quit_data = fetch_fred_series('JTSQUR')

# Fetch weekly data and instantly aggregate them into monthly averages
initial_claims_map = aggregate_weekly_to_monthly(fetch_fred_series('ICSA', limit=1500))
continued_claims_map = aggregate_weekly_to_monthly(fetch_fred_series('CCSA', limit=1500))

# CRITICAL SECURITY GUARD: Do not overwrite the database if core upstream macro APIs returned blank
if not debt_map or not cpi_data or not u3_data or not u6_data or not lfpr_data:
    print("CRITICAL: One or more upstream macro APIs returned an empty response.")
    print("Aborting run to protect historical database integrity.")
    exit(1)

# Gather every unique YYYY-MM across all datasets
all_months = set()
all_months.update(debt_map.keys())
all_months.update(obs['date'][:7] for obs in cpi_data)
all_months.update(obs['date'][:7] for obs in u3_data)
all_months.update(obs['date'][:7] for obs in u6_data)
all_months.update(obs['date'][:7] for obs in lfpr_data)

sorted_months = sorted(list(all_months))
economy_data = []

for month_key in sorted_months:
    # Match standard observations
    cpi_match = next((d for d in cpi_data if d['date'][:7] == month_key), None)
    u3_match = next((d for d in u3_data if d['date'][:7] == month_key), None)
    u6_match = next((d for d in u6_data if d['date'][:7] == month_key), None)
    
    # Match new expanded observations
    lfpr_match = next((d for d in lfpr_data if d['date'][:7] == month_key), None)
    not_lf_match = next((d for d in not_lf_data if d['date'][:7] == month_key), None)
    lt_count_match = next((d for d in lt_count_data if d['date'][:7] == month_key), None)
    lt_pct_match = next((d for d in lt_pct_data if d['date'][:7] == month_key), None)
    jts_job_match = next((d for d in jts_job_data if d['date'][:7] == month_key), None)
    jts_quit_match = next((d for d in jts_quit_data if d['date'][:7] == month_key), None)
    
    # Value parsing (Value if present, else explicit None)
    debt_val = debt_map[month_key] if month_key in debt_map else None
    cpi_val  = cpi_match['value'] if cpi_match else None
    u3_val   = u3_match['value'] if u3_match else None
    u6_val   = u6_match['value'] if u6_match else None
    
    lfpr_val = lfpr_match['value'] if lfpr_match else None
    not_lf_val = not_lf_match['value'] if not_lf_match else None
    lt_count_val = lt_count_match['value'] if lt_count_match else None
    lt_pct_val = lt_pct_match['value'] if lt_pct_match else None
    jts_job_val = jts_job_match['value'] if jts_job_match else None
    jts_quit_val = jts_quit_match['value'] if jts_quit_match else None
    
    # Map pre-aggregated weekly dictionaries
    initial_claims_val = initial_claims_map.get(month_key, None)
    continued_claims_val = continued_claims_map.get(month_key, None)
    
    precise_date = cpi_match['date'] if cpi_match else (u3_match['date'] if u3_match else f"{month_key}-01")
    
    economy_data.append({
        "month_date": precise_date,
        "avg_monthly_debt": debt_val,
        "cpi_index": cpi_val,
        "u3_rate": u3_val,
        "u6_rate": u6_val,
        "lfpr_rate": lfpr_val,
        "not_in_labor_force": not_lf_val,
        "long_term_unemp_count": lt_count_val,
        "long_term_unemp_pct": lt_pct_val,
        "job_openings_rate": jts_job_val,
        "quits_rate": jts_quit_val,
        "initial_claims_monthly_avg": initial_claims_val,
        "continued_claims_monthly_avg": continued_claims_val
    })

# Invert array order to preserve descending chronology (Newest first)
economy_data.reverse()

with open('economic_data.json', 'w') as f:
    json.dump(economy_data, f, indent=4)

print(f"Pipeline executed successfully. Matrix generated with {len(economy_data)} rows.")
