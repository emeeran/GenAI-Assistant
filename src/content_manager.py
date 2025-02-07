from typing import Optional, Dict
from pathlib import Path
import json
import os


class ContentManager:
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.content_index = {}
        self._load_index()

    def _load_index(self):
        index_path = self.cache_dir / "content_index.json"
        if index_path.exists():
            with open(index_path, "r") as f:
                self.content_index = json.load(f)

    def _save_index(self):
        with open(self.cache_dir / "content_index.json", "w") as f:
            json.dump(self.content_index, f)

    def store_content(self, file_name: str, content: str, file_type: str) -> str:
        """Store content and return reference ID"""
        content_id = str(hash(f"{file_name}{content}"))[:10]
        cache_path = self.cache_dir / f"{content_id}.txt"

        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(content)

        self.content_index[content_id] = {
            "file_name": file_name,
            "file_type": file_type,
            "path": str(cache_path),
        }
        self._save_index()
        return content_id

    def get_content(self, content_id: str) -> Optional[Dict]:
        """Retrieve content and metadata by ID"""
        if content_id not in self.content_index:
            return None

        info = self.content_index[content_id]
        try:
            with open(info["path"], "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "content": content,
                "file_name": info["file_name"],
                "file_type": info["file_type"],
            }
        except Exception:
            return None
