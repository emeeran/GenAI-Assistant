import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import sqlite3
from functools import lru_cache
import streamlit as st
import logging
import os
import time

# Configure logger
logger = logging.getLogger(__name__)

class ChatExporter:
    EXPORTS_DIR = Path("./exports")
    DB_PATH = "chat_history.db"

    @classmethod
    def get_saved_chats(cls) -> List[str]:
        """Get list of all saved chats from database"""
        try:
            conn = sqlite3.connect(cls.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT chat_name FROM chat_history ORDER BY chat_name")
            chats = [row[0] for row in cursor.fetchall()]
            conn.close()
            return chats
        except Exception as e:
            logger.error(f"Failed to get saved chats from DB: {e}")
            # Fallback to file system if DB fails
            cls.EXPORTS_DIR.mkdir(exist_ok=True)
            return sorted(set(f.stem.rsplit('_', 1)[0] for f in cls.EXPORTS_DIR.glob("*.md")))

    @classmethod
    def load_markdown(cls, chat_name: str) -> Optional[List[Dict]]:
        """Load chat history from database or file"""
        try:
            # Try database first
            conn = sqlite3.connect(cls.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM chat_history WHERE chat_name = ?", (chat_name,))
            result = cursor.fetchone()
            conn.close()

            if result:
                return json.loads(result[0])

            # Fallback to file system
            files = list(cls.EXPORTS_DIR.glob(f"{chat_name}_*.md"))
            if not files:
                return None

            latest_file = max(files, key=lambda f: f.stat().st_mtime)
            content = latest_file.read_text(encoding="utf-8")
            return cls._parse_markdown(content)

        except Exception as e:
            logger.error(f"Failed to load chat '{chat_name}': {e}")
            raise Exception(f"Failed to load chat '{chat_name}': {e}")

    @classmethod
    def _parse_markdown(cls, content: str) -> List[Dict]:
        """Parse markdown content into chat messages"""
        messages = []
        current_role = None
        current_content = []

        for line in content.split('\n'):
            if line.startswith('### 🤖 Assistant'):
                if current_role:
                    messages.append({"role": current_role, "content": '\n'.join(current_content).strip()})
                current_role = "assistant"
                current_content = []
            elif line.startswith('### 👤 User'):
                if current_role:
                    messages.append({"role": current_role, "content": '\n'.join(current_content).strip()})
                current_role = "user"
                current_content = []
            elif current_role and line:
                current_content.append(line)

        if current_role and current_content:
            messages.append({"role": current_role, "content": '\n'.join(current_content).strip()})

        return messages

    @staticmethod
    def export_markdown(chat_history: List[Dict], filename: str) -> Optional[str]:
        """Export chat history to markdown file"""
        try:
            # Ensure export directory exists
            export_dir = "exports"
            os.makedirs(export_dir, exist_ok=True)

            # Create export path
            export_path = os.path.join(export_dir, f"{filename}.md")

            # Format chat content
            content = ["# Chat Export\n"]
            content.append(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

            for msg in chat_history:
                role = msg.get('role', 'unknown')
                text = msg.get('content', '')
                feedback = msg.get('feedback', '')

                content.append(f"\n### {role.title()}")
                content.append(text)
                if feedback:
                    content.append(f"\nFeedback: {feedback}")

            # Write to file
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))

            return export_path

        except Exception as e:
            logger.error(f"Failed to export chat '{filename}': {str(e)}")
            return None

    @staticmethod
    def delete_chat(chat_name: str):
        """Delete a saved chat"""
        try:
            chat_path = Path(f"./exports/{chat_name}.md")
            if chat_path.exists():
                os.remove(chat_path)
                logger.info(f"Deleted chat: {chat_name}")
                st.success(f"Chat '{chat_name}' has been deleted.")
            else:
                logger.warning(f"Chat not found: {chat_name}")
                st.warning(f"Chat '{chat_name}' does not exist.")
        except Exception as e:
            logger.error(f"Failed to delete chat: {str(e)}")
            st.error(f"Failed to delete chat '{chat_name}'. Please try again.")

class ConfigManager:
    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        path = Path(config_path)
        if path.exists():
            return json.loads(path.read_text())
        return {}

    @staticmethod
    def save_config(config: Dict[str, Any], config_path: str):
        path = Path(config_path)
        path.write_text(json.dumps(config, indent=2))

@st.cache_data(ttl=3600)
def load_provider_config(provider: str) -> Dict:
    """Cache provider configuration"""
    # ...config loading logic...

@st.cache_data(ttl=300)
def get_saved_chats() -> List[str]:
    """Cache list of saved chats"""
    # ...chat loading logic...

@lru_cache(maxsize=100)
def process_file_content(content: str, max_length: int = 2000) -> str:
    """Cache file processing results"""
    # ...file processing logic...
