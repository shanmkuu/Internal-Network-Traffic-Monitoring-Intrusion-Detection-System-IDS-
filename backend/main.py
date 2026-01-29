import os
import logging
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load env variables from root
import sys
# Add project root to sys.path so 'backend.modules' imports work from anywhere
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel
from typing import Optional

try:
    from backend.utils.eve_builder import build_eve_alert
except ImportError:
    from utils.eve_builder import build_eve_alert

# Supabase Setup w/ Fallback
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    logging.error("Supabase credentials missing! Checked for SUPABASE_URL, VITE_SUPABASE_URL, etc.")
    logging.error(f"Current Env Keys: {list(os.environ.keys())}")
    # Don't exit, let it fail gracefully or just warn
    # exit(1) is bad for API server
else:
    logging.info("Supabase credentials loaded.")

# Initialize Supabase Client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
except Exception as e:
    logging.error(f"Failed to init Supabase: {e}")
    supabase = None

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
    return [build_eve_alert(alert) for alert in response.data]

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
    return [build_eve_alert(alert) for alert in response.data]

import threading
import time
try:
    from backend.network_scanner import scan_network, run_full_scan, get_local_ip_and_range
    from backend.nmap_scanner import run_nmap_scan_flow
except ImportError:
    from network_scanner import scan_network, run_full_scan, get_local_ip_and_range
    from nmap_scanner import run_nmap_scan_flow

# ... (Existing code) ...

# --- Scan Results Endpoints ---

@app.post("/api/scan/start")
async def start_active_scan(background_tasks: BackgroundTasks):
    """Triggers a full active scan using the new Discovery Orchestrator."""
    def perform_scan_and_save():
        try:
            logging.info("Starting orchestrated active scan...")
            
            # 1. Determine Network Range
            local_ip, cidr = get_local_ip_and_range()
            
            # 2. Run Orchestrator
            from backend.modules.discovery_orchestrator import DiscoveryOrchestrator
            orchestrator = DiscoveryOrchestrator()
            results = orchestrator.run_full_discovery(cidr)

            logging.info(f"Orchestrated scan completed. Processed {len(results)} devices.")
            
            # 3. (Optional) Run legacy logic for compatibility if needed, 
            # but Orchestrator handles DB upsert now.
            
        except Exception as e:
            logging.error(f"Active scan task failed: {e}")

    # Use FastAPI BackgroundTasks
    background_tasks.add_task(perform_scan_and_save)
    return {"status": "Scan started", "message": "The deep network discovery is running in the background."}

@app.get("/api/scan-results")
async def get_scan_results():
    """Retrieves historical scan results."""
    try:
        response = supabase.table("scan_results").select("*").order("created_at", desc=True).limit(50).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ... (Existing device_scanner_loop and other endpoints) ...

# ... existing imports ...

# Global In-Memory Device List (Deprecated in favor of DB, but kept for fallback or cache)
connected_devices = []

def device_scanner_loop():
    """Background thread to scan network periodically (Orchestrated)."""
    global connected_devices
    logging.info("Device scanner thread started.")
    
    # Import Orchestrator here
    try:
        from backend.modules.discovery_orchestrator import DiscoveryOrchestrator
        orchestrator = DiscoveryOrchestrator()
    except Exception as e:
        logging.error(f"Failed to load Orchestrator: {e}")
        return

    while True:
        try:
            logging.info("Running scheduled network discovery...")
            local_ip, cidr = get_local_ip_and_range()
            results = orchestrator.run_full_discovery(cidr)
            
            if results:
                connected_devices = results
                logging.info(f"Scheduled discovery found {len(results)} devices.")
        except Exception as e:
            logging.error(f"Device scan failed: {e}")
        
        # Scan every 5 minutes (300s)
        time.sleep(300) 

@app.on_event("startup")
def startup_event():
    # Start scanning thread
    display_thread = threading.Thread(target=device_scanner_loop, daemon=True)
    display_thread.start()

@app.get("/api/devices")
def get_devices():
    """Returns the current list of devices (Synced from DB for rich data)."""
    try:
        # Prefer DB source for rich data
        response = supabase.table("devices").select("*").order("last_seen", desc=True).execute()
        return response.data
    except Exception as e:
        logging.error(f"Failed to fetch from DB, returning cached: {e}")
        return connected_devices

if __name__ == "__main__":
    import uvicorn
    # Bind to 0.0.0.0 to allow external access
    uvicorn.run(app, host="0.0.0.0", port=8000)




