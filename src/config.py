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

PERFORMANCE_CONFIG = {
    "CACHE_TTL": 600,  # Cache timeout in seconds
    "MAX_HISTORY_LENGTH": 100,  # Maximum messages to keep
    "MESSAGES_PER_PAGE": 10,  # Messages per page
    "MAX_FILE_SIZE": 5 * 1024 * 1024,  # 5MB max file size
    "CHUNK_SIZE": 1024,  # Chunk size for processing
    "RESPONSE_TIMEOUT": 30,  # API timeout
    "MAX_RETRIES": 3,  # Maximum retries
    "DEBOUNCE_MS": 100,  # Input debounce
}

CONTEXT_CONFIG = {
    "MAX_CONTEXT_LENGTH": 10,
    "CONTEXT_RELEVANCE_THRESHOLD": 0.5,
    "OFFLINE_CACHE_SIZE": 1000,
    "OFFLINE_CACHE_TTL": 7 * 24 * 60 * 60,  # 7 days
}

# Update main config
CONFIG.update({
    "PERFORMANCE": PERFORMANCE_CONFIG,
    "CONTEXT": CONTEXT_CONFIG,
    # ...existing config...
})

# Create necessary directories
CONFIG["DB_PATH"].parent.mkdir(parents=True, exist_ok=True)
CONFIG["EXPORTS_PATH"].mkdir(parents=True, exist_ok=True)
