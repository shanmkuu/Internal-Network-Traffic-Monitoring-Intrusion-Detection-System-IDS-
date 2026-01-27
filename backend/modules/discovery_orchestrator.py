import logging
import threading
from backend.modules.discovery.arp import perform_arp_scan
from backend.modules.discovery.icmp import perform_icmp_scan
from backend.modules.discovery.dns_resolver import perform_dns_resolution
from backend.modules.profiling.mac_vendor import get_mac_vendor, update_mac_db
from backend.modules.profiling.service_fingerprint import profile_services
from backend.modules.risk.risk_engine import RiskEngine
from backend.modules.db.db_manager import DBManager
from backend.network_scanner import scan_ports # Reuse existing port scanner for now

logger = logging.getLogger(__name__)

class DiscoveryOrchestrator:
    def __init__(self):
        self.risk_engine = RiskEngine()
        self.db_manager = DBManager()
        # Ensure MAC DB is fresh-ish
        # update_mac_db() # Blocking, maybe skip for speed in dev

    def run_full_discovery(self, target_network):
        logger.info(f"Orchestrator: Starting full discovery on {target_network}")
        
        # 1. ARP Scan (Layer 2)
        arp_devices = perform_arp_scan(target_network)
        # arp_devices is list of {ip, mac}
        
        # 2. ICMP Sweep (Layer 3) - Find what ARP missed (or cross-verify)
        alive_ips = perform_icmp_scan(target_network)
        
        # Merge results
        discovered_hosts = {} # Key: IP
        
        for dev in arp_devices:
            discovered_hosts[dev['ip']] = {
                "ip": dev['ip'],
                "mac": dev['mac'],
                "method": "ARP"
            }
            
        for ip in alive_ips:
            if ip not in discovered_hosts:
                discovered_hosts[ip] = {
                    "ip": ip,
                    "mac": None, # Missing MAC if only ICMP responded (e.g. routed)
                    "method": "ICMP"
                }

        logger.info(f"Merged discovery: {len(discovered_hosts)} unique hosts.")
        
        # 3. DNS Resolution
        ip_list = list(discovered_hosts.keys())
        dns_map = perform_dns_resolution(ip_list)
        
        results = []
        
        # 4. Deep Profiling Loop
        for ip, host_data in discovered_hosts.items():
            logger.info(f"Profiling {ip}...")
            
            # Enrich with DNS
            host_data['hostname'] = dns_map.get(ip)
            
            # Enrich with Vendor
            if host_data['mac']:
                host_data['vendor'] = get_mac_vendor(host_data['mac'])
            else:
                host_data['vendor'] = "Unknown"

            # Enrich with Services (Active)
            # Using existing simple port scanner for now + fingerprinting
            open_ports_info = scan_ports(ip) # Returns list of strings "80:http..."
            
            # Parse open ports to numbers for risk engine
            open_ports = []
            protocols = []
            
            for info in open_ports_info:
                try:
                    port = int(info.split(':')[0])
                    open_ports.append(port)
                    # Simple protocol inference
                    if port == 80: protocols.append('http')
                    if port == 443: protocols.append('https')
                    if port == 22: protocols.append('ssh')
                    if port == 23: protocols.append('telnet')
                    if port == 445: protocols.append('smb')
                except:
                    pass
            
            host_data['open_ports'] = open_ports
            host_data['protocols_detected'] = protocols
            
            # OS Fingerprint (Basic)
            host_data['os_family'] = "Unknown" 
            if 445 in open_ports: host_data['os_family'] = "Windows"
            if 22 in open_ports and 445 not in open_ports: host_data['os_family'] = "Linux"
            
            # Risk Analysis
            risk_assessment = self.risk_engine.calculate_risk(host_data)
            host_data['risk_level'] = risk_assessment['score'] # Use score or level?
            # DB Schema uses text Level
            host_data['risk_level'] = risk_assessment['level']
            
            # 4b. Backfill Hostname from History (Preserve existing names)
            if host_data.get('mac'):
                 logger.info(f"Checking DB for MAC: {host_data['mac']}")
                 existing_dev = self.db_manager.get_device_by_mac(host_data['mac'])
                 if existing_dev:
                     logger.info(f"DB Hit for {host_data['mac']}: {existing_dev.get('hostname')} / {existing_dev.get('custom_name')}")
                     # If we didn't resolve a hostname this time, but we knew one before, keep it.
                     if not host_data.get('hostname'):
                         known_name = existing_dev.get('hostname') or existing_dev.get('custom_name')
                         if known_name:
                             host_data['hostname'] = known_name
                             logger.info(f"Backfilled hostname for {host_data['ip']} from DB: {known_name}")
                     
                     # Also preserve custom_name if we have it in memory for the scan report
                     if existing_dev.get('custom_name'):
                         host_data['custom_name'] = existing_dev.get('custom_name')
            else:
                 logger.warning(f"No MAC for IP {host_data['ip']} - cannot backfill hostname.")

            # 5. Persist to DB
            if host_data['mac']: # Only persist if we have a MAC (Key)
                db_device = self.db_manager.upsert_device(host_data)
                if db_device:
                    # Log discovery
                     # Extract ID from list result
                    try:
                         dev_id = db_device[0]['id']
                         self.db_manager.log_discovery(dev_id, host_data['method'])
                    except:
                        pass
            
            # 6. Save to Scan History (For Reports UI)
            # This allows the "Active Scan Reports" table to show this scan immediately.
            # We explicitly include hostname here.
            self.db_manager.save_scan_result(host_data)
            
            results.append(host_data)
            
        return results
