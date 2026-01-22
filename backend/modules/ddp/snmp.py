from pysnmp.hlapi import *
import logging

logger = logging.getLogger(__name__)

def snmp_get_info(ip, community='public', port=161):
    """
    Queries SNMP for basic system info (SysDescr, SysName).
    Returns dict or None if failed.
    """
    data = {}
    try:
        iterator = getCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=1), # v2c
            UdpTransportTarget((ip, port), timeout=1.0, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0)),
            ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysName', 0)),
            ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysUpTime', 0))
        )

        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

        if errorIndication:
            return None
        elif errorStatus:
            return None
        else:
            # Parse results
            # Order matches ObjectType calls above
            data['sys_descr'] = varBinds[0][1].prettyPrint()
            data['sys_name'] = varBinds[1][1].prettyPrint()
            data['uptime'] = varBinds[2][1].prettyPrint()
            return data

    except Exception as e:
        logger.debug(f"SNMP query failed for {ip}: {e}")
        return None

def scan_snmp(ip_list, communities=['public', 'private']):
    """
    Tries to find SNMP enabled devices in the IP list.
    """
    logger.info("Starting SNMP Probe...")
    results = {}
    
    for ip in ip_list:
        for comm in communities:
            info = snmp_get_info(ip, comm)
            if info:
                results[ip] = info
                logger.info(f"SNMP Found on {ip} (comm: {comm}): {info['sys_name']}")
                break # Stop after first working community
                
    return results
