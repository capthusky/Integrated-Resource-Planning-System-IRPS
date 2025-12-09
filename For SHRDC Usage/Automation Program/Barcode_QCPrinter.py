import requests
import time
import sys
import threading
from flask import Flask, request

NODE_RED_URL = "http://192.168.8.227:1880"
PYTHON_PORT = 5000

# --- Flask setup ---
app = Flask(__name__)
user_input = None

@app.route("/qc_event", methods=["POST"])
def qc_event():
    global user_input
    data = request.get_json()
    user_input = data.get("color")
    print(f"🎯 Button pressed: {user_input}")
    return {"ok": True}

def run_flask():
    app.run(host="0.0.0.0", port=PYTHON_PORT, debug=False, use_reloader=False)

# --- Node-RED functions ---
def ping_nodered():
    try:
        r = requests.get(f"{NODE_RED_URL}/ping", timeout=3)
        if r.status_code == 200:
            print("✅ Node-RED online:", r.json())
            return True
    except Exception as e:
        print("❌ Ping failed:", e)
    return False

def switch_flow_mode(action: str):
    try:
        r = requests.post(f"{NODE_RED_URL}/flow_mode", json={"action": action}, timeout=30)
        if r.status_code == 200:
            data = r.json()
            print(f"🔀 Flow mode switched: {data}")
            return True
        else:
            print(f"⚠️ Flow mode switch failed (HTTP {r.status_code})")
    except Exception as e:
        print(f"❌ Flow mode switch error: {e}")
    return False

# --- Main QC loop ---
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()

    if not ping_nodered():
        sys.exit("❌ Node-RED not reachable, aborting.")

    if not switch_flow_mode("start"):
        sys.exit("🚫 Failed to switch to QC mode, exiting.")

    print("⏳ QC mode active, waiting for button press or timeout (30s)...")

    start_time = time.time()
    while time.time() - start_time < 30:
        if user_input:
            print(f"✅ User input received ({user_input}), ending QC early.")
            break
        time.sleep(0.5)

    switch_flow_mode("end")
    print("🔁 Reverted back to Sticker mode.")
