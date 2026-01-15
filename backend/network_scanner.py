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

def scan_network():
    """Performs ARP scan on local subnet."""
    local_ip, target_range = get_local_ip_and_range()
    logger.info(f"Starting scan on {target_range} (Local IP: {local_ip})")
    
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
        
        logger.info(f"Scan complete. Found {len(devices)} devices.")
        return devices

    except Exception as e:
        logger.error(f"Scan failed: {e}")
        return []

if __name__ == "__main__":
    # Test run
    print("Scanning...")
    devs = scan_network()
    for d in devs:
        print(d)
