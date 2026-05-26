import json
import csv
import os

def export_monthly_to_csv():
    filename = 'economic_data.json'
    output_filename = 'economic_data.csv'
    
    # Debug print to confirm exactly where the cloud computer is looking
    print(f"Current working directory: {os.getcwd()}")
    print(f"Checking for file: {os.path.abspath(filename)}")
    
    if not os.path.exists(filename):
        print(f"CRITICAL ERROR: '{filename}' does not exist in this directory.")
        return

    with open(filename, 'r') as f:
        data = json.load(f)
    
    print(f"Loaded JSON successfully. Records found: {len(data)}")
    
    if not data or len(data) == 0:
        print("ERROR: JSON data array is empty. Cannot parse to CSV.")
        return

    # Sort and extract headers
    data.sort(key=lambda x: x.get('month_date', ''))
    headers = list(data[0].keys())

    with open(output_filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        
    print(f"Success: Generated '{output_filename}' in root directory.")

if __name__ == "__main__":
    export_monthly_to_csv()
