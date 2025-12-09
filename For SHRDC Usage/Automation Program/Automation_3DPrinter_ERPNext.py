import requests
import time
import os
import json
import re
from datetime import datetime

# === CONFIGURATION ===
BASE_URL = "http://localhost:8000"
API_KEY = "43fd33ddcda2fe6"
API_SECRET = "0955c609f037d12"

AUTH_HEADER = {
    "Authorization": f"token {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json"
}

PROCESSED_FILE = "processed_so.json"
LOG_FILE = "error_log.txt"

# === OCTOPRINT CONFIG (printer6 / GOLD) ===
OCTOPRINT_URL = "http://192.168.8.249/SHRDCPrinter6"
OCTOPRINT_API_KEY = "cnya_g4JxPzXap7pBxszMWjzgtsUWULrNlJerQSHYGg"
OCTO_HEADERS = {"X-Api-Key": OCTOPRINT_API_KEY}

# === ITEM → GCODE Mapping ===
ITEM_TO_GCODE = {
    "BCP-001-RED": "Cake bottom 3_PLA_42m3s.gcode",
    #"CUS-BLA": "trophy_PPG_PLA_1h13m.gcode",
    "CUS-BLA": "Part Studio 1 - Part 1_PLA_20s (1).gcode",
    "TCP-001-RED": "top.gcode",
    # Add future colors/items here
}

# === STATE HANDLING ===
def load_processed():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_processed(processed):
    with open(PROCESSED_FILE, "w") as f:
        json.dump(list(processed), f)

# === LOGGING ===
def remove_unicode_symbols(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)

def log_error(message):
    clean_message = remove_unicode_symbols(str(message))
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} - {clean_message}\n")

# === DOCUMENT STATUS HANDLING ===
def submit_doc(doctype, name):
    url = f"{BASE_URL}/api/resource/{doctype}/{name}/submit"
    response = requests.post(url, headers=AUTH_HEADER)
    response.raise_for_status()
    print(f"[✓] Submitted {doctype}: {name}")

def check_doc_status(doctype, name, expected_status=1, retries=5):
    for attempt in range(retries):
        url = f"{BASE_URL}/api/resource/{doctype}/{name}"
        response = requests.get(url, headers=AUTH_HEADER)
        response.raise_for_status()
        doc = response.json()["data"]
        if doc.get("docstatus") == expected_status:
            print(f"[✓] {doctype} {name} is in expected docstatus: {expected_status}")
            return True
        print(f"[...] Waiting for {doctype} {name} to reach docstatus {expected_status}")
        time.sleep(2)
    raise Exception(f"{doctype} {name} did not reach docstatus {expected_status} after {retries} retries")

# === API UTILITIES ===
def frappe_set_value(doctype, name, fieldname, value):
    url = f"{BASE_URL}/api/method/frappe.client.set_value"
    payload = {"doctype": doctype, "name": name, "fieldname": fieldname, "value": value}
    resp = requests.post(url, headers=AUTH_HEADER, json=payload)
    resp.raise_for_status()
    return resp.json()

def get_submitted_sales_orders():
    url = f"{BASE_URL}/api/resource/Sales Order"
    filters = [["docstatus", "=", 1]]
    params = {
        "fields": '["name", "transaction_date", "customer"]',
        "filters": json.dumps(filters)
    }
    response = requests.get(url, headers=AUTH_HEADER, params=params)
    response.raise_for_status()
    data = response.json()["data"]
    print(f"DEBUG: Found {len(data)} submitted sales orders")
    return data

def get_sales_order_items(so_name):
    url = f"{BASE_URL}/api/resource/Sales Order/{so_name}"
    response = requests.get(url, headers=AUTH_HEADER)
    response.raise_for_status()
    return response.json()["data"]["items"]

def get_default_bom(item_code):
    url = f"{BASE_URL}/api/resource/BOM?filters=[[\"item\", \"=\", \"{item_code}\"],[\"is_default\", \"=\", 1]]"
    response = requests.get(url, headers=AUTH_HEADER)
    response.raise_for_status()
    boms = response.json()["data"]
    return boms[0]["name"] if boms else None

def get_bom_details(bom_name):
    url = f"{BASE_URL}/api/resource/BOM/{bom_name}"
    response = requests.get(url, headers=AUTH_HEADER)
    response.raise_for_status()
    return response.json()["data"]

# === MANUFACTURING FLOW ===
def create_work_order(item, bom_name):
    payload = {
        "production_item": item["item_code"],
        "qty": item["qty"],
        "bom_no": bom_name,
        "company": "Selangor Human Resource Development Centre",
        "fg_warehouse": "Finished Goods - SHRDC",
        "wip_warehouse": "Work In Progress - SHRDC",
        "planned_start_date": datetime.now().isoformat(),
        "sales_order": item["parent"],
        "sales_order_item": item["name"],
        "use_operations": 0,
        "docstatus": 1
    }

    url = f"{BASE_URL}/api/resource/Work Order"
    response = requests.post(url, headers=AUTH_HEADER, json={"data": payload})
    response.raise_for_status()
    wo = response.json()["data"]
    print(f"[✓] Work Order {wo['name']} created and submitted (docstatus: {wo.get('docstatus')})")
    return wo["name"]

def mark_work_order_in_process(work_order_name):
    print(f"[📌] Marking Work Order {work_order_name} as In Process")
    url = f"{BASE_URL}/api/resource/Work Order/{work_order_name}"
    payload = {"status": "In Process"}
    response = requests.put(url, headers=AUTH_HEADER, json=payload)
    response.raise_for_status()

def create_material_transfer(work_order_name):
    print(f"[📦] Creating Material Transfer for Work Order: {work_order_name}")
    wo_url = f"{BASE_URL}/api/resource/Work Order/{work_order_name}"
    wo = requests.get(wo_url, headers=AUTH_HEADER).json()["data"]

    generate_url = f"{BASE_URL}/api/method/erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry"
    payload = {"work_order_id": work_order_name, "purpose": "Material Transfer for Manufacture", "qty": wo["qty"]}
    resp = requests.post(generate_url, headers=AUTH_HEADER, json=payload)
    resp.raise_for_status()
    se_data = resp.json().get("message")
    if not se_data:
        raise Exception("make_stock_entry did not return expected message payload")

    se_data["docstatus"] = 1
    create_url = f"{BASE_URL}/api/resource/Stock Entry"
    response = requests.post(create_url, headers=AUTH_HEADER, json={"data": se_data})
    response.raise_for_status()
    se = response.json()["data"]
    print(f"[✓] Material Transfer Stock Entry created and submitted: {se['name']}")
    check_doc_status("Stock Entry", se["name"])
    return se["name"]

def complete_work_order(work_order_name):
    print(f"[🏁] Completing Work Order: {work_order_name}")
    wo = requests.get(
        f"{BASE_URL}/api/resource/Work Order/{work_order_name}",
        headers=AUTH_HEADER
    ).json()["data"]
    produced_qty = wo.get("qty", 0)

    generate_url = f"{BASE_URL}/api/method/erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry"
    payload = {
        "work_order_id": work_order_name,
        "purpose": "Manufacture",
        "qty": produced_qty
    }
    resp = requests.post(generate_url, headers=AUTH_HEADER, json=payload)
    resp.raise_for_status()
    se_data = resp.json().get("message")

    if not se_data:
        raise Exception("make_stock_entry did not return expected message payload")

    se_data["docstatus"] = 1
    create_url = f"{BASE_URL}/api/resource/Stock Entry"
    response = requests.post(create_url, headers=AUTH_HEADER, json={"data": se_data})
    response.raise_for_status()
    se = response.json()["data"]
    print(f"[✓] Manufacture Stock Entry created and submitted: {se['name']}")
    check_doc_status("Stock Entry", se["name"])

    print(f"[...] Waiting for Work Order {work_order_name} to complete...")
    check_doc_status("Work Order", work_order_name, expected_status=1)
    wo_after = requests.get(
        f"{BASE_URL}/api/resource/Work Order/{work_order_name}",
        headers=AUTH_HEADER
    ).json()["data"]

    if wo_after.get("status") == "Completed":
        print(f"[✅] Work Order {work_order_name} marked as Completed by ERPNext")
    else:
        print(f"[⚠] Work Order {work_order_name} did not auto-complete. Current status: {wo_after.get('status')}")
        log_error(f"WO {work_order_name} stuck at status {wo_after.get('status')}")

def is_sales_order_completed(so_name):
    try:
        items = get_sales_order_items(so_name)
        for item in items:
            url = f"{BASE_URL}/api/resource/Work Order?filters=" + json.dumps([
                ["production_item", "=", item["item_code"]],
                ["sales_order", "=", so_name],
                ["sales_order_item", "=", item["name"]],
                ["docstatus", "=", 1]
            ])
            response = requests.get(url, headers=AUTH_HEADER)
            response.raise_for_status()
            if not response.json()["data"]:
                return False
        return True
    except Exception as e:
        print(f"[!] Error checking SO completion: {e}")
        log_error(f"Error in is_sales_order_completed for {so_name}: {e}")
        return False

# === OCTOPRINT HELPERS ===
def get_printer_state():
    try:
        url = f"{OCTOPRINT_URL}/api/printer"
        r = requests.get(url, headers=OCTO_HEADERS, timeout=10)
        r.raise_for_status()
        return r.json().get("state", {}).get("text")
    except Exception as e:
        return f"Unavailable ({e})"

def get_job_status():
    url = f"{OCTOPRINT_URL}/api/job"
    r = requests.get(url, headers=OCTO_HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()

def start_print(file_name):
    url = f"{OCTOPRINT_URL}/api/files/local/{file_name}"
    payload = {"command": "select", "print": True}
    r = requests.post(url, headers=OCTO_HEADERS, json=payload, timeout=10)
    r.raise_for_status()
    print(f"[🖨] Started printing: {file_name}")

def monitor_print_until_done():
    print("[🔄] Monitoring OctoPrint job...")
    while True:
        try:
            job = get_job_status()
        except Exception as e:
            print(f"[⚠] Could not fetch job status: {e}")
            log_error(f"OctoPrint job status error: {e}")
            time.sleep(5)
            continue

        state = job.get("state")
        progress = job.get("progress", {})
        job_info = job.get("job", {}).get("file", {})

        completion = progress.get("completion")
        elapsed = progress.get("printTime")
        remaining = progress.get("printTimeLeft")
        file_name = job_info.get("name")

        print(
            f"   State: {state} | File: {file_name} | "
            f"Progress: {completion}% | Elapsed: {elapsed}s | Remaining: {remaining}s"
        )

        if state == "Operational" and completion == 100:
            print(f"[✅] Print finished: {file_name}")
            return True

        if state in ("Error", "Cancelled"):
            print(f"[❌] Print interrupted: {state}")
            log_error(f"OctoPrint job interrupted for {file_name} (state={state})")
            return False

        time.sleep(5)

# === MAIN LOOP ===
def main():
    try:
        printer_state = get_printer_state()
        print(f"[🟢] OctoPrint status at startup: {printer_state}")
    except Exception as e:
        print(f"[❌] OctoPrint check failed at startup: {e}")

    processed = load_processed()
    print("🟢 Watching for new submitted Sales Orders...")

    while True:
        try:
            sales_orders = get_submitted_sales_orders()
            for so in sales_orders:
                so_name = so["name"]
                if so_name in processed:
                    continue

                if is_sales_order_completed(so_name):
                    print(f"[⏭] Sales Order {so_name} already completed. Skipping.")
                    processed.add(so_name)
                    save_processed(processed)
                    continue

                print(f"\n📦 New Sales Order detected: {so_name}")
                items = get_sales_order_items(so_name)
                all_success = True

                for item in items:
                    item_code = item["item_code"]
                    qty = item["qty"]
                    print(f"[→] Processing item: {item_code} (Qty: {qty})")

                    try:
                        bom = get_default_bom(item_code)
                        if not bom:
                            print(f"[!] No BOM for item {item_code}, skipping.")
                            all_success = False
                            continue

                        work_order = create_work_order(item, bom)
                        create_material_transfer(work_order)
                        mark_work_order_in_process(work_order)

                        # Use strict ITEM_TO_GCODE mapping
                        gcode_file = ITEM_TO_GCODE.get(item_code)
                        if not gcode_file:
                            print(f"[❌] No GCODE mapping for item '{item_code}'. Stopping process for this SO.")
                            all_success = False
                            break  # stop processing further items for this SO

                        print(f"[🖨] Triggering print for Work Order {work_order}: {gcode_file}")
                        try:
                            start_print(gcode_file)
                        except Exception as e:
                            print(f"[❌] Failed to start print for {gcode_file}: {e}")
                            log_error(f"Failed to start OctoPrint job for {gcode_file}: {e}")
                            all_success = False
                            break

                        ok = monitor_print_until_done()
                        if not ok:
                            print(f"[❌] Print failed for {item_code} in SO {so_name}.")
                            all_success = False
                            break

                        complete_work_order(work_order)

                    except Exception as item_error:
                        print(f"❌ Error processing item {item_code} in SO {so_name}: {item_error}")
                        log_error(f"Item error in SO {so_name}: {item_error}")
                        all_success = False
                        break  # stop on first item failure

                if all_success:
                    processed.add(so_name)
                    save_processed(processed)
                    print(f"[✔] Sales Order {so_name} fully processed.")
                else:
                    print(f"[↩] Sales Order {so_name} not fully processed. Will retry later.")

        except Exception as e:
            print(f"❌ Global Error: {e}")
            log_error(f"Global error: {e}")

        time.sleep(10)

if __name__ == "__main__":
    main()
