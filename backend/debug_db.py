from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("--- Diagnostics: Traffic Stats Write ---")

# 1. Try Extended Stats (New Schema)
extended_data = {
    "total_packets": 11,
    "tcp_packets": 11,
    "udp_packets": 0,
    "icmp_packets": 0,
    "http_packets": 5,
    "https_packets": 3,
    "dns_packets": 2
}
print(f"Attempting to insert extended data: {extended_data}")
try:
    supabase.table("traffic_stats").insert(extended_data).execute()
    print("SUCCESS: Extended stats inserted.")
except Exception as e:
    print(f"FAILED: Extended stats insert failed. Reason: {e}")

    # 2. Try Basic Stats (Old Schema)
    basic_data = {
        "total_packets": 5,
        "tcp_packets": 5,
        "udp_packets": 0,
        "icmp_packets": 0
    }
    print(f"\nAttempting to insert basic data: {basic_data}")
    try:
        supabase.table("traffic_stats").insert(basic_data).execute()
        print("SUCCESS: Basic stats inserted (Fallback works).")
    except Exception as e2:
        print(f"FAILED: Basic stats insert also failed. Reason: {e2}")
