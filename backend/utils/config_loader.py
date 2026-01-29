import yaml
import os
import logging
from typing import Dict, Any

class ConfigLoader:
    """Loads configuration from suricata.yaml and classification.config"""
    
    def __init__(self, config_path="suricata.yaml", classification_path="classification.config"):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(self.base_dir, config_path)
        self.classification_path = os.path.join(self.base_dir, classification_path)
        self.config = {}
        self.classifications = {}
        
        self.load_config()
        self.load_classification()

    def load_config(self):
        """Loads the main YAML configuration."""
        if not os.path.exists(self.config_path):
            logging.warning(f"Config file not found: {self.config_path}. Using defaults.")
            return

        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logging.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logging.error(f"Failed to load config: {e}")

    def load_classification(self):
        """Loads classification map from file."""
        # Format: config classification: shortname,description,priority
        if not os.path.exists(self.classification_path):
            logging.warning(f"Classification file not found: {self.classification_path}")
            return

        try:
            with open(self.classification_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if line.startswith("config classification:"):
                        # Remove prefix
                        content = line.replace("config classification:", "").strip()
                        parts = [p.strip() for p in content.split(',')]
                        if len(parts) >= 3:
                            shortname = parts[0]
                            description = parts[1]
                            priority = int(parts[2])
                            self.classifications[shortname] = {
                                "description": description,
                                "priority": priority
                            }
            logging.info(f"Loaded {len(self.classifications)} classifications")
        except Exception as e:
            logging.error(f"Failed to load classifications: {e}")

    def get(self, key: str, default=None):
        """Dot notation access to config (e.g. 'outputs.eve-log.enabled')"""
        keys = key.split('.')
        val = self.config
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
        return val if val is not None else default

    def get_classification(self, classtype):
        """Returns (priority, description) for a classtype."""
        if classtype in self.classifications:
            c = self.classifications[classtype]
            return c["priority"], c["description"]
        return 3, "Unknown Class Type" # Default priority 3 (Low)

# Global Instance
config_loader = ConfigLoader()
