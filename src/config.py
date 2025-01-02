from typing import Dict, Any
from pathlib import Path

CONFIG: Dict[str, Any] = {
    "SUPPORTED_PROVIDERS": frozenset({"openai", "anthropic", "cohere", "groq", "xai"}),
    "DEFAULT_PROVIDER": "groq",
    "DB_PATH": Path("./data/chat_history.db"),
    "EXPORTS_PATH": Path("./exports"),
    "MODELS": {
        "openai": ("gpt-4o", "gpt-4o-mini"),
        "anthropic": ("claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"),
        "groq": ("llama-3.3-70b-versatile", "llama-3.1-8b-instant"),
        "cohere": ("command-r7b-12-2024",),
        "xai": ("grok-2-vision-1212",)
    },
    "VOICE_LANGUAGES": {
        "English": "en",
        "French": "fr",
        "German": "de",
        "Spanish": "es",
        "Japanese": "ja"
    },
    "MAX_HISTORY": 100,
    "CACHE_TTL": 3600
}

# Create necessary directories
CONFIG["DB_PATH"].parent.mkdir(parents=True, exist_ok=True)
CONFIG["EXPORTS_PATH"].mkdir(parents=True, exist_ok=True)
