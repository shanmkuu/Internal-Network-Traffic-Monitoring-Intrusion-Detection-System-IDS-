import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Missing env vars")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# UUID tables
uuid_tables = [
    "alerts",
    "traffic_stats",
    "system_status",
    "wazuh_blocks",
    "devices"
]

# Bigint tables
bigint_tables = [
    "discovery_logs",
    "scan_results"
]

print("Clearing database...")

for t in bigint_tables:
    try:
        # Delete where id >= 0
        res = supabase.table(t).delete().gte("id", 0).execute()
        print(f"Cleared {t}: {len(res.data)} rows deleted.")
    except Exception as e:
        print(f"Failed to clear {t}: {e}")

for t in uuid_tables:
    try:
        # Delete where id != a dummy UUID
        res = supabase.table(t).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"Cleared {t}: {len(res.data)} rows deleted.")
    except Exception as e:
        print(f"Failed to clear {t}: {e}")

print("Done.")
