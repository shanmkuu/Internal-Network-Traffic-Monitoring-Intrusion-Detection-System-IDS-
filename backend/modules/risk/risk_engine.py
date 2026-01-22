import logging

logger = logging.getLogger(__name__)

class RiskEngine:
    def __init__(self):
        self.high_risk_ports = [21, 23, 445, 3389] # FTP, Telnet, SMB, RDP
        self.critical_services = ["Telnet", "VNC", "TeamViewer"]
        
    def calculate_risk(self, device_profile):
        """
        Calculates a risk score (0-100) and level based on device profile.
        device_profile includes: open_ports, vendor, os_family, protocols.
        """
        score = 0
        reasons = []
        
        # 1. Open Ports Analysis
        ports = device_profile.get('open_ports', [])
        for port in ports:
            if port in self.high_risk_ports:
                score += 20
                reasons.append(f"High risk port open: {port}")
                
        # 2. Insecure Protocols
        protocols = device_profile.get('protocols_detected', [])
        if 'http' in protocols and 'https' not in protocols:
            score += 10
            reasons.append("Unencrypted HTTP detected")
        if 'telnet' in protocols:
            score += 30
            reasons.append("Telnet service detected")

        # 3. OS / Vendor Risks
        os_family = device_profile.get('os_family', 'Unknown')
        if os_family == "Windows" and 445 in ports:
            score += 10 # Windows with SMB is a common target
            
        # 4. Unknown Devices
        if device_profile.get('vendor') == "Unknown":
            score += 5
            reasons.append("Unknown vendor")

        # Cap score
        score = min(score, 100)
        
        # Determine Level
        if score >= 70:
            level = "High"
        elif score >= 40:
            level = "Medium"
        else:
            level = "Low"
            
        return {
            "score": score,
            "level": level,
            "reasons": reasons
        }
