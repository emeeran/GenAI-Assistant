import json
from typing import List, Dict
from datetime import datetime

class ChatExporter:
    """Handles chat history export functionality"""

    @staticmethod
    def export_chat(chat_history: List[Dict], format: str = 'json') -> str:
        """Export chat history in the specified format"""
        if format == 'json':
            return json.dumps(chat_history, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    @staticmethod
    def save_chat(chat_history: List[Dict], filename: str = None) -> str:
        """Save chat history to a file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_export_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(chat_history, f, indent=2)

        return filename
