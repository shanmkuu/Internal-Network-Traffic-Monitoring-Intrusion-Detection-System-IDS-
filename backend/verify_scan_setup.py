import urllib.request
import urllib.error
import json
import os
from supabase import create_client

# Load env safely or hardcode? Better to rely on what system usually does.
# We will try to read .env first
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

print("--- 1. Checking API Endpoint ---")
try:
    # Try sending a POST request to start scan
    req = urllib.request.Request(
        "http://localhost:8000/api/scan/start", 
        method="POST"
    )
    with urllib.request.urlopen(req) as response:
        print(f"API Response: {response.status}")
        print("  [PASS] Endpoint exists.")
except urllib.error.HTTPError as e:
    if e.code == 404:
        print(f"API Error: {e.code} Not Found.")
        print("  [FAIL] Endpoint MISSING. You need to restart 'main.py'.")
    elif e.code == 422:
        print(f"API Error: {e.code} Unprocessable Entity (Expected if missing body but endpoint exists).")
        print("  [PASS] Endpoint exists.")
    else:
        print(f"API Error: {e.code} {e.reason}")
except Exception as e:
    print(f"Connection Failed: {e}")
    print("  [FAIL] Is the backend running?")

print("\n--- 2. Checking Database Table 'scan_results' ---")
if not url or not key:
    print("  [SKIP] Database credentials not found in env.")
else:
    try:
        supabase = create_client(url, key)
        # Try a select. If table doesn't exist, it should error.
        res = supabase.table("scan_results").select("count", count="exact").limit(1).execute()
        print("  [PASS] Table 'scan_results' exists.")
    except Exception as e:
        print(f"Database Error: {e}")
        print("  [FAIL] Table 'scan_results' likely MISSING. Run 'create_scan_results.sql' in Supabase.")
