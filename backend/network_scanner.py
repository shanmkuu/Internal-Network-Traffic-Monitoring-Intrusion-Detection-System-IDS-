from scapy.all import ARP, Ether, srp, Conf
import socket
import os
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NetworkScanner")

def get_local_ip_and_range():
    """Determines local IP and simple /24 subnet."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        # Assume /24 subnet for simplicity
        ip_parts = local_ip.split('.')
        network_range = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
        return local_ip, network_range
    except Exception as e:
        logger.error(f"Failed to determine local IP: {e}")
        return "127.0.0.1", "127.0.0.1/32"

def resolve_mac_vendor(mac_address):
    """Placeholder for vendor lookup. Parsing OUI is heavy without external DB."""
    # In a real app, you'd lookup an OUI database here.
    return "Unknown"

COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 135, 139, 443, 445, 3306, 3389, 5432, 8000, 8080]

def get_banner(ip, port):
    """Attempts to grab a service banner from the port."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect((ip, port))
        
        # Send a generic trigger for some protocols
        if port in [80, 8080]:
            s.send(b'HEAD / HTTP/1.0\r\n\r\n')
        
        banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
        s.close()
        return banner
    except:
        return ""

def scan_ports(ip):
    """Checks for open ports on the target IP (Quick Connect Scan)."""
    open_ports = []
    try:
        for port in COMMON_PORTS:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5) # Fast timeout
            result = s.connect_ex((ip, port))
            s.close()
            
            if result == 0:
                # Port is open, try to identify service
                try:
                    service_name = socket.getservbyport(port)
                except:
                    service_name = "unknown"
                
                # Grab banner
                banner = get_banner(ip, port)
                if banner:
                    # Truncate clean banner
                    clean_banner = banner.split('\n')[0][:50]
                    service_info = f"{service_name} ({clean_banner})"
                else:
                    service_info = service_name
                
                open_ports.append(f"{port}:{service_info}")
                
    except Exception as e:
        logger.error(f"Port scan failed for {ip}: {e}")
    return open_ports

def scan_network():
    """Performs ARP scan on local subnet."""
    local_ip, target_range = get_local_ip_and_range()
    logger.info(f"Starting ARP scan on {target_range} (Local IP: {local_ip})")
    
    devices = []
    try:
        # Create ARP Request
        arp = ARP(pdst=target_range)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp

        # Send packet
        # timeout=2 is usually enough for local LAN
        # verbose=0 suppresses scapy stdout noise
        result = srp(packet, timeout=2, verbose=0)[0]

        for sent, received in result:
            devices.append({
                "ip": received.psrc,
                "mac": received.hwsrc,
                "vendor": resolve_mac_vendor(received.hwsrc),
                "status": "Online",
                "last_seen": "Just now"
            })
            
        # Ensure local host is included if scapy misses it (it often does)
        # Note: Scapy srp doesn't always capture own loopback/self in ARP scan
        
        logger.info(f"ARP Scan complete. Found {len(devices)} devices.")
        return devices

    except Exception as e:
        logger.error(f"ARP Scan failed: {e}")
        return []

def run_full_scan():
    """Orchestrates a full network scan: ARP + Port Scan."""
    logger.info("Starting FULL Active Network Scan...")
    
    # 1. Host Discovery
    devices = scan_network()
    
    # 2. Port Scanning
    results = []
    for device in devices:
        ip = device['ip']
        logger.info(f"Scanning ports for {ip}...")
        ports = scan_ports(ip)
        
        # Assess Risk
        risk = "Low"
        if 22 in ports or 3389 in ports: risk = "Medium" # SSH/RDP open
        if 23 in ports: risk = "High" # Telnet is insecure
        
        device['open_ports'] = ports
        device['risk_level'] = risk
        results.append(device)
        
    logger.info(f"Full scan complete. Analyzed {len(results)} hosts.")
    return results

if __name__ == "__main__":
    # Test run
    print("Scanning...")
    devs = scan_network()
    for d in devs:
        print(d)
