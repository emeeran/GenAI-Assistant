import sqlite3
import json
from typing import List, Dict, Optional
from pathlib import Path
from ..utils.export import format_markdown

class DB:
    def __init__(self, path: str):
        """Initialize database connection and create tables"""
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._init_tables()

    def _init_tables(self):
        """Initialize database tables"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                chat_name TEXT PRIMARY KEY,
                data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    # Add other DB methods with better error handling and performance optimization
