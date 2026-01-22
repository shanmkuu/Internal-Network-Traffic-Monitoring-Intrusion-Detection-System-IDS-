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
        Performs port scan on specific IPs with Version Detection, OS Detection, and Vuln Scripts.
        devices: list of dicts from scan_network_segment or native scanner.
        """
        if not self.available:
            raise RuntimeError("Nmap not available")

        if not devices:
            return []

        # Extract IPs
        target_ips = " ".join([d['ip'] for d in devices])
        logger.info(f"Starting Nmap Port & Vuln Scan on {len(devices)} targets...")
        
        try:
            # -A: Aggressive scan (OS detection, version detection, script scanning, traceroute)
            # --script vuln: Run vulnerability detection scripts
            # (Removed --top-ports 100 to scan default top 1000 ports for better coverage)
            nm_args = '-A --script vuln' 
            logger.info(f"Running Aggressive Nmap Scan with arguments: {nm_args}")
            self.nm.scan(hosts=target_ips, arguments=nm_args)
            
            enrichment_results = []
            for device in devices:
                ip = device['ip']
                # Default values
                open_ports_list = []
                os_match = "Unknown"
                vulns_found = []
                risk = "Low"
                tool_status = "Nmap"

                if ip in self.nm.all_hosts():
                    host_data = self.nm[ip]
                    
                    # 1. Open Ports & Services
                    if 'tcp' in host_data:
                        for port, info in host_data['tcp'].items():
                            if info['state'] == 'open':
                                service_info = f"{info.get('name', 'tcp')} {info.get('product', '')} {info.get('version', '')}".strip()
                                open_ports_list.append(f"{port}:{service_info}")
                                
                                # Extract script output (vulnerabilities) for this port
                                if 'script' in info:
                                    for script_name, script_output in info['script'].items():
                                        vulns_found.append({
                                            "type": "port_script",
                                            "port": port,
                                            "script": script_name,
                                            "output": script_output
                                        })

                    # 2. OS Detection
                    if 'osmatch' in host_data and host_data['osmatch']:
                        # Take the best match
                        best = host_data['osmatch'][0]
                        os_match = f"{best['name']} ({best['accuracy']}%)"

                    # 3. Host Script info (e.g. smb-vuln-*)
                    if 'hostscript' in host_data:
                        for script in host_data['hostscript']:
                             vulns_found.append({
                                 "type": "host_script",
                                 "port": None,
                                 "script": script['id'],
                                 "output": script['output']
                             })

                    # 4. Risk Assessment
                    if vulns_found:
                        risk = "High"
                    elif any("22:" in p or "3389:" in p or "23:" in p for p in open_ports_list):
                        risk = "Medium"
                    
                else:
                    tool_status = "Nmap (Failed/Offline)"
                
                # Update device dict
                device['open_ports'] = open_ports_list
                device['os_details'] = os_match
                device['vulnerabilities'] = vulns_found
                device['risk_level'] = risk
                device['scan_tool'] = tool_status
                    
                enrichment_results.append(device)
                
            return enrichment_results

        except Exception as e:
            logger.error(f"Nmap Port Scan failed: {e}")
            logger.exception("Traceback:")
            return devices # Return original without enrichment on error

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
