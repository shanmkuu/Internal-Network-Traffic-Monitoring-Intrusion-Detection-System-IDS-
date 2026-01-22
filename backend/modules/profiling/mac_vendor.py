from mac_vendor_lookup import MacLookup
import logging

logger = logging.getLogger(__name__)

# Initialize global lookup to avoid reloading
try:
    mac_lookup = MacLookup()
except Exception:
    mac_lookup = None

def get_mac_vendor(mac_address):
    """
    Returns the vendor name for a given MAC address.
    """
    if not mac_lookup:
        return "Unknown"
        
    try:
        return mac_lookup.lookup(mac_address)
    except Exception:
        return "Unknown"

def update_mac_db():
    """
    Updates the OUI database from the web.
    """
    try:
        if mac_lookup:
            mac_lookup.update_vendors()
            logger.info("MAC Vendor DB updated.")
    except Exception as e:
        logger.error(f"Failed to update MAC Vendor DB: {e}")
