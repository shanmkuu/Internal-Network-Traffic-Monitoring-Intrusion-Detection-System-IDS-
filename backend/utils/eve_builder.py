from datetime import datetime

SEVERITY_MAP = {
    "High": 1,
    "Medium": 2,
    "Low": 3
}

def clean_severity(sev_str):
    """Ensure severity is valid title case for map lookup."""
    if not sev_str:
        return "Low"
    return str(sev_str).capitalize()

def build_eve_alert(db_row):
    """
    Converts a database alert row (or dict) to EVE JSON format.
    
    Args:
        db_row (dict): A dictionary representing a row from the 'alerts' table.
                       Expected keys: created_at, source_ip, destination_ip, protocol,
                       severity, description, alert_type.
    
    Returns:
        dict: EVE JSON compliant event object.
    """
    severity_int = SEVERITY_MAP.get(clean_severity(db_row.get('severity')), 3)
    
    # Ensure protocol is not None
    proto = db_row.get('protocol')
    if not proto:
        proto = "UNKNOWN"

    return {
        "timestamp": db_row.get('created_at', datetime.now().isoformat()),
        "event_type": "alert",
        "src_ip": db_row.get('source_ip', '0.0.0.0'),
        "dest_ip": db_row.get('destination_ip', '0.0.0.0'),
        "proto": proto.upper(),
        "alert": {
            "action": "allowed", # Default for IDS mode
            "gid": 1,
            "signature_id": 1000001, # Placeholder SID
            "rev": 1,
            "signature": db_row.get('description') or db_row.get('alert_type', 'Unknown Alert'),
            "category": db_row.get('alert_type', 'Misc'),
            "severity": severity_int
        },
        # Preserve original ID for frontend keys if needed
        "_original_id": db_row.get('id')
    }
