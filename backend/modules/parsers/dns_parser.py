from scapy.all import DNS, DNSQR, UDP

class DNSParser:
    """
    Parses DNS traffic from Scapy packets.
    """
    def parse(self, packet):
        """
        Returns a dict with DNS metadata if present, else None.
        """
        if DNS not in packet:
            return None
            
        dns = packet[DNS]
        
        # Check for Query
        if dns.qr == 0 and DNSQR in dns:
            qname = dns[DNSQR].qname.decode('utf-8', errors='ignore') if dns[DNSQR].qname else ""
            qtype = dns[DNSQR].qtype
            
            return {
                "type": "query",
                "qname": qname,
                "qtype": qtype
            }
            
        return None

dns_parser = DNSParser()
