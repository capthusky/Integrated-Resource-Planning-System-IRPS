import requests
import json

BASE_URL = "http://localhost:8000"
API_KEY = "50888bcaf6d0f88"
API_SECRET = "010a4174ecf21bf"

AUTH_HEADER = {
    "Authorization": f"token {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json"
}

def get_bom_details(bom_name):
    url = f"{BASE_URL}/api/resource/BOM/{bom_name}"
    response = requests.get(url, headers=AUTH_HEADER)
    response.raise_for_status()
    return response.json()["data"]

if __name__ == "__main__":
    bom_name = input("Enter BOM name to test: ").strip()
    try:
        bom_details = get_bom_details(bom_name)
        print(f"Full BOM data for {bom_name}:\n{json.dumps(bom_details, indent=2)}\n")

        operations = bom_details.get("operations")
        if operations is None:
            print(f"❌ No 'operations' key found in BOM {bom_name}.")
        elif len(operations) == 0:
            print(f"⚠️ BOM {bom_name} has an empty 'operations' list.")
        else:
            print(f"✅ BOM {bom_name} has {len(operations)} operation(s):")
            for i, op in enumerate(operations, start=1):
                print(f"  Operation {i}: {op}")

    except Exception as e:
        print(f"Error fetching BOM details: {e}")