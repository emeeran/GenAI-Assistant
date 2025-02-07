import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    """Handles configuration file management"""

    @staticmethod
    def load_config(config_path: str) -> Optional[Dict]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing config file: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}")
            return None

    @staticmethod
    def save_config(config: Dict, config_path: str) -> bool:
        """Save configuration to JSON file"""
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
