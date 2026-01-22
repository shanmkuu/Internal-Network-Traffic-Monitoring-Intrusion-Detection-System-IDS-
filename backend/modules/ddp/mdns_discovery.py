import logging
import socket
from zeroconf import Zeroconf, ServiceBrowser

logger = logging.getLogger(__name__)

class MDNSListener:
    def __init__(self):
        self.zeroconf = Zeroconf()
        self.discovered_services = {}

    def remove_service(self, zeroconf, type, name):
        pass

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            ip = socket.inet_ntoa(info.addresses[0])
            self.discovered_services[ip] = {
                "name": name,
                "type": type,
                "server": info.server,
                "properties": {k.decode('utf-8', 'ignore'): (v.decode('utf-8', 'ignore') if isinstance(v, bytes) else v) for k, v in info.properties.items()}
            }
            logger.info(f"mDNS Discovered: {ip} - {name}")

    def start_discovery(self, duration=10):
        browser = ServiceBrowser(self.zeroconf, ["_http._tcp.local.", "_googlecast._tcp.local.", "_ipp._tcp.local."], self)
        import time
        time.sleep(duration)
        self.zeroconf.close()
        return self.discovered_services
