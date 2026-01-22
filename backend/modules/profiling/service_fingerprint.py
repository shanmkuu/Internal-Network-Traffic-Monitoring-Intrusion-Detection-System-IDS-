import socket
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Common banner ports
BANNER_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    445: "SMB", # Native OS detection often possible
    3389: "RDP"
}

def grab_banner(ip, port, timeout=1.0):
    """
    Connects to a port and grabs the banner.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        
        # Trigger for HTTP
        if port in [80, 8080]:
            s.send(b'HEAD / HTTP/1.0\r\n\r\n')
        
        banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
        s.close()
        return banner
    except Exception:
        return None

def fingerprint_service(ip, port):
    """
    Returns (port, service_name, banner_info)
    """
    banner = grab_banner(ip, port)
    service_name = BANNER_PORTS.get(port, "Unknown")
    
    # Heuristics based on banner
    info = ""
    if banner:
        info = banner.split('\n')[0][:50] # First line
        
        if "SSH" in banner:
            service_name = "SSH"
        elif "Server:" in banner: # HTTP Server header
            # Extract server header
            for line in banner.split('\r\n'):
                if line.startswith("Server:"):
                    info = line.replace("Server:", "").strip()
                    break
                    
    return (port, service_name, info)

def profile_services(ip, scan_ports=None):
    """
     Checks a small set of ports to fingerprint the OS/Service.
     Returns a description string like "Linux (SSH)" or "Windows (SMB)".
    """
    if scan_ports is None:
        scan_ports = [22, 80, 445, 3389]
        
    detected = []
    
    # Check 445 (SMB) for Windows
    if 445 in scan_ports:
        # Simple check if open
        if grab_banner(ip, 445, timeout=0.5) is not None: # SMB doesn't always send banner on connect, but getting no error means open
             # Start with "Windows?" but usually we need nmap for true OS detection via SMB
             # For now, just note the port.
             pass

    # We will use the results from the main port scanner usually.
    # This module is for specific targeting.
    
    # TODO: Integrate python-nmap for OS fingerprinting
    return "Unknown"
