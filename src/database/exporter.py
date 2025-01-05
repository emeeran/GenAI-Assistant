from pathlib import Path
import json
from typing import List, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ChatExporter:
    EXPORTS_DIR = Path("exports")
    EXPORTS_DIR.mkdir(exist_ok=True)

    @classmethod
    def export_markdown(cls, chat_history: List[Dict], filename: str) -> Optional[str]:
        """Export chat history to markdown file"""
        try:
            filepath = cls.EXPORTS_DIR / f"{filename}.md"

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Chat Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for msg in chat_history:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    f.write(f"### {role.title()}\n{content}\n\n")

            return str(filepath)
        except Exception as e:
            logger.error(f"Export error: {e}")
            return None

    @classmethod
    def load_markdown(cls, filename: str) -> Optional[List[Dict]]:
        """Load chat history from markdown file"""
        try:
            filepath = cls.EXPORTS_DIR / f"{filename}.md"
            if not filepath.exists():
                return None

            chat_history = []
            current_role = None
            current_content = []

            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('### '):
                        if current_role:
                            chat_history.append({
                                'role': current_role.lower(),
                                'content': '\n'.join(current_content).strip()
                            })
                        current_role = line[4:].strip()
                        current_content = []
                    elif line.strip() and current_role:
                        current_content.append(line.strip())

            if current_role and current_content:
                chat_history.append({
                    'role': current_role.lower(),
                    'content': '\n'.join(current_content).strip()
                })

            return chat_history
        except Exception as e:
            logger.error(f"Load error: {e}")
            return None

    @classmethod
    def get_saved_chats(cls) -> List[str]:
        """Get list of saved chat files"""
        return [f.stem for f in cls.EXPORTS_DIR.glob("*.md")]
