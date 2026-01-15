import sys
import os
import time
import socket
import logging
from scapy.all import sniff, Conf, ARP, Ether, srp
from supabase import create_client

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def check_dependencies():
    print("\n--- 1. Dependency Check ---")
    try:
        import scapy
        print("Scapy: OK")
    except ImportError:
        print("Scapy: MISSING")
    
    try:
        import supabase
        print("Supabase: OK")
    except ImportError:
        print("Supabase: MISSING")

def check_interface():
    print("\n--- 2. Interface Detection ---")
    from scapy.arch.windows import get_windows_if_list
    interfaces = get_windows_if_list()
    print(f"Found {len(interfaces)} interfaces.")
    
    # Simple logic similar to monitor.py
    wifi_iface = None
    for iface in interfaces:
        # print(f"  - {iface['name']} ({iface['description']})")
        if "Wi-Fi" in iface['name'] or "Wireless" in iface['description']:
            wifi_iface = iface
            print(f"  [MATCH] Detected likely Wi-Fi: {iface['name']} - {iface['description']}")
    
    if not wifi_iface:
        print("  [WARN] No explicit 'Wi-Fi' interface found. Monitor defaults to 'conf.iface'.")
    return wifi_iface

def check_sniffing():
    print("\n--- 3. Sniffing Test (Npcap Check) ---")
    print("Attempting to capture 5 packets (timeout 5s)...")
    try:
        packets = sniff(count=5, timeout=5)
        print(f"Captured {len(packets)} packets.")
        if len(packets) == 0:
            print("  [FAIL] No packets captured. Verifiy Npcap is installed in 'WinPcap API-compatible Mode'.")
        else:
            print("  [PASS] Sniffing works.")
            print(f"  Sample: {packets[0].summary()}")
    except Exception as e:
        print(f"  [CRITICAL] Sniffing failed: {e}")

def check_arp_scan():
    print("\n--- 4. ARP Scan Test ---")
    try:
        # Determine local range
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        ip_parts = local_ip.split('.')
        target = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.1/24" # Scan gateway mostly
        print(f"Scanning target: {target} (Local IP: {local_ip})")
        
        arp = ARP(pdst=target)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp
        result = srp(packet, timeout=2, verbose=0)[0]
        
        print(f"Found {len(result)} devices response.")
        if len(result) > 0:
             print("  [PASS] ARP Scan works.")
        else:
             print("  [WARN] No devices found. Check firewall or Npcap.")
             
    except Exception as e:
        print(f"  [FAIL] ARP Scan Error: {e}")

if __name__ == "__main__":
    check_dependencies()
    check_interface()
    check_sniffing()
    check_arp_scan()
