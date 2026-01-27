import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self):
        # Load env variables
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), '.env')
        load_dotenv(dotenv_path=env_path)
        
        url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY")
        
        if not url or not key:
            logger.error("Supabase credentials missing in DBManager.")
            self.supabase = None
        else:
            try:
                self.supabase: Client = create_client(url, key)
            except Exception as e:
                logger.error(f"Failed to init Supabase client: {e}")
                self.supabase = None

    def get_device_by_mac(self, mac_address):
        """
        Retrieves a device from the 'devices' table by MAC address.
        """
        if not self.supabase: return None
        try:
            response = self.supabase.table("devices").select("*").eq("mac_address", mac_address).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get device by mac {mac_address}: {e}")
            return None

    def upsert_device(self, device_data):
        """
        Inserts or updates a device in the 'devices' table.
        Uses mac_address as unique key.
        """
        if not self.supabase: return None
        
        try:
            # Check if exists to preserve ID (Supabase upsert handles this if unique constraint exists)
            # We map python dict keys to DB columns
            payload = {
                "mac_address": device_data.get("mac"),
                "ip_address": device_data.get("ip"),
                "vendor": device_data.get("vendor"),
                "hostname": device_data.get("hostname"),
                "device_type": device_data.get("type", "Unknown"),
                "os_family": device_data.get("os_family"),
                "risk_level": device_data.get("risk_level", "Low"),
                "protocols_detected": device_data.get("protocols", []),
                "last_seen": "now()"
            }
            
            # Using upsert with on_conflict
            response = self.supabase.table("devices").upsert(
                payload, on_conflict="mac_address"
            ).execute()
            
            return response.data
        except Exception as e:
            logger.error(f"Failed to upsert device {device_data.get('ip')}: {e}")
            return None

    def log_discovery(self, device_id, method, raw_data=None):
        """
        Logs a discovery event.
        """
        if not self.supabase or not device_id: return
        
        try:
            payload = {
                "device_id": device_id,
                "discovery_method": method,
                "raw_data": raw_data or {}
            }
            self.supabase.table("discovery_logs").insert(payload).execute()
        except Exception as e:
            logger.error(f"Failed to log discovery: {e}")

    def save_scan_result(self, scan_data):
        """
        Inserts a record into the 'scan_results' table.
        Used for the frontend's historical scan reports.
        """
        if not self.supabase: return None
        
        try:
            # Clean up open_ports to be a string if it's a list
            open_ports_str = scan_data.get('open_ports')
            if isinstance(open_ports_str, list):
                # Join with comma
                # items in list are like "80:http", which is what we want
                open_ports_str = ",".join([str(p) for p in open_ports_str])
            elif not isinstance(open_ports_str, str):
                open_ports_str = ""

            payload = {
                "ip_address": scan_data.get('ip'),
                "hostname": scan_data.get('hostname'),
                "mac_address": scan_data.get('mac'),
                "status": "Online", # Active scan only finds online hosts
                "open_ports": open_ports_str,
                "os_details": scan_data.get('os_family') or scan_data.get('os_details'),
                "risk_level": scan_data.get('risk_level', 'Low'),
                "vulnerabilities": scan_data.get('vulnerabilities', []),
                "scan_duration": scan_data.get('scan_duration', 0)
            }
            
            response = self.supabase.table("scan_results").insert(payload).execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to save scan result for {scan_data.get('ip')}: {e}")
            return None
