import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import sqlite3

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
            raise StorageError(f"Failed to load chat '{chat_name}': {e}")

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

    @classmethod
    def export_markdown(cls, history: List[Dict], filename: str) -> Path:
        """Export chat history to both database and markdown file"""
        try:
            # Save to database
            conn = sqlite3.connect(cls.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history
                (chat_name TEXT PRIMARY KEY, data JSON)
            """)
            cursor.execute(
                "INSERT OR REPLACE INTO chat_history (chat_name, data) VALUES (?, ?)",
                (filename, json.dumps(history))
            )
            conn.commit()
            conn.close()

            # Save to file
            cls.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = cls.EXPORTS_DIR / f"{filename}_{timestamp}.md"
            content = cls._format_markdown(history)
            export_path.write_text(content, encoding="utf-8")
            logger.info(f"Exported chat '{filename}' to {export_path}")
            return export_path

        except Exception as e:
            logger.error(f"Failed to export chat '{filename}': {e}")
            raise StorageError(f"Failed to export chat '{filename}': {e}")

    @staticmethod
    def _format_markdown(history: List[Dict]) -> str:
        """Format chat history as markdown"""
        lines = ["# Chat Export\n"]
        for msg in history:
            role = "🤖 Assistant" if msg["role"] == "assistant" else "👤 User"
            lines.extend([f"### {role}\n", f"{msg['content']}\n"])
        return "\n".join(lines)

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
