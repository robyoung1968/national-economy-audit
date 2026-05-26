import json
import csv

def export_annual_to_csv():
    # Removed try/except so GitHub Actions can read the raw error
    with open('annual_data.json', 'r') as f:
        data = json.load(f)
        
    if not data:
        print("Annual JSON file is empty.")
        return

    data.sort(key=lambda x: int(x.get('year', 0)))
    headers = list(data[0].keys())

    output_filename = 'annual_data.csv'
    with open(output_filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        
    print(f"Success: Generated '{output_filename}' using native modules.")

if __name__ == "__main__":
    export_annual_to_csv()
