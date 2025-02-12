from pathlib import Path
from typing import Dict, Any, FrozenSet
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    SUPPORTED_PROVIDERS: FrozenSet[str] = frozenset({"groq", "anthropic", "openai"})
    DEFAULT_PROVIDER: str = "groq"
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DB_PATH: Path = BASE_DIR / "data" / "chat_history.db"
    EXPORTS_PATH: Path = BASE_DIR / "exports"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
