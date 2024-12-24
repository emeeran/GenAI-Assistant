from dataclasses import dataclass
from typing import List, Dict, Optional
import os
import logging
from functools import lru_cache
import openai

logger = logging.getLogger(__name__)

@dataclass
class Provider:
    name: str
    models: List[str]
    api_key_env: str

class ModelManager:
    DEFAULT_MODELS = {
        "OpenAI": [
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ],
        "Anthropic": [
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-2.1"
        ],
        "Google": [
            "gemini-pro",
            "gemini-pro-vision"
        ],
        "Mistral": [
            "mistral-tiny",
            "mistral-small",
            "mistral-medium",
            "mistral-large"
        ]
    }

    PROVIDERS = {
        "OpenAI": Provider("OpenAI", DEFAULT_MODELS["OpenAI"], "OPENAI_API_KEY"),
        "Anthropic": Provider("Anthropic", DEFAULT_MODELS["Anthropic"], "ANTHROPIC_API_KEY"),
        "Google": Provider("Google", DEFAULT_MODELS["Google"], "GOOGLE_API_KEY"),
        "Mistral": Provider("Mistral", DEFAULT_MODELS["Mistral"], "MISTRAL_API_KEY")
    }

    @staticmethod
    @lru_cache()
    def get_available_models(provider_name: str) -> List[str]:
        """Get available models for a provider with API fallback"""
        if provider_name == "OpenAI":
            try:
                # Direct OpenAI client usage
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.warning("OpenAI API key not found")
                    return ModelManager.DEFAULT_MODELS["OpenAI"]

                client = openai.OpenAI(api_key=api_key)
                models = client.models.list()
                return [model.id for model in models
                       if any(name in model.id.lower()
                       for name in ["gpt-4", "gpt-3.5"])]

            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")
                return ModelManager.DEFAULT_MODELS["OpenAI"]

        return ModelManager.DEFAULT_MODELS.get(provider_name, [])

    @staticmethod
    def get_providers() -> List[str]:
        """Get list of available providers"""
        return list(ModelManager.PROVIDERS.keys())

from typing import Dict, Any
import openai
from anthropic import Anthropic
import google.generativeai as genai
import os
import logging

logger = logging.getLogger(__name__)

class MessageHandler:
    def __init__(self):
        self.setup_clients()

    def setup_clients(self):
        """Initialize API clients"""
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    async def get_response(self, provider: str, model: str, messages: list) -> str:
        """Get response from selected provider"""
        try:
            if provider == "OpenAI":
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages
                )
                return response.choices[0].message.content

            elif provider == "Anthropic":
                response = self.anthropic.messages.create(
                    model=model,
                    messages=messages
                )
                return response.content[0].text

            elif provider == "Google":
                model = genai.GenerativeModel(model_name=model)
                response = model.generate_content([m["content"] for m in messages])
                return response.text

            else:
                raise ValueError(f"Unknown provider: {provider}")

        except Exception as e:
            logger.error(f"Error getting response from {provider}: {str(e)}")
            return f"Error: Failed to get response from {provider}"