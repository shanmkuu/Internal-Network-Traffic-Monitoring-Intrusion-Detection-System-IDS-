from supabase import create_client, Client
from dotenv import load_dotenv
import os
import time

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("Checking for recent traffic stats...")
try:
    # Fetch last 5 stats
    response = supabase.table("traffic_stats").select("*").order("created_at", desc=True).limit(5).execute()
    data = response.data
    
    if not data:
        print("No data found in traffic_stats table.")
    else:
        print(f"Found {len(data)} recent records.")
        for row in data:
            print(f"Time: {row.get('created_at')}, Total: {row.get('total_packets')}, TCP: {row.get('tcp_packets')}, HTTP: {row.get('http_packets', 'N/A')}")
            
except Exception as e:
    print(f"Error querying database: {e}")
