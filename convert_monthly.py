import pandas as pd

def export_monthly_to_csv():
    try:
        # Load the raw monthly JSON data
        df = pd.read_json('economic_data.json')
        
        # Optional: Explicitly sort by date to guarantee chronological order in Excel
        if 'month_date' in df.columns:
            df = df.sort_values('month_date', ascending=True)
            
        # Export straight to CSV
        output_filename = 'economic_data.csv'
        df.to_csv(output_filename, index=False)
        print(f"Success: Generated '{output_filename}' from monthly JSON.")
        
    except Exception as e:
        print(f"Error processing monthly data: {e}")

if __name__ == "__main__":
    export_monthly_to_csv()
