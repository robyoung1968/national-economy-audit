# --- EXECUTION ---

# A. Fetch Data
print("Fetching daily/monthly data...")
debt_df = fetch_treasury_debt(90)
cpi_df = fetch_fred_data('CPIAUCSL')
u3_df = fetch_fred_data('UNRATE')
u6_df = fetch_fred_data('U6RATE')

print("Fetching annual data (GDP/Trade Balance)...")
gdp_df = fetch_fred_data('GDPCA').rename(columns={'value': 'real_gdp', 'date': 'record_date'})
net_exports_df = fetch_fred_data('NETEXP').rename(columns={'value': 'net_exports', 'date': 'record_date'})
goods_df = fetch_fred_data('IEAXGS').rename(columns={'value': 'goods_balance', 'date': 'record_date'})
services_df = fetch_fred_data('IEAXS').rename(columns={'value': 'services_balance', 'date': 'record_date'})

# B. Upload Individual Monthly/Daily Tables to BigQuery
upload_to_bq(debt_df, "treasury_debt_historical")
upload_to_bq(cpi_df, "fred_cpi_historical")
upload_to_bq(u3_df, "fred_unemployment_u3_historical")
upload_to_bq(u6_df, "fred_unemployment_u6_historical")

# C. Merge Annual Indicators & Upload to BigQuery
annual_df = pd.DataFrame() 
if not gdp_df.empty:
    print("Merging annual indicators...")
    annual_df = pd.merge(gdp_df, net_exports_df, on='record_date', how='outer')
    annual_df = pd.merge(annual_df, goods_df, on='record_date', how='outer')
    annual_df = pd.merge(annual_df, services_df, on='record_date', how='outer')
    
    annual_df['regime'] = 'Historical'
    upload_to_bq(annual_df, "annual_economy_indicators")

# D. EXPORT FOR DASHBOARD
if not annual_df.empty:
    # Sanitization
    annual_df_sanitized = annual_df.where(pd.notnull(annual_df), None)

    export_data = {
        "last_updated": datetime.datetime.now().isoformat(),
        "data": annual_df_sanitized.to_dict(orient='records') # This 'data' key is vital
    }

    with open('economic_data.json', 'w') as f: # Filename alignment
        json.dump(export_data, f, default=json_serial, indent=4)

    print("Local data.json created successfully with null handling.")

    print("All tasks complete. Data Refresh Success.")
