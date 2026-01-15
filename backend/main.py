import os
import logging
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load env variables from root
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel
from typing import Optional

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
    """Triggers a full active scan (Nmap Priority -> Native Fallback)."""
    def perform_scan_and_save():
        results = []
        tool_used = "Native"
        
        try:
            logging.info("Starting active scan task...")
            
            # 1. Determine Network Range
            local_ip, cidr = get_local_ip_and_range()
            
            # 2. Try Nmap Scan
            try:
                logging.info(f"Attempting Nmap Scan on {cidr}...")
                results = run_nmap_scan_flow(cidr)
                tool_used = "Nmap"
                logging.info("Nmap scan successful.")
            except ImportError:
                logging.warning("Nmap not available. Falling back to Native Scanner.")
                results = run_full_scan()
                tool_used = "Native"
            except Exception as e:
                logging.error(f"Nmap scan error: {e}. Falling back to Native.")
                results = run_full_scan()
                tool_used = "Native (Fallback)"

            # 3. Save to Database
            for device in results:
                # Update connected_devices (optional, keeping it simple for now)
                
                # Insert into scan_results
                scan_data = {
                    "ip_address": device['ip'],
                    "open_ports": ",".join(map(str, device.get('open_ports', []))),
                    "risk_level": device.get('risk_level', 'Low'),
                    "scan_type": "Full",
                    "scan_tool": device.get('scan_tool', tool_used),
                    "hostname": device.get('vendor', 'Unknown')
                }
                supabase.table("scan_results").insert(scan_data).execute()
                
            logging.info(f"Active scan task completed using {tool_used}.")
        except Exception as e:
            logging.error(f"Active scan task failed: {e}")

    # Use FastAPI BackgroundTasks
    background_tasks.add_task(perform_scan_and_save)
    return {"status": "Scan started", "message": "The network scan is running in the background."}

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




