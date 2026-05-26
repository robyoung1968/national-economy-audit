import json
import csv

def export_monthly_to_csv():
    # Removed try/except so GitHub Actions can read the raw error
    with open('economic_data.json', 'r') as f:
        data = json.load(f)
    
    if not data:
        print("Monthly JSON file is empty.")
        return

    data.sort(key=lambda x: x.get('month_date', ''))
    headers = list(data[0].keys())

    output_filename = 'economic_data.csv'
    with open(output_filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        
    print(f"Success: Generated '{output_filename}' using native modules.")

if __name__ == "__main__":
    export_monthly_to_csv()
