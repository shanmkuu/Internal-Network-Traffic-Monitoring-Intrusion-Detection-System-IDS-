import nmap
import logging
import os
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NmapScanner")

class NmapScanner:
    def __init__(self):
        # Check if nmap is in PATH
        self.nmap_path = shutil.which("nmap")
        if not self.nmap_path:
            logger.warning("Nmap binary not found in PATH. Nmap features will be disabled.")
            self.available = False
        else:
            logger.info(f"Nmap found at: {self.nmap_path}")
            self.available = True
            self.nm = nmap.PortScanner()

    def scan_network_segment(self, cidr):
        """
        Performs a ping scan (-sn) to discover live hosts.
        Returns a list of dicts: {'ip':Str, 'mac':Str, 'vendor':Str, 'status':'Online'}
        """
        if not self.available:
            raise RuntimeError("Nmap not available")

        logger.info(f"Starting Nmap Host Discovery on {cidr}...")
        try:
            # -sn: Ping Scan - disable port scan
            # -PE: ICMP Echo
            self.nm.scan(hosts=cidr, arguments='-sn -PE')
            
            hosts = []
            for host in self.nm.all_hosts():
                if self.nm[host].state() == 'up':
                    mac = self.nm[host]['addresses'].get('mac', 'Unknown')
                    vendor = self.nm[host]['vendor'].get(mac, 'Unknown')
                    hosts.append({
                        "ip": host,
                        "mac": mac,
                        "vendor": vendor,
                        "status": "Online",
                        "last_seen": "now()"
                    })
            
            logger.info(f"Nmap discovered {len(hosts)} hosts.")
            return hosts

        except Exception as e:
            logger.error(f"Nmap Host Discovery failed: {e}")
            return []

    def scan_specific_targets(self, devices):
        """
        Performs port scan on specific IPs.
        devices: list of dicts from scan_network_segment or native scanner.
        """
        if not self.available:
            raise RuntimeError("Nmap not available")

        if not devices:
            return []

        # Extract IPs
        target_ips = " ".join([d['ip'] for d in devices])
        logger.info(f"Starting Nmap Port Scan on {len(devices)} targets...")
        
        try:
            # -sT: Connect Scan (unprivileged)
            # --top-ports 100: Fast scan of common ports
            self.nm.scan(hosts=target_ips, arguments='-sT --top-ports 100')
            
            enrichment_results = []
            for device in devices:
                ip = device['ip']
                if ip in self.nm.all_hosts():
                    # Get open ports
                    open_ports = []
                    if 'tcp' in self.nm[ip]:
                        for port, info in self.nm[ip]['tcp'].items():
                            if info['state'] == 'open':
                                open_ports.append(port)
                    
                    # Risk Assessment
                    risk = "Low"
                    if 22 in open_ports or 3389 in open_ports: risk = "Medium"
                    if 23 in open_ports: risk = "High"
                    
                    device['open_ports'] = open_ports
                    device['risk_level'] = risk
                    device['scan_tool'] = "Nmap"
                else:
                    # Nmap might have missed it or it went offline
                    device['open_ports'] = []
                    device['risk_level'] = "Low"
                    device['scan_tool'] = "Nmap (Failed)"
                    
                enrichment_results.append(device)
                
            return enrichment_results

        except Exception as e:
            logger.error(f"Nmap Port Scan failed: {e}")
            return devices # Return original without ports

# Global Instance
nmap_scanner_instance = NmapScanner()

def run_nmap_scan_flow(cidr):
    """
    Orchestrates the full Nmap scan workflow.
    """
    scanner = nmap_scanner_instance
    if notVNmapScanner.available:
        scanner = NmapScanner() # Try re-init 
        
    if not scanner.available:
        raise ImportError("Nmap binary missing")

    # 1. Host Discovery
    hosts = scanner.scan_network_segment(cidr)
    
    # 2. Port Scan
    results = scanner.scan_specific_targets(hosts)
    
    return results
