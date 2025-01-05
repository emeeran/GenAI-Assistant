from typing import Dict, List, Optional
import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Storage:
    """Base storage class for chat data"""
    def __init__(self, storage_dir: str = 'data'):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def save(self, data: Dict, filename: str) -> bool:
        """Save data to storage"""
        try:
            filepath = self.storage_dir / f"{filename}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Storage save error: {e}")
            return False

    def load(self, filename: str) -> Optional[Dict]:
        """Load data from storage"""
        try:
            filepath = self.storage_dir / f"{filename}.json"
            if not filepath.exists():
                return None
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Storage load error: {e}")
            return None

    def list_files(self) -> List[str]:
        """List all stored files"""
        return [f.stem for f in self.storage_dir.glob("*.json")]

    def delete(self, filename: str) -> bool:
        """Delete file from storage"""
        try:
            filepath = self.storage_dir / f"{filename}.json"
            if filepath.exists():
                filepath.unlink()
            return True
        except Exception as e:
            logger.error(f"Storage delete error: {e}")
            return False
