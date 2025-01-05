from typing import Dict, List, Optional
import logging
from .storage import Storage
from .exporter import ChatExporter

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Central manager for all database operations"""
    def __init__(self):
        self.storage = Storage()
        self.exporter = ChatExporter()

    def save_chat(self, chat_history: List[Dict], name: str) -> bool:
        """Save chat history"""
        try:
            # Save to both storage and exports
            self.storage.save({'history': chat_history}, name)
            self.exporter.export_markdown(chat_history, name)
            return True
        except Exception as e:
            logger.error(f"Save chat error: {e}")
            return False

    def load_chat(self, name: str) -> Optional[List[Dict]]:
        """Load chat history"""
        try:
            # Try loading from storage first
            data = self.storage.load(name)
            if data and 'history' in data:
                return data['history']

            # Fall back to markdown export
            return self.exporter.load_markdown(name)
        except Exception as e:
            logger.error(f"Load chat error: {e}")
            return None

    def list_chats(self) -> List[str]:
        """List all available chats"""
        storage_files = set(self.storage.list_files())
        export_files = set(self.exporter.get_saved_chats())
        return sorted(storage_files | export_files)

    def delete_chat(self, name: str) -> bool:
        """Delete chat from all storage"""
        success = True
        if not self.storage.delete(name):
            success = False
        # Also try to delete export if it exists
        try:
            (ChatExporter.EXPORTS_DIR / f"{name}.md").unlink(missing_ok=True)
        except Exception:
            success = False
        return success
