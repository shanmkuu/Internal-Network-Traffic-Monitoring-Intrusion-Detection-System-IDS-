import time
import logging
from collections import defaultdict

class FlowManager:
    """
    Manages network flows (5-tuple state).
    Flow ID: (src_ip, src_port, dst_ip, dst_port, protocol)
    """
    def __init__(self):
        self.flows = {} # Key: FlowID, Value: FlowState
        self.timeout = 60 # Seconds
        self.cleanup_interval = 10
        self.last_cleanup = time.time()

    def get_flow_id(self, packet):
        """Extracts 5-tuple from packet."""
        # This will depend on Scapy packet structure passed from monitor.py
        # Assuming packet has IP/TCP/UDP layers
        from scapy.all import IP, TCP, UDP, ICMP
        
        if IP not in packet:
            return None
            
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        proto = packet[IP].proto
        src_port = 0
        dst_port = 0
        
        if TCP in packet:
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
        elif UDP in packet:
            src_port = packet[UDP].sport
            dst_port = packet[UDP].dport
            
        # Normalize direction (canonical flow ID)
        # Always (lower_ip, lower_port, higher_ip, higher_port, proto) ? 
        # Or standard source->dest. Suricata tracks bi-directionally.
        # For simplicity, we use source->dest string tuple.
        return (src_ip, src_port, dst_ip, dst_port, proto)

    def update_flow(self, packet):
        """Updates the state of a flow."""
        flow_id = self.get_flow_id(packet)
        if not flow_id:
            return

        now = time.time()
        
        if flow_id not in self.flows:
            self.flows[flow_id] = {
                "start_time": now,
                "last_seen": now,
                "packet_count": 0,
                "bytes": 0,
                "state": "new" 
            }
        
        flow = self.flows[flow_id]
        flow["last_seen"] = now
        flow["packet_count"] += 1
        flow["bytes"] += len(packet)
        
        # Simple TCP State Machine Simulation
        from scapy.all import TCP
        if TCP in packet:
            flags = packet[TCP].flags
            if flags == 'S': # SYN
                flow["state"] = "syn_sent"
            elif flags == 'SA': # SYN-ACK
                if flow["state"] == "syn_sent":
                    flow["state"] = "established"
            elif flags == 'F' or flags == 'R': # FIN or RST
                flow["state"] = "closed"

        self._cleanup_if_needed()
        return flow

    def _cleanup_if_needed(self):
        """Removes old flows."""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
            
        expired = []
        for fid, flow in self.flows.items():
            if now - flow["last_seen"] > self.timeout:
                expired.append(fid)
                
        for fid in expired:
            del self.flows[fid]
            
        self.last_cleanup = now
        # logging.debug(f"Cleaned up {len(expired)} flows. Active: {len(self.flows)}")

flow_manager = FlowManager()
