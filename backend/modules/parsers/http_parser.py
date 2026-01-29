from scapy.all import TCP, Raw

class HTTPParser:
    """
    Parses HTTP traffic from Scapy packets.
    """
    def parse(self, packet):
        """
        Returns a dict with HTTP metadata if present, else None.
        """
        if TCP not in packet:
            return None
            
        # Basic check for common HTTP ports or pattern matching
        # Suricata parses typically on any port if stream looks like HTTP
        # payload = str(packet[Raw].load) if Raw in packet else ""
        
        if Raw not in packet:
            return None
            
        try:
            payload = packet[Raw].load.decode('utf-8', errors='ignore')
        except:
            return None

        # Request
        if payload.startswith(('GET ', 'POST ', 'PUT ', 'DELETE ', 'HEAD ', 'OPTIONS ', 'PATCH ')):
            lines = payload.split('\r\n')
            req_line = lines[0]
            parts = req_line.split(' ')
            if len(parts) >= 2:
                method = parts[0]
                uri = parts[1]
                
                # Extract Host and User-Agent
                headers = {}
                for line in lines[1:]:
                    if ': ' in line:
                        k, v = line.split(': ', 1)
                        headers[k.lower()] = v
                        
                return {
                    "type": "request",
                    "req_line": req_line.strip(),
                    "method": method,
                    "uri": uri,
                    "host": headers.get("host", ""),
                    "user_agent": headers.get("user-agent", "")
                }
                
        # Response checks skipped for brevity in this iteration
        return None

http_parser = HTTPParser()
