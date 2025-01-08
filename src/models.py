from typing import Dict, Tuple, FrozenSet, Optional
from dataclasses import dataclass
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)

class ModelCapability(Enum):
    VISION = auto()
    AUDIO = auto()
    CODE = auto()
    FUNCTION = auto()

@dataclass(frozen=True)
class ModelConfig:
    name: str
    context_length: int
    capabilities: Tuple[ModelCapability, ...] = tuple()
    max_tokens: Optional[int] = None
    message_format: str = "default"  # Add message format type

    @property
    def supports_vision(self) -> bool: return ModelCapability.VISION in self.capabilities
    @property
    def supports_audio(self) -> bool: return ModelCapability.AUDIO in self.capabilities

SUPPORTED_PROVIDERS: FrozenSet[str] = frozenset({
    "groq", "openai", "anthropic", "cohere", "xai"
})

PROVIDERS = {
    "groq": ("mixtral", "llama2", "gemma"),
    "openai": ("gpt-4", "gpt-3.5"),
    "anthropic": ("claude-3", "claude-2"),
    "cohere": ("command"),
    "xai": ("grok")
}

MODELS = {
    "groq": {
        "mixtral-8x7b-32768": ModelConfig(
            "mixtral-8x7b-32768", 32768, (ModelCapability.CODE,)
        ),
        "llama2-70b-4096": ModelConfig(
            "llama2-70b-4096", 4096, (ModelCapability.CODE,)
        ),
        "gemma-7b-it": ModelConfig(
            "gemma-7b-it", 8192, (ModelCapability.CODE,)
        ),
        "mixtral-8x7b-instruct": ModelConfig(
            "mixtral-8x7b-instruct", 32768, (ModelCapability.CODE,)
        ),
        "llama2-70b-32k": ModelConfig(
            "llama2-70b-32k", 32768, (ModelCapability.CODE,)
        )
    },
    "openai": {
        "gpt-4-turbo-preview": ModelConfig(
            "gpt-4-turbo-preview", 128000,
            (ModelCapability.VISION, ModelCapability.AUDIO, ModelCapability.FUNCTION)
        ),
        "gpt-4-vision-preview": ModelConfig(
            "gpt-4-vision-preview", 128000,
            (ModelCapability.VISION, ModelCapability.FUNCTION)
        ),
        "gpt-4": ModelConfig(
            "gpt-4", 8192,
            (ModelCapability.FUNCTION,)
        ),
        "gpt-3.5-turbo": ModelConfig(
            "gpt-3.5-turbo", 16384,
            (ModelCapability.FUNCTION,)
        ),
        "gpt-3.5-turbo-16k": ModelConfig(
            "gpt-3.5-turbo-16k", 16384,
            (ModelCapability.FUNCTION,)
        )
    },
    "anthropic": {
        "claude-3-opus": ModelConfig(
            "claude-3-opus", 200000,
            (ModelCapability.VISION, ModelCapability.CODE)
        ),
        "claude-3-sonnet": ModelConfig(
            "claude-3-sonnet", 200000,
            (ModelCapability.VISION, ModelCapability.CODE)
        ),
        "claude-3-haiku": ModelConfig(
            "claude-3-haiku", 200000,
            (ModelCapability.VISION,)
        ),
        "claude-2.1": ModelConfig(
            "claude-2.1", 100000,
            (ModelCapability.CODE,)
        ),
        "claude-2.0": ModelConfig(
            "claude-2.0", 100000,
            (ModelCapability.CODE,)
        )
    },
    "cohere": {
        "command-r": ModelConfig(
            "command-r", 128000,
            (ModelCapability.CODE, ModelCapability.FUNCTION)
        ),
        "command-light": ModelConfig(
            "command-light", 128000,
            (ModelCapability.FUNCTION,)
        ),
        "command": ModelConfig(
            "command", 128000,
            (ModelCapability.FUNCTION,)
        ),
        "command-nightly": ModelConfig(
            "command-nightly", 128000,
            (ModelCapability.VISION, ModelCapability.FUNCTION)
        ),
        "command-light-nightly": ModelConfig(
            "command-light-nightly", 128000,
            (ModelCapability.FUNCTION,)
        )
    },
    "xai": {
        "grok-1": ModelConfig(
            "grok-1", 8192,
            (ModelCapability.CODE,)
        ),
        "grok-1-pro": ModelConfig(
            "grok-1-pro", 8192,
            (ModelCapability.CODE, ModelCapability.VISION)
        ),
        "grok-1-vision": ModelConfig(
            "grok-1-vision", 8192,
            (ModelCapability.VISION,)
        ),
        "grok-1-nano": ModelConfig(
            "grok-1-nano", 4096,
            (ModelCapability.CODE,)
        ),
        "grok-1-lite": ModelConfig(
            "grok-1-lite", 4096
        )
    }
}

def get_model_config(provider: str, model: str) -> Optional[ModelConfig]:
    """Get model configuration safely"""
    config = MODELS.get(provider, {}).get(model)
    if config is None:
        logger.warning(f"Model config not found for provider: {provider}, model: {model}")
    return config

def list_models(provider: str) -> Tuple[str, ...]:
    """Get available models for provider"""
    return tuple(MODELS.get(provider, {}).keys())

def validate_model(provider: str, model: str) -> bool:
    """Check if model exists and is valid"""
    return bool(get_model_config(provider, model))
