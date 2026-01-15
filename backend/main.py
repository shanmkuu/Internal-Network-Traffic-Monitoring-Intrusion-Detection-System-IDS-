import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Warning: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in environment variables.")

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = FastAPI(title="IDS Backend API")

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "*" # Allow all for now based on user request for accessibility
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class AlertCreate(BaseModel):
    source_ip: str
    destination_ip: str
    protocol: Optional[str] = None
    alert_type: str
    severity: str
    description: Optional[str] = None

class TrafficStatsCreate(BaseModel):
    total_packets: int
    tcp_packets: int
    udp_packets: int
    icmp_packets: int

class SystemStatusUpdate(BaseModel):
    status: str
    monitored_interface: Optional[str] = None

# Routes

@app.get("/")
def read_root():
    return {"message": "IDS Backend API is running"}

@app.get("/api/alerts")
def get_alerts():
    # Fetch only security alerts (Medium/High) or exclude 'Low' if used for info
    # Or specifically exclude "System *" alert types
    response = supabase.table("alerts").select("*").neq("severity", "Low").order("created_at", desc=True).limit(50).execute()
    return response.data

@app.post("/api/alerts")
def create_alert(alert: AlertCreate):
    data = alert.dict()
    response = supabase.table("alerts").insert(data).execute()
    return response.data

@app.get("/api/stats")
def get_stats():
    # Get the most recent stats entry
    response = supabase.table("traffic_stats").select("*").order("created_at", desc=True).limit(1).execute()
    return response.data

@app.post("/api/stats")
def create_stats(stats: TrafficStatsCreate):
    data = stats.dict()
    response = supabase.table("traffic_stats").insert(data).execute()
    return response.data

@app.get("/api/status")
def get_status():
    response = supabase.table("system_status").select("*").order("updated_at", desc=True).limit(1).execute()
    return response.data

@app.post("/api/status")
def update_status(status: SystemStatusUpdate):
    data = status.dict()
    response = supabase.table("system_status").insert(data).execute()
    return response.data

@app.get("/api/stats/history")
def get_stats_history(limit: int = 20):
    response = supabase.table("traffic_stats").select("*").order("created_at", desc=True).limit(limit).execute()
    # Return reversed data so it flows left to right in charts (oldest first)
    return list(reversed(response.data))

@app.get("/api/analytics/top-sources")
def get_top_sources():
    # Since we can't easily do aggregation query via simple client without rpc,
    # we fetch recent alerts and aggregate in python. 
    # For production this should be a DB view or RPC.
    response = supabase.table("alerts").select("source_ip").order("created_at", desc=True).limit(100).execute()
    
    from collections import Counter
    if not response.data:
        return []
        
    counts = Counter(item['source_ip'] for item in response.data)
    # Return top 5
    return [{"ip": ip, "count": count} for ip, count in counts.most_common(5)]

@app.get("/api/analytics/geo")
def get_geo_distribution():
    # Mocking geo distribution based on IPs (since we don't have a geoip DB installed)
    # In a real app, use GeoIP2 or similar.
    response = supabase.table("alerts").select("source_ip").order("created_at", desc=True).limit(50).execute()
    
    if not response.data:
        return []
    
    # Simple deterministic hash to mock locations for demo purposes
    # This ensures the same IP always maps to the same "country"
    countries = ["USA", "China", "Russia", "Germany", "Brazil", "France", "India"]
    
    from collections import Counter
    
    def get_country(ip):
        hash_val = sum(ord(c) for c in ip)
        return countries[hash_val % len(countries)]
        
    counts = Counter(get_country(item['source_ip']) for item in response.data)
    return [{"country": country, "count": count} for country, count in counts.most_common()]

@app.get("/api/logs")
def get_logs():
    # Fetch system logs (Severity 'Low' or specific types)
    response = supabase.table("alerts").select("*").eq("severity", "Low").order("created_at", desc=True).limit(100).execute()
    return response.data

import threading
import time
from backend.network_scanner import scan_network

# ... existing imports ...

# Global In-Memory Device List
connected_devices = []

def device_scanner_loop():
    """Background thread to scan network periodically."""
    global connected_devices
    logging.info("Device scanner thread started.")
    while True:
        try:
            logging.info("Running network scan...")
            devices = scan_network()
            if devices:
                connected_devices = devices
                logging.info(f"Updated connected devices list: {len(devices)} found.")
        except Exception as e:
            logging.error(f"Device scan failed: {e}")
        
        time.sleep(30) # Scan every 30 seconds

@app.on_event("startup")
def startup_event():
    # Start scanning thread
    display_thread = threading.Thread(target=device_scanner_loop, daemon=True)
    display_thread.start()

@app.get("/api/devices")
def get_devices():
    """Returns the current list of connected devices."""
    return connected_devices

if __name__ == "__main__":
    import uvicorn
    # Bind to 0.0.0.0 to allow external access
    uvicorn.run(app, host="0.0.0.0", port=8000)




