import requests
import time

# === CONFIG ===
OCTOPRINT_URL = "http://192.168.8.249/SHRDCPrinter6"  # your OctoPrint URL
OCTOPRINT_API_KEY = "cnya_g4JxPzXap7pBxszMWjzgtsUWULrNlJerQSHYGg"

headers = {"X-Api-Key": OCTOPRINT_API_KEY}


# --- Basic Printer Status ---
def get_printer_state():
    url = f"{OCTOPRINT_URL}/api/printer"
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json().get("state", {}).get("text")


# --- Job Status ---
def get_job_status():
    url = f"{OCTOPRINT_URL}/api/job"
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()


# --- File Listing ---
def list_files():
    url = f"{OCTOPRINT_URL}/api/files/local"
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()

    if "files" not in data or not data["files"]:
        print("⚠️ No files found in OctoPrint storage.")
        return []

    files = [f["name"] for f in data["files"]]
    print("📂 Files available in OctoPrint:")
    for f in files:
        print("   -", f)
    return files


# --- Start a Print Job ---
def start_print(file_name):
    url = f"{OCTOPRINT_URL}/api/files/local/{file_name}"
    payload = {"command": "select", "print": True}
    r = requests.post(url, headers=headers, json=payload, timeout=10)
    r.raise_for_status()
    print(f"🖨️ Started printing: {file_name}")


# --- Main Loop ---
def main():
    try:
        # Test connection
        state = get_printer_state()
        print(f"✅ Connected to OctoPrint | Printer state: {state}")

        # List files
        available_files = list_files()
        if not available_files:
            print("⚠️ Upload GCODE files first.")
            return

        # Pick first file for demo (you can change this logic)
        file_to_print = "Part Studio 1 - Part 1_PLA_20s (1).gcode"
        print(f"👉 Selected file for printing: {file_to_print}")

        # Start printing
        start_print(file_to_print)

        # Poll job status until done
        print("\n🔄 Monitoring print progress...")
        while True:
            job = get_job_status()
            state = job.get("state")
            progress = job.get("progress", {})
            job_info = job.get("job", {}).get("file", {})

            completion = progress.get("completion")
            elapsed = progress.get("printTime")
            remaining = progress.get("printTimeLeft")
            file_name = job_info.get("name")

            print(
                f"State: {state} | File: {file_name} | "
                f"Progress: {completion}% | Elapsed: {elapsed}s | Remaining: {remaining}s"
            )

            if state == "Operational" and completion == 100:
                print(f"✅ Print finished: {file_name}")
                break

            time.sleep(5)

    except Exception as e:
        print("❌ Error communicating with OctoPrint:", e)


if __name__ == "__main__":
    main()
