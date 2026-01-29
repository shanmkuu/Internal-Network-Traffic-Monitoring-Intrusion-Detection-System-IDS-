import re
import logging

class RuleParser:
    """
    Parses Suricata-style rules.
    Format: action proto src_ip src_port -> dest_ip dest_port (options)
    Example: alert http any any -> any any (msg:"Possible SQL Injection"; content:"UNION SELECT"; sid:1000001; rev:1;)
    """

    def __init__(self):
        self.rules = []

    def parse_file(self, file_path):
        """Parses a file containing Suricata rules."""
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    rule = self.parse_rule(line)
                    if rule:
                        self.rules.append(rule)
            logging.info(f"Loaded {len(self.rules)} rules from {file_path}")
            return self.rules
        except Exception as e:
            logging.error(f"Failed to parse rule file {file_path}: {e}")
            return []

    def parse_rule(self, line):
        """Parses a single rule line."""
        line = line.strip()
        if not line or line.startswith('#'):
            return None

        # Basic regex to capture the header and options
        # Group 1: Header (action proto src ... -> dst ...)
        # Group 2: Options (content:"..."; msg:"...";)
        pattern = r"^([^\(]+)\((.*)\)$"
        match = re.match(pattern, line)

        if not match:
            logging.warning(f"Invalid rule format: {line}")
            return None

        header_str = match.group(1).strip()
        options_str = match.group(2).strip()

        # Parse Header
        parts = header_str.split()
        if len(parts) < 7: # action proto src port direction dst port
            return None
        
        # Simple extraction (can be expanded for complex IP/port lists)
        rule = {
            "action": parts[0],
            "protocol": parts[1],
            "src_ip": parts[2],
            "src_port": parts[3],
            "direction": parts[4], # -> or <>
            "dest_ip": parts[5],
            "dest_port": parts[6],
            "options": self._parse_options(options_str),
            "raw": line
        }
        
        return rule

    def _parse_options(self, options_str):
        """Parses the options part of the rule."""
        options = {}
        # improved regex to handle escaped semicolons if needed, 
        # but simple split by ';' works for standard simple rules
        # Matches key:value; or key;
        
        # Helper to parse fields like msg:"Something"; sid:123;
        parts = [p.strip() for p in options_str.split(';') if p.strip()]
        
        for part in parts:
            if ':' in part:
                key, val = part.split(':', 1)
                key = key.strip()
                val = val.strip().strip('"') # Remove surrounding quotes
                options[key] = val
            else:
                options[part] = True # boolean flags like 'nocase'
        
        return options
