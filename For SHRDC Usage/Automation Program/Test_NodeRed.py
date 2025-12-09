import requests

NODE_RED_URL = "http://192.168.8.201:1880/test"  # change to your Node-RED IP

def test_connection():
    try:
        r = requests.get(NODE_RED_URL, timeout=5)
        r.raise_for_status()
        print("✅ Connected to Node-RED:", r.json())
    except Exception as e:
        print("❌ Error connecting to Node-RED:", e)

if __name__ == "__main__":
    test_connection()