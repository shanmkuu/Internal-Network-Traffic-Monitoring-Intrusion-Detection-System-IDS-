import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from scapy.all import IP, UDP, NBNSQueryRequest, sr1, DNS, DNSQR, DNSRR
import struct

logger = logging.getLogger(__name__)

def resolve_netbios_name(ip, timeout=1):
    """
    Attempts to resolve NetBIOS name via port 137.
    Uses Scapy to send a NBNS Node Status Request.
    """
    try:
        # Construct NBNS Query for "*" (Node Status Request)
        # 0x20 encodes to ' ' (space) * 32. 
        # Actually standard wildcard for NBNS stats is CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        # But simpler is just asking for the name. 
        # Let's try a standard query for the machine name using a raw socket if scapy is heavy,
        # but scapy is easier to read.
        
        # Scapy method: Use NBNSQueryRequest
        # Note: 'CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' is the encoded form of '*' used for status.
        query = NBNSQueryRequest(QUESTION_NAME='*'*15, QUESTION_TYPE='NBSTAT')
        pkt = IP(dst=ip)/UDP(sport=137, dport=137)/query
        
        # Verbose=0 to silence scapy
        resp = sr1(pkt, timeout=timeout, verbose=0)
        
        if resp and resp.haslayer(NBNSQueryRequest):
            # Parse the response records to find the name
            # This is complex in Scapy without proper NBNSAnswer parsing support in some versions.
            # Let's fallback to a simpler socket approach for NetBIOS which is lighter.
            pass
    except:
        pass

    # Fallback: Raw Socket NetBIOS Node Status Request
    # Transaction ID (2 bytes) + Flags (2 bytes) + Questions (2 bytes) + ...
    # ID=Random, Flags=0, Questions=1, AnswerRRs=0, AuthorityRRs=0, AdditionalRRs=0
    # Query Name: "CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" (Generic placeholder)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        
        # Truncated simple packet construction for NBSTAT
        # HEX: A2 48 00 00 00 01 00 00 00 00 00 00 + 20 + "CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + 00 + 00 21 + 00 01
        packet = b'\xa2\x48\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x20CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\x00\x00\x21\x00\x01'
        
        s.sendto(packet, (ip, 137))
        data, _ = s.recvfrom(1024)
        s.close()
        
        # Parsed Name is usually at the end or in the RRs.
        # This is a bit "hacky" but works for retrieval.
        # The name is usually the first 15 bytes of one of the records.
        # Let's try to extract a printable string.
        # Skip header (57 bytes usually for the response to this query)
        if len(data) > 57:
             num_names = data[56]
             # Names start at offset 57. Each is 18 bytes (16 name + 2 type).
             for i in range(num_names):
                 offset = 57 + (i * 18)
                 name_bytes = data[offset:offset+15]
                 name = name_bytes.decode('utf-8', errors='ignore').strip()
                 if name and name.isprintable():
                     return name
    except:
        pass
        
    return None

def resolve_mdns_name(ip, timeout=1):
    """
    Attempts to resolve mDNS name (Bonjour/Avahi) via port 5353.
    """
    try:
        # Resolving IP to name in mDNS uses reverse mapping: 4.3.2.1.in-addr.arpa
        rev_ip = ".".join(reversed(ip.split("."))) + ".in-addr.arpa"
        
        pkt = IP(dst="224.0.0.251")/UDP(sport=5353, dport=5353)/DNS(rd=1, qd=DNSQR(qname=rev_ip, qtype="PTR"))
        resp = sr1(pkt, timeout=timeout, verbose=0)
        
        if resp and resp.haslayer(DNSRR):
            # The PTR record points to the name (e.g., "My-iPhone.local.")
            name = resp[DNSRR].rdata.decode('utf-8')
            if name.endswith('.'): name = name[:-1]
            return name
    except:
        pass
        
    return None

def resolve_hostname_advanced(ip):
    """
    Tries standard DNS, then NetBIOS, then mDNS.
    """
    # 1. Standard DNS
    try:
        fqdn, _, _ = socket.gethostbyaddr(ip)
        if fqdn:
             return (ip, fqdn)
    except:
        pass
        
    # 2. NetBIOS (Great for Windows)
    nb_name = resolve_netbios_name(ip)
    if nb_name:
        return (ip, nb_name)
        
    # 3. mDNS (Great for Apple/Linux)
    mdns_name = resolve_mdns_name(ip)
    if mdns_name:
        return (ip, mdns_name)

    return (ip, None)

def perform_dns_resolution(ip_list, concurrency=20):
    """
    Resolves hostnames for a list of IPs using advanced methods.
    Returns text dict {ip: hostname}.
    """
    logger.info(f"Resolving hostnames (Advanced) for {len(ip_list)} IPs...")
    results = {}
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = executor.map(resolve_hostname_advanced, ip_list)
        
        for ip, hostname in futures:
            if hostname:
                results[ip] = hostname
                
    logger.info(f"Advanced Resolution complete. Resolved {len(results)} hostnames.")
    return results
