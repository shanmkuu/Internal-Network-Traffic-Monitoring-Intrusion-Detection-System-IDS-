import os
import time
from datetime import datetime, timedelta
from supabase import create_client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("DebugDataFlow")

# Load env variables (Manual loading for script)
def load_env():
    try:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            print(f"Loading .env from: {env_path}")
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, val = line.strip().split("=", 1)
                        print(f"   Found Key: {key}")
                        os.environ[key] = val.strip('"\'')
        else:
            print(f"[WARN] .env not found at {env_path} (CWD: {os.getcwd()})")
    except Exception as e:
        print(f"[WARN] Failed to load .env: {e}")

load_env()
url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("VITE_SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_KEY")

def check_data_flow():
    print("\n--- DIAGNOSTIC: DATA FLOW CHECK ---")
    
    if not url or not key:
        print("[FAIL] Missing Supabase credentials in .env")
        print(f"Keys found: {list(os.environ.keys())}")
        return

    try:
        supabase = create_client(url, key)
        
        # 1. Check Traffic Stats (Last 5 minutes)
        print("\n1. Checking 'traffic_stats' (Live Traffic Monitor)...")
        five_mins_ago = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        
        response = supabase.table("traffic_stats")\
            .select("*")\
            .gt("created_at", five_mins_ago)\
            .order("created_at", desc=True)\
            .limit(5)\
            .execute()
            
        rows = response.data
        if not rows:
            print("   [FAIL] No traffic stats recorded in the last 5 minutes.")
            print("   -> CAUSE: The 'monitor.py' script is NOT running or NOT connected to DB.")
        else:
            print(f"   [PASS] Found {len(rows)} recent records.")
            latest = rows[0]
            print(f"   Latest Record ({latest['created_at']}):")
            print(f"     Total Packets: {latest.get('total_packets', 'N/A')}")
            print(f"     TCP: {latest.get('tcp_packets', 0)} | UDP: {latest.get('udp_packets', 0)}")
            
            if latest.get('total_packets', 0) == 0:
                 print("   [WARN] Total Packets is 0. Monitor is running but detecting NOTHING.")
                 print("   -> CAUSE: Wrong Network Interface selected (Virtual Adapter?).")
            else:
                 print("   [SUCCESS] Monitor is writing REAL data.")

        # 2. Check Connected Devices
        print("\n2. Checking 'connected_devices' (Network Analytics)...")
        response = supabase.table("connected_devices")\
            .select("*")\
            .order("last_seen", desc=True)\
            .limit(5)\
            .execute()
            
        devices = response.data
        if not devices:
            print("   [FAIL] No devices found in database.")
            print("   -> CAUSE: 'network_scanner' hasn't run or table is empty.")
        else:
            print(f"   [PASS] Found {len(devices)} devices.")
            for d in devices:
                print(f"     - {d.get('ip_address')} ({d.get('vendor')}) Last Seen: {d.get('last_seen')}")

        # 3. Check Scan Results
        print("\n3. Checking 'scan_results' (Active Scans)...")
        try:
            response = supabase.table("scan_results")\
                .select("*")\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            if response.data:
                print("   [PASS] Scan results exist.")
            else:
                print("   [INFO] No active scan results yet (Normal if you haven't clicked 'Start Scan').")
        except Exception as e:
             print(f"   [FAIL] Could not query 'scan_results': {e}")
             print("   -> CAUSE: Table likely missing. Run 'create_scan_results.sql'.")

    except Exception as e:
        print(f"[CRITICAL] Database Connection Failed: {e}")

if __name__ == "__main__":
    check_data_flow()
