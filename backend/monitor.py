import logging
from scapy.all import sniff, IP, TCP, UDP, ICMP, Conf
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import time
from collections import defaultdict
import threading
import sys

# Load environment variables
# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Supabase Setup
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    logging.error("Supabase credentials missing! Checked for SUPABASE_URL, VITE_SUPABASE_URL, etc.")
    logging.error(f"Current Env Keys: {list(os.environ.keys())}")
    exit(1)
else:
    logging.info(f"Supabase URL: {SUPABASE_URL[:10]}...")
    logging.info(f"Supabase Key: {SUPABASE_SERVICE_ROLE_KEY[:5]}...*****...{SUPABASE_SERVICE_ROLE_KEY[-5:]}")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def log_system_event(event_type, message):
    """Logs a system event to the alerts table with 'Info' severity."""
    try:
        data = {
            "source_ip": "localhost",
            "destination_ip": "localhost",
            "protocol": "SYSTEM",
            "alert_type": event_type,
            "severity": "Low", # Using Low as Info
            "description": message
        }
        supabase.table("alerts").insert(data).execute()
        logging.info(f"SYSTEM LOG: {message}")
    except Exception as e:
        logging.error(f"Failed to log system event: {e}")


# Stats Container
class TrafficStats:
    def __init__(self):
        self.total_packets = 0
        self.tcp_packets = 0
        self.udp_packets = 0
        self.icmp_packets = 0
        self.http_packets = 0
        self.https_packets = 0
        self.dns_packets = 0
        self.lock = threading.Lock()

    def update(self, packet):
        with self.lock:
            self.total_packets += 1
            if TCP in packet:
                self.tcp_packets += 1
                if packet[TCP].dport == 80 or packet[TCP].sport == 80:
                    self.http_packets += 1
                elif packet[TCP].dport == 443 or packet[TCP].sport == 443:
                    self.https_packets += 1
            elif UDP in packet:
                self.udp_packets += 1
                if packet[UDP].dport == 53 or packet[UDP].sport == 53:
                    self.dns_packets += 1
            elif ICMP in packet:
                self.icmp_packets += 1

    def reset(self):
        with self.lock:
            self.total_packets = 0
            self.tcp_packets = 0
            self.udp_packets = 0
            self.icmp_packets = 0
            self.http_packets = 0
            self.https_packets = 0
            self.dns_packets = 0

stats = TrafficStats()

# Detection Logic State
syn_packet_count = defaultdict(int)
packet_rate_tracker = defaultdict(int)
SCAN_THRESHOLD = 20 # Number of SYN packets to trigger scan alert
RATE_LIMIT_THRESHOLD = 100 # Packets per second to trigger Rate alert

def log_alert(source_ip, dest_ip, protocol, alert_type, severity, description):
    """Inserts an alert into Supabase."""
    try:
        data = {
            "source_ip": source_ip,
            "destination_ip": dest_ip,
            "protocol": protocol,
            "alert_type": alert_type,
            "severity": severity,
            "description": description
        }
        supabase.table("alerts").insert(data).execute()
        logging.warning(f"ALERT SENT: {alert_type} from {source_ip}")
    except Exception as e:
        logging.error(f"Failed to log alert: {e}")

def process_packet(packet):
    """Callback function for every captured packet."""
    if IP in packet:
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        proto = packet[IP].proto
        
        # Update Stats
        stats.update(packet)

        # 1. Port Scan Detection (SYN Scan)
        if TCP in packet and packet[TCP].flags == 'S':
            syn_packet_count[src_ip] += 1
            if syn_packet_count[src_ip] > SCAN_THRESHOLD:
                log_alert(src_ip, dst_ip, "TCP", "Port Scan Detected", "High", f"Excessive SYN packets detected from {src_ip}")
                syn_packet_count[src_ip] = 0 # Reset after alert to avoid spamming

        # 2. High Traffic Volume Check
        packet_rate_tracker[src_ip] += 1
        if packet_rate_tracker[src_ip] > RATE_LIMIT_THRESHOLD:
             log_alert(src_ip, dst_ip, "IP", "High Traffic Volume", "Medium", f"High packet rate detected from {src_ip}")
             packet_rate_tracker[src_ip] = 0

def report_stats():
    """Periodically pushes stats to Supabase."""
    print("Stats reporting thread started.")
    sys.stdout.flush()
    while True:
        time.sleep(10) # Report every 10 seconds
        try:
            with stats.lock:
                # Prepare data with extended stats
                data = {
                    "total_packets": stats.total_packets,
                    "tcp_packets": stats.tcp_packets,
                    "udp_packets": stats.udp_packets,
                    "icmp_packets": stats.icmp_packets,
                    "http_packets": stats.http_packets,
                    "https_packets": stats.https_packets,
                    "dns_packets": stats.dns_packets
                }
                stats.reset() 

            print(f"Attempting to report stats: {data['total_packets']} packets captured.")
            sys.stdout.flush()

            if data["total_packets"] >= 0: # Always report even if 0 to show flatline
                try:
                    # Try to insert with extended stats
                    supabase.table("traffic_stats").insert(data).execute()
                    print(f"Stats reported successfully (Extended).")
                    sys.stdout.flush()
                    logging.info(f"Stats reported: {data}")
                except Exception as e:
                    print(f"Extended stats insert failed: {e}")
                    sys.stdout.flush()
                    # Fallback to basic stats if columns missing
                    logging.warning(f"Failed to report extended stats (likely missing columns), retrying with basic stats: {e}")
                    basic_data = {
                        "total_packets": data["total_packets"],
                        "tcp_packets": data["tcp_packets"],
                        "udp_packets": data["udp_packets"],
                        "icmp_packets": data["icmp_packets"]
                    }
                    try:
                        supabase.table("traffic_stats").insert(basic_data).execute()
                        print(f"Stats reported successfully (Basic Fallback).")
                        sys.stdout.flush()
                        logging.info(f"Basic stats reported: {basic_data}")
                    except Exception as e2:
                         print(f"CRITICAL: Basic stats insert failed too: {e2}")
                         sys.stdout.flush()

        except Exception as e:
            print(f"CRITICAL: Report stats loop error: {e}")
            sys.stdout.flush()
            logging.error(f"Failed to report stats: {e}")

def resolve_interface():
    """Tries to find the Wi-Fi interface automatically."""
    try:
        if os.name == 'nt':
            from scapy.arch.windows import get_windows_if_list
            interfaces = get_windows_if_list()
            
            # 1. Prioritize real Wi-Fi adapters (exclude Virtual)
            for iface in interfaces:
                name = iface['name']
                desc = iface['description']
                if ("Wi-Fi" in name or "Wireless" in desc or "Wi-Fi" in desc) and "Virtual" not in desc:
                    print(f"Automatically selected interface (Real): {name} ({desc})")
                    return iface # Return full dict, sniffing usually takes name or dict
                    
            # 2. Fallback to any Wi-Fi match
            for iface in interfaces:
                # Look for common Wi-Fi names
                if 'Wi-Fi' in iface['name'] or 'Wireless' in iface['name'] or 'Wi-Fi' in iface['description']:
                    print(f"Automatically selected interface (Fallback): {iface['name']} ({iface['description']})")
                    return iface
                    
    except Exception as e:
        print(f"Interface auto-discovery failed: {e}")
    
    return conf.iface
    
    return None # Fallback to default

def main():
    print("Starting IDS Monitor...")
    log_system_event("System Start", "IDS Monitor started")
    
    iface = resolve_interface()
    print(f"Monitor utilizing interface: {iface}")
    
    # Update System Status
    try:
        # Convert iface to string for DB
        iface_str = iface['name'] if isinstance(iface, dict) else str(iface)
        supabase.table("system_status").insert({
            "status": "Running",
            "monitored_interface": iface_str
        }).execute()
    except Exception as e:
        print(f"Failed to update status: {e}")
        # If 401, logic should probably continue sniffing but warn user
        if "401" in str(e):
             print("CRITICAL: Supabase rejected the connection (401 Unauthorized).")
             print("   -> Your Anon/Service Key is invalid or expired.")
             print("   -> Check your .env file in root.")

    # Start Stats Reporter Thread
    stats_thread = threading.Thread(target=report_stats)
    stats_thread.daemon = True
    stats_thread.start()

    print("Stats reporting thread started.")

    # Start Sniffing
    try:
        # Resolve just the name for Scapy if it's a dict
        scapy_iface = iface['name'] if isinstance(iface, dict) and 'name' in iface else iface
        
        # Determine strictness of sniffing
        # store=0 helps memory. prn=process_packet is the callback.
        sniff(iface=scapy_iface, prn=process_packet, store=0)
    except Exception as e:
        print(f"Error sniffing: {e}")
        print("Note: On Windows, make sure Npcap is installed. On Linux, run as root.")
        if "name" in str(e):
             print("debug: iface object was:", iface)

    # Start Stats Thread
    stats_thread = threading.Thread(target=report_stats, daemon=True)
    stats_thread.start()

    # Start Sniffer
    try:
        # calling sniff with count=0 runs indefinitely
        # On Windows, defining iface often fixes "no packets captured" issues if default is Loopback
        if iface:
            sniff(iface=iface, prn=process_packet, store=0)
        else:
            print("Using default interface...")
            sniff(prn=process_packet, store=0)
    except KeyboardInterrupt:
        print("Stopping IDS Monitor...")
        log_system_event("System Stop", "IDS Monitor stopped manually")
    except Exception as e:
        log_system_event("System Error", f"IDS Monitor crashed: {e}")
        print(f"Error: {e}")
        print("Note: On Windows, make sure Npcap is installed. On Linux, run as root.")

if __name__ == "__main__":
    main()
