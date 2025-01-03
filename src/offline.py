import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
import json
import streamlit as st
import logging

# Configure logger
logger = logging.getLogger(__name__)

class OfflineStorage:
    DB_PATH = Path("./data/offline_storage.db")

    def __init__(self):
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(str(self.DB_PATH))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_cache (
                query TEXT PRIMARY KEY,
                response TEXT,
                context TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def save_response(self, query: str, response: str, context: Optional[Dict] = None):
        """Save response to offline storage"""
        conn = sqlite3.connect(str(self.DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO chat_cache (query, response, context) VALUES (?, ?, ?)",
            (query, response, json.dumps(context or {}))
        )
        conn.commit()
        conn.close()

    def get_offline_response(self, query: str) -> Optional[str]:
        """Get cached response for query"""
        conn = sqlite3.connect(str(self.DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT response FROM chat_cache WHERE query = ?", (query,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
