import json
import csv

def export_annual_to_csv():
    try:
        # Load the annual JSON dataset
        with open('annual_data.json', 'r') as f:
            data = json.load(f)
            
        if not data:
            print("Annual JSON file is empty.")
            return

        # Sort chronologically by year integer
        data.sort(key=lambda x: int(x.get('year', 0)))

        # Extract headers dynamically
        headers = list(data[0].keys())

        # Write straight to clean CSV text
        output_filename = 'annual_data.csv'
        with open(output_filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
            
        print(f"Success: Generated '{output_filename}' using native modules.")
        
    except Exception as e:
        print(f"Error processing annual data: {e}")

if __name__ == "__main__":
    export_annual_to_csv()
