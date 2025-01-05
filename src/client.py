import os
from typing import Dict, Set, Optional, List, Any
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

from .provider import ProviderFactory

logger = logging.getLogger(__name__)

@dataclass
class CompletionResponse:
    choices: list

    @staticmethod
    def from_dict(data: Dict) -> 'CompletionResponse':
        return CompletionResponse(
            choices=[{"message": {"content": data.get("content", "")}}]
        )

class ChatCompletions:
    def __init__(self, client: 'Client'):
        self.client = client

    def create(self, model: str, messages: list, temperature: float) -> CompletionResponse:
        # Placeholder for actual API call
        # In a real implementation, this would make calls to the respective APIs
        return CompletionResponse.from_dict({"content": "Hello! This is a placeholder response."})

class Client:
    def __init__(self, provider_configs: dict = {}):
        """
        Initialize the client with provider configurations.
        Use the ProviderFactory to create provider instances.

        Args:
            provider_configs (dict): A dictionary containing provider configurations.
                Each key should be a provider string (e.g., "google" or "aws-bedrock"),
                and the value should be a dictionary of configuration options for that provider.
                For example:
                {
                    "openai": {"api_key": "your_openai_api_key"},
                    "aws-bedrock": {
                        "aws_access_key": "your_aws_access_key",
                        "aws_secret_key": "your_aws_secret_key",
                        "aws_region": "us-west-2"
                    }
                }
        """
        self._closing = False
        self.session = self._setup_session()
        self.providers = {}
        self.provider_configs = provider_configs
        self._chat = None
        self._initialize_providers()

    def _setup_session(self) -> requests.Session:
        """Setup session with retries"""
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session

    def close(self):
        """Cleanup resources"""
        if not self._closing:
            self._closing = True
            if self.session:
                self.session.close()

    def __del__(self):
        """Safe cleanup on deletion"""
        if hasattr(self, '_closing') and not self._closing:
            self.close()

    def _initialize_providers(self):
        """Helper method to initialize or update providers."""
        for provider_key, config in self.provider_configs.items():
            provider_key = self._validate_provider_key(provider_key)
            self.providers[provider_key] = ProviderFactory.create_provider(
                provider_key, config
            )

    def _validate_provider_key(self, provider_key):
        """
        Validate if the provider key corresponds to a supported provider.
        """
        supported_providers = ProviderFactory.get_supported_providers()

        if provider_key not in supported_providers:
            raise ValueError(
                f"Invalid provider key '{provider_key}'. Supported providers: {supported_providers}. "
                "Make sure the model string is formatted correctly as 'provider:model'."
            )

        return provider_key

    def configure(self, provider_configs: dict = None):
        """
        Configure the client with provider configurations.
        """
        if provider_configs is None:
            return

        self.provider_configs.update(provider_configs)
        self._initialize_providers()  # NOTE: This will override existing provider instances.

    @property
    def chat(self):
        """Return the chat API interface."""
        if not self._chat:
            self._chat = ClientChat(self)
        return self._chat


class ClientChat:
    def __init__(self, client: "Client"):
        self.client = client
        self._completions = Completions(self.client)

    @property
    def completions(self):
        return self._completions


class Completions:
    def __init__(self, client: "Client"):
        self.client = client

    def create(self, model: str, messages: list, **kwargs):
        """
        Create chat completion based on the model, messages, and any extra arguments.
        """
        # Check that correct format is used
        if ":" not in model:
            raise ValueError(
                f"Invalid model format. Expected 'provider:model', got '{model}'"
            )

        # Extract the provider key from the model identifier, e.g., "google:gemini-xx"
        provider_key, model_name = model.split(":", 1)

        # Validate if the provider is supported
        supported_providers = ProviderFactory.get_supported_providers()
        if provider_key not in supported_providers:
            raise ValueError(
                f"Invalid provider key '{provider_key}'. Supported providers: {supported_providers}. "
                "Make sure the model string is formatted correctly as 'provider:model'."
            )

        # Initialize provider if not already initialized
        if provider_key not in self.client.providers:
            config = self.client.provider_configs.get(provider_key, {})
            self.client.providers[provider_key] = ProviderFactory.create_provider(
                provider_key, config
            )

        provider = self.client.providers.get(provider_key)
        if not provider:
            raise ValueError(f"Could not load provider for '{provider_key}'.")

        # Delegate the chat completion to the correct provider's implementation
        try:
            logger.info(f"Making API call to provider: {provider_key} with model: {model_name}")
            return provider.chat_completions_create(model_name, messages, **kwargs)
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise
