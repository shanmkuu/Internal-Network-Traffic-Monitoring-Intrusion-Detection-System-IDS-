import socket
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

def resolve_hostname(ip):
    """
    Performs a reverse DNS lookup for a single IP.
    """
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return (ip, hostname)
    except socket.herror:
        return (ip, None)
    except Exception:
        return (ip, None)

def perform_dns_resolution(ip_list, concurrency=20):
    """
    Resolves hostnames for a list of IPs.
    Returns text dict {ip: hostname}.
    """
    logger.info(f"Resolving hostnames for {len(ip_list)} IPs...")
    results = {}
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = executor.map(resolve_hostname, ip_list)
        
        for ip, hostname in futures:
            if hostname:
                results[ip] = hostname
                
    logger.info(f"DNS resolution complete. Resolved {len(results)} hostnames.")
    return results
