import logging
from scapy.all import sniff, IP, TCP, UDP, ICMP, Conf, conf
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import time
from collections import defaultdict
import threading
import sys
from scapy.all import Raw

try:
    from utils.rule_parser import RuleParser
    from utils.config_loader import config_loader
    from modules.flow.flow_manager import flow_manager
    from modules.detection.threshold_manager import threshold_manager
    from modules.parsers.http_parser import http_parser
    from modules.parsers.dns_parser import dns_parser
except ImportError:
    from backend.utils.rule_parser import RuleParser
    from backend.utils.config_loader import config_loader
    from backend.modules.flow.flow_manager import flow_manager
    from backend.modules.detection.threshold_manager import threshold_manager
    from backend.modules.parsers.http_parser import http_parser
    from backend.modules.parsers.dns_parser import dns_parser

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
        self.dhcp_packets = 0
        self.lock = threading.Lock()

    def update(self, packet):
        with self.lock:
            self.total_packets += 1
            if self.total_packets % 50 == 0:
                logging.info(f"Packet Debug: {packet.summary()} | Layers: {[x.name for x in packet.layers()]}")

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
                elif packet[UDP].dport in [67, 68] or packet[UDP].sport in [67, 68]:
                    self.dhcp_packets += 1
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
            self.dhcp_packets = 0

stats = TrafficStats()

# Detection Logic State
syn_packet_count = defaultdict(int)
packet_rate_tracker = defaultdict(int)
SCAN_THRESHOLD = 20 # Number of SYN packets to trigger scan alert
RATE_LIMIT_THRESHOLD = 100 # Packets per second to trigger Rate alert

# Initialize Rule Engine & Config
rule_parser = RuleParser()
RULES_DIR = config_loader.get("default-rule-path", "./rules")
RULE_FILES = config_loader.get("rule-files", ["local.rules"])

LOADED_RULES = []
base_dir = os.path.dirname(os.path.abspath(__file__))
for rf in RULE_FILES:
    r_path = os.path.join(base_dir, RULES_DIR, rf)
    if os.path.exists(r_path):
        LOADED_RULES.extend(rule_parser.parse_file(r_path))
    else:
        logging.warning(f"Rule file not found: {r_path}")

def check_rule_match(packet, rule):
    """Checks if a packet matches a given rule."""
    # 1. Check Protocol
    proto_map = {TCP: "tcp", UDP: "udp", ICMP: "icmp"}
    p_layer = None
    packet_proto = "ip"
    
    if TCP in packet:
        p_layer = packet[TCP]
        packet_proto = "tcp"
    elif UDP in packet:
        p_layer = packet[UDP]
        packet_proto = "udp"
    elif ICMP in packet:
        packet_proto = "icmp"
        
    if rule['protocol'] != 'any' and rule['protocol'].lower() != packet_proto:
        return False

    # 2. Check IPs (Simplified 'any' support)
    if IP in packet:
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        
        if rule['src_ip'] != 'any' and rule['src_ip'] != src_ip:
            return False
        if rule['dest_ip'] != 'any' and rule['dest_ip'] != dst_ip:
            return False

    # 3. Check Ports (TCP/UDP only)
    if p_layer:
        src_port = str(p_layer.sport)
        dst_port = str(p_layer.dport)
        
        if rule['src_port'] != 'any' and rule['src_port'] != src_port:
            return False
        if rule['dest_port'] != 'any' and rule['dest_port'] != dst_port:
            return False

    # 4. Check Flow State
    if 'flow' in rule['options']:
        # Format: flow:established,to_server
        flow_opts = rule['options']['flow'].split(',')
        
        # Get current flow state for this packet
        # Note: Scapy packet might not carry flow state directly, needs lookup
        # In a real engine, flow is passed in. Here we rely on flow_manager cache
        # accessed via global or lookup. 
        # Since process_packet calls update_flow first, we can get state.
        
        flow_id = flow_manager.get_flow_id(packet)
        flow_state = flow_manager.flows.get(flow_id, {})
        current_state = flow_state.get('state', 'new')
        
        if 'established' in flow_opts and current_state != 'established':
            return False
        # (Add more flow checks like to_server/to_client here)

    # 5. Check Content (Payload)
    if 'content' in rule['options']:
        content_sig = rule['options']['content']
        if Raw in packet:
            payload = str(packet[Raw].load)
            if content_sig not in payload:
                return False
        else:
            # If content required but no payload, fail (unless reversed)
            return False

    # 6. Check HTTP Options
    # e.g. http.method, http.uri
    if 'http.method' in rule['options']:
        # This requires the packet to have been parsed as HTTP
        # In this simple implementation, check_rule_match needs the parsed metadata.
        # We'll attach it to the packet object dynamically for now or pass it in.
        # Hack: access attached metadata
        http_meta = getattr(packet, 'http_meta', None)
        if not http_meta:
            return False
        if rule['options']['http.method'] != http_meta['method']:
            return False
            
    if 'http.uri' in rule['options']:
        http_meta = getattr(packet, 'http_meta', None)
        if not http_meta:
            return False
        if rule['options']['http.uri'] not in http_meta['uri']:
             return False

    return True

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
        
        # Update Flow State
        flow_manager.update_flow(packet)
        
        # App Layer Parsings
        http_meta = http_parser.parse(packet)
        if http_meta:
            packet.http_meta = http_meta # Attach for rule engine
            logging.info(f"HTTP DETECTED: {http_meta['method']} {http_meta['uri']}")

        dns_meta = dns_parser.parse(packet)
        if dns_meta:
            packet.dns_meta = dns_meta
            logging.info(f"DNS DETECTED: {dns_meta['type']} {dns_meta['qname']}")

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

        # 3. Rule Engine Check
        for rule in LOADED_RULES:
            if check_rule_match(packet, rule):
                # Check Threshold before alerting
                if not threshold_manager.check_threshold(rule, src_ip, dst_ip):
                    continue

                # Construct description
                msg = rule['options'].get('msg', 'Suspicious Activity Detected')
                
                # Check for classification
                classtype = rule['options'].get('classtype')
                priority_int = 3 # Default Low
                
                if classtype:
                    priority_int, class_desc = config_loader.get_classification(classtype)
                
                # Map priority int to severity string for DB (legacy support)
                sev_map = {1: "High", 2: "Medium", 3: "Low", 4: "Low"}
                severity = sev_map.get(priority_int, "Low")
                
                # Deduplicate based on recent logs? For now, just log.
                # In prod, we'd throttle specific SIDs.
                log_alert(src_ip, dst_ip, rule['protocol'].upper(), msg, severity, f"Rule Match: {msg} (SID: {rule['options'].get('sid')})")
                break # Stop after first match per packet to prevent flood

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
                    "dns_packets": stats.dns_packets,
                    "dhcp_packets": stats.dhcp_packets
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
                    with open("monitor_error.log", "a") as f:
                        f.write(f"Extended stats error: {e}\n")
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
        print(f"Starting Scapy Sniffer on {scapy_iface}...")
        
        # Determine strictness of sniffing
        # store=0 helps memory. prn=process_packet is the callback.
        sniff(iface=scapy_iface, prn=process_packet, store=0)
    except KeyboardInterrupt:
        print("Stopping IDS Monitor...")
        log_system_event("System Stop", "IDS Monitor stopped manually")
    except Exception as e:
        log_system_event("System Error", f"IDS Monitor crashed: {e}")
        print(f"Error sniffing: {e}")
        print("Note: On Windows, make sure Npcap is installed. On Linux, run as root.")
        if "name" in str(e):
             print("debug: iface object was:", iface)


if __name__ == "__main__":
    main()
