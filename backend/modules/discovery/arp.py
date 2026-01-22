from scapy.all import ARP, Ether, srp
import logging

logger = logging.getLogger(__name__)

def perform_arp_scan(target_range, timeout=2):
    """
    Performs an ARP scan on the specified network range.
    Returns a list of dicts: [{'ip': '192.168.1.1', 'mac': 'aa:bb:cc:dd:ee:ff'}, ...]
    """
    logger.info(f"Starting ARP scan on {target_range}")
    devices = []
    try:
        arp = ARP(pdst=target_range)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp

        result = srp(packet, timeout=timeout, verbose=0)[0]

        for sent, received in result:
            devices.append({
                "ip": received.psrc,
                "mac": received.hwsrc
            })
            
        logger.info(f"ARP Scan complete. Found {len(devices)} devices.")
        return devices

    except Exception as e:
        logger.error(f"ARP Scan failed: {e}")
        return []
