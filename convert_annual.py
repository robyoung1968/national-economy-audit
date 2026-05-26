import pandas as pd

def export_annual_to_csv():
    try:
        # Load the annual JSON dataset
        df = pd.read_json('annual_data.json')
        
        # Ensure chronological order by year
        if 'year' in df.columns:
            df = df.sort_values('year', ascending=True)
            
        # Export straight to CSV
        output_filename = 'annual_data.csv'
        df.to_csv(output_filename, index=False)
        print(f"Success: Generated '{output_filename}' from annual JSON.")
        
    except Exception as e:
        print(f"Error processing annual data: {e}")

if __name__ == "__main__":
    export_annual_to_csv()
