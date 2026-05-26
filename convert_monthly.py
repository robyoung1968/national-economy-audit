import json
import csv

def export_monthly_to_csv():
    try:
        # Load the raw monthly JSON data
        with open('economic_data.json', 'r') as f:
            data = json.load(f)
        
        if not data:
            print("Monthly JSON file is empty.")
            return

        # Sort chronologically by date
        data.sort(key=lambda x: x.get('month_date', ''))

        # Extract headers dynamically from the first dictionary object
        headers = list(data[0].keys())

        # Write straight to clean CSV text
        output_filename = 'economic_data.csv'
        with open(output_filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
            
        print(f"Success: Generated '{output_filename}' using native modules.")
        
    except Exception as e:
        print(f"Error processing monthly data: {e}")

if __name__ == "__main__":
    export_monthly_to_csv()
