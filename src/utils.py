# utils.py
import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime


class ChatExporter:
    @staticmethod
    def export_markdown(history: List[Dict], filename: str) -> Path:
        export_dir = Path("./exports")
        export_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = export_dir / f"{filename}_{timestamp}.md"

        content = ChatExporter._format_markdown(history)
        export_path.write_text(content, encoding="utf-8")
        return export_path

    @staticmethod
    def _format_markdown(history: List[Dict]) -> str:
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
