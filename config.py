import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "SUPPORTED_PROVIDERS": frozenset({"openai", "anthropic", "cohere", "groq", "xai"}),
    "DEFAULT_PROVIDER": "groq",
    "DB_PATH": "chat_history.db",
    "MODELS": {
        "openai": ("gpt-4o", "gpt-4o-mini", "o1-mini-2024-09-12"),
        "anthropic": ("claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"),
        "groq": (
            "deepseek-r1-distill-llama-70b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ),
        "cohere": ("command-r7b-12-2024",),
        "xai": ("grok-2-vision-1212",),
    },
    "MAX_TOKENS": 2000,
    "CHUNK_OVERLAP": 100,
    "RATE_LIMIT_DELAY": 2,
    "SUMMARY_MAX_TOKENS": 500,
}
