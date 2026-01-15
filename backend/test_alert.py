import requests
import json
import time

# API Endpoint
url = "http://localhost:8000/api/alerts"

# Test Alert Data
payload = {
    "source_ip": "192.168.1.100",
    "destination_ip": "10.0.0.5",
    "protocol": "TEST",
    "alert_type": "Live Data Verification",
    "severity": "High",
    "description": "This is a test alert to verify live dashboard updates."
}

try:
    print(f"Sending test alert to {url}...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print("Success! Alert created.")
        print("Response:", json.dumps(response.json(), indent=2))
        print("\nCheck your dashboard now. You should see 'Live Data Verification' in the Recent Alerts table.")
    else:
        print(f"Failed. Status Code: {response.status_code}")
        print("Response:", response.text)
except Exception as e:
    print(f"Error: {e}")
    print("Is the backend running?")
