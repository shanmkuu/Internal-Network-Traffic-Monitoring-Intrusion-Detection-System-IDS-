import platform
import subprocess
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import socket

logger = logging.getLogger(__name__)

def ping_host(ip):
    """
    Pings a single host. Returns (ip, True) if alive, else (ip, False).
    """
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
    # Windows timeout is milliseconds, Linux is seconds usually. 
    # Using 1000ms for windows.
    timeout_val = '1000'
    
    command = ['ping', param, '1', timeout_param, timeout_val, ip]
    
    try:
        # Use subprocess to hide output and check return code
        result = subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return (ip, result == 0)
    except Exception as e:
        logger.debug(f"Ping failed for {ip}: {e}")
        return (ip, False)

def perform_icmp_scan(target_network, concurrency=50):
    """
    Performs a ping sweep on the target /24 network.
    Assumes target_network string like "192.168.1.0/24".
    """
    # Parse network to get list of IPs (simple /24 logic)
    # For robust parsing, we'd use ipaddress module
    import ipaddress
    
    alive_hosts = []
    try:
        net = ipaddress.ip_network(target_network, strict=False)
        # Exclude network and broadcast
        hosts = list(net.hosts())
        
        logger.info(f"Starting ICMP sweep on {target_network} ({len(hosts)} hosts) with {concurrency} threads")
        
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            # Map IPs to existing string format
            results = executor.map(ping_host, [str(ip) for ip in hosts])
            
            for ip, is_alive in results:
                if is_alive:
                    alive_hosts.append(ip)
                    
        logger.info(f"ICMP sweep complete. Found {len(alive_hosts)} alive hosts.")
        return alive_hosts
        
    except Exception as e:
        logger.error(f"ICMP Scan failed: {e}")
        return []
