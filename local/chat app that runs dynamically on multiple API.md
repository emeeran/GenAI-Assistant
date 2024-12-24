Following are my project for a cutting-edge streamlit chat app that runs dynamically on multiple API. Please write a robust and  compact code using Python, streamlit, SQLite, HTM, CSS, js, JSX and other required



UI Descriptions:

SIDEBAR

- in a sidebar, place a drop-down list for selecting API provider
- below that, place a drop-down list with models the selected provider API supports
- below this place a slider for Temperature
- palce two buttons on a row
  - place "Refresh" button # that refreshes current chat window
  - place "Edit" button # for editing previous prompt
- place two buttons on a  row
  - place "Save" button # when pressed ask for a name to save the chat
  - place "Load" button # pop up with saved chat names
- place "Export" # for exporting the current chat thread to markdown

CHAT WINDOW

1. place at the bottom fixed, always visible an expandable prompt input box with paper-clip icon in left corner for uploading files and arrow icon in right corner for sending
2. above this, place scrollable text box, within this print history of chat response along with its prompt neatly markdown formatted exactly more like ChatGPT web UI
3. above this, Title: "Dynamic Chat App"

FEATURES:

-  Must be context aware
- Caching enabled
- Optimized for speedy response

 

```
  demo_chat git:(develop) ✗ tree

├── pyproject.toml
├── README.md
├── requirements.txt
├── src
│   ├── client.py
│   ├── framework
│   │   ├── chat_completion_response.py
│   │   ├── choice.py
│   │   ├── __init__.py
│   │   ├── message.py
│   │   └── provider_interface.py
│   ├── __init__.py
│   ├── provider.py
│   └── providers
│       ├── anthropic_provider.py
│       ├── aws_provider.py
│       ├── azure_provider.py
│       ├── cohere_provider.py
│       ├── fireworks_provider.py
│       ├── google_provider.py
│       ├── groq_provider.py
│       ├── huggingface_provider.py
│       ├── __init__.py
│       ├── mistral_provider.py
│       ├── ollama_provider.py
│       ├── openai_provider.py
│       ├── sambanova_provider.py
│       ├── together_provider.py
│       ├── watsonx_provider.py
│       └── xai_provider.py
└── uv.lock
```



src/client.py

```python
from .provider import ProviderFactory


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
        self.providers = {}
        self.provider_configs = provider_configs
        self._chat = None
        self._initialize_providers()

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
            self._chat = Chat(self)
        return self._chat


class Chat:
    def __init__(self, client: "Client"):
        self.client = client
        self._completions = Completions(self.client)

    @property
    def completions(self):
        """Return the completions interface."""
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
        return provider.chat_completions_create(model_name, messages, **kwargs)

```

src/provide.py

```python
from abc import ABC, abstractmethod
from pathlib import Path
import importlib
import os
import functools


class LLMError(Exception):
    """Custom exception for LLM errors."""

    def __init__(self, message):
        super().__init__(message)


class Provider(ABC):
    @abstractmethod
    def chat_completions_create(self, model, messages):
        """Abstract method for chat completion calls, to be implemented by each provider."""
        pass


class ProviderFactory:
    """Factory to dynamically load provider instances based on naming conventions."""

    PROVIDERS_DIR = Path(__file__).parent / "providers"

    @classmethod
    def create_provider(cls, provider_key, config):
        """Dynamically load and create an instance of a provider based on the naming convention."""
        # Convert provider_key to the expected module and class names
        provider_class_name = f"{provider_key.capitalize()}Provider"
        provider_module_name = f"{provider_key}_provider"

        module_path = f"src.providers.{provider_module_name}"

        # Lazily load the module
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            raise ImportError(
                f"Could not import module {module_path}: {str(e)}. Please ensure the provider is supported by doing ProviderFactory.get_supported_providers()"
            )

        # Instantiate the provider class
        provider_class = getattr(module, provider_class_name)
        return provider_class(**config)

    @classmethod
    @functools.cache
    def get_supported_providers(cls):
        """List all supported provider names based on files present in the providers directory."""
        provider_files = Path(cls.PROVIDERS_DIR).glob("*_provider.py")
        return {file.stem.replace("_provider", "") for file in provider_files}

```

src.framework/chat_completion_response.py

```python
from src.framework.choice import Choice


class ChatCompletionResponse:
    """Used to conform to the response model of OpenAI"""

    def __init__(self):
        self.choices = [Choice()]  # Adjust the range as needed for more choices

```

src/framwork/choice.py

```python
from src.framework.message import Message


class Choice:
    def __init__(self):
        self.message = Message()

```

src/frmework/message.py

```python
"""Interface to hold contents of api responses when they do not confirm to the OpenAI style response"""


class Message:
    def __init__(self):
        self.content = None

        		
```

src/framework/provider_interface.py

```python
"""The shared interface for model providers."""


class ProviderInterface:
    """Defines the expected behavior for provider-specific interfaces."""

    def chat_completion_create(self, messages=None, model=None, temperature=0) -> None:
        """Create a chat completion using the specified messages, model, and temperature.

        This method must be implemented by subclasses to perform completions.

        Args:
        ----
            messages (list): The chat history.
            model (str): The identifier of the model to be used in the completion.
            temperature (float): The temperature to use in the completion.

        Raises:
        ------
            NotImplementedError: If this method has not been implemented by a subclass.

        """
        raise NotImplementedError(
            "Provider Interface has not implemented chat_completion_create()"
        )

```

src.providers/anthropic_provider.py

```python
import anthropic
from src.provider import Provider
from src.framework import ChatCompletionResponse

# Define a constant for the default max_tokens value
DEFAULT_MAX_TOKENS = 4096


class AnthropicProvider(Provider):
    def __init__(self, **config):
        """
        Initialize the Anthropic provider with the given configuration.
        Pass the entire configuration dictionary to the Anthropic client constructor.
        """

        self.client = anthropic.Anthropic(**config)

    def chat_completions_create(self, model, messages, **kwargs):
        # Check if the fist message is a system message
        if messages[0]["role"] == "system":
            system_message = messages[0]["content"]
            messages = messages[1:]
        else:
            system_message = []

        # kwargs.setdefault('max_tokens', DEFAULT_MAX_TOKENS)
        if "max_tokens" not in kwargs:
            kwargs["max_tokens"] = DEFAULT_MAX_TOKENS

        return self.normalize_response(
            self.client.messages.create(
                model=model, system=system_message, messages=messages, **kwargs
            )
        )

    def normalize_response(self, response):
        """Normalize the response from the Anthropic API to match OpenAI's response format."""
        normalized_response = ChatCompletionResponse()
        normalized_response.choices[0].message.content = response.content[0].text
        return normalized_response

```

sc/provider/cohere_provider.py

````py
import os
import cohere

from src.framework import ChatCompletionResponse
from src.provider import Provider


class CohereProvider(Provider):
    def __init__(self, **config):
        """
        Initialize the Cohere provider with the given configuration.
        Pass the entire configuration dictionary to the Cohere client constructor.
        """
        # Ensure API key is provided either in config or via environment variable
        config.setdefault("api_key", os.getenv("CO_API_KEY"))
        if not config["api_key"]:
            raise ValueError(
                " API key is missing. Please provide it in the config or set the CO_API_KEY environment variable."
            )
        self.client = cohere.ClientV2(**config)

    def chat_completions_create(self, model, messages, **kwargs):
        response = self.client.chat(
            model=model,
            messages=messages,
            **kwargs  # Pass any additional arguments to the Cohere API
        )

        return self.normalize_response(response)

    def normalize_response(self, response):
        """Normalize the reponse from Cohere API to match OpenAI's response format."""
        normalized_response = ChatCompletionResponse()
        normalized_response.choices[0].message.content = response.message.content[
            0
        ].text
        return normalized_response

````

src/provider/google_provider.py

```pyttho
"""The interface to Google's Vertex AI."""

import os

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

from src.framework import ProviderInterface, ChatCompletionResponse


DEFAULT_TEMPERATURE = 0.7


class GoogleProvider(ProviderInterface):
    """Implements the ProviderInterface for interacting with Google's Vertex AI."""

    def __init__(self, **config):
        """Set up the Google AI client with a project ID."""
        self.project_id = config.get("project_id") or os.getenv("GOOGLE_PROJECT_ID")
        self.location = config.get("region") or os.getenv("GOOGLE_REGION")
        self.app_creds_path = config.get("application_credentials") or os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )

        if not self.project_id or not self.location or not self.app_creds_path:
            raise EnvironmentError(
                "Missing one or more required Google environment variables: "
                "GOOGLE_PROJECT_ID, GOOGLE_REGION, GOOGLE_APPLICATION_CREDENTIALS. "
                "Please refer to the setup guide: /guides/google.md."
            )

        vertexai.init(project=self.project_id, location=self.location)

    def chat_completions_create(self, model, messages, **kwargs):
        """Request chat completions from the Google AI API.

        Args:
        ----
            model (str): Identifies the specific provider/model to use.
            messages (list of dict): A list of message objects in chat history.
            kwargs (dict): Optional arguments for the Google AI API.

        Returns:
        -------
            The ChatCompletionResponse with the completion result.

        """

        # Set the temperature if provided, otherwise use the default
        temperature = kwargs.get("temperature", DEFAULT_TEMPERATURE)

        # Transform the roles in the messages
        transformed_messages = self.transform_roles(messages)

        # Convert the messages to the format expected Google
        final_message_history = self.convert_openai_to_vertex_ai(
            transformed_messages[:-1]
        )

        # Get the last message from the transformed messages
        last_message = transformed_messages[-1]["content"]

        # Create the GenerativeModel with the specified model and generation configuration
        model = GenerativeModel(
            model, generation_config=GenerationConfig(temperature=temperature)
        )

        # Start a chat with the GenerativeModel and send the last message
        chat = model.start_chat(history=final_message_history)
        response = chat.send_message(last_message)

        # Convert the response to the format expected by the OpenAI API
        return self.normalize_response(response)

    def convert_openai_to_vertex_ai(self, messages):
        """Convert OpenAI messages to Google AI messages."""
        from vertexai.generative_models import Content, Part

        history = []
        for message in messages:
            role = message["role"]
            content = message["content"]
            parts = [Part.from_text(content)]
            history.append(Content(role=role, parts=parts))
        return history

    def transform_roles(self, messages):
        """Transform the roles in the messages based on the provided transformations."""
        openai_roles_to_google_roles = {
            "system": "user",
            "assistant": "model",
        }

        for message in messages:
            if role := openai_roles_to_google_roles.get(message["role"], None):
                message["role"] = role
        return messages

    def normalize_response(self, response):
        """Normalize the response from Google AI to match OpenAI's response format."""
        openai_response = ChatCompletionResponse()
        openai_response.choices[0].message.content = (
            response.candidates[0].content.parts[0].text
        )
        return openai_response


```

src/providers/groq_provider.py

```pyth
import os

import groq
from src.provider import Provider


class GroqProvider(Provider):
    def __init__(self, **config):
        """
        Initialize the Groq provider with the given configuration.
        Pass the entire configuration dictionary to the Groq client constructor.
        """
        # Ensure API key is provided either in config or via environment variable
        config.setdefault("api_key", os.getenv("GROQ_API_KEY"))
        if not config["api_key"]:
            raise ValueError(
                " API key is missing. Please provide it in the config or set the GROQ_API_KEY environment variable."
            )
        self.client = groq.Groq(**config)

    def chat_completions_create(self, model, messages, **kwargs):
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs  # Pass any additional arguments to the Groq API
        )

```

src/providers/openai_provider.py

```pytho
import os

import groq
from src.provider import Provider


class GroqProvider(Provider):
    def __init__(self, **config):
        """
        Initialize the Groq provider with the given configuration.
        Pass the entire configuration dictionary to the Groq client constructor.
        """
        # Ensure API key is provided either in config or via environment variable
        config.setdefault("api_key", os.getenv("GROQ_API_KEY"))
        if not config["api_key"]:
            raise ValueError(
                " API key is missing. Please provide it in the config or set the GROQ_API_KEY environment variable."
            )
        self.client = groq.Groq(**config)

    def chat_completions_create(self, model, messages, **kwargs):
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs  # Pass any additional arguments to the Groq API
        )

```

src/provider/xai_provider.py

```python
import os
import httpx
from src.provider import Provider, LLMError
from src.framework import ChatCompletionResponse


class XaiProvider(Provider):
    """
    xAI Provider using httpx for direct API calls.
    """

    BASE_URL = "https://api.x.ai/v1/chat/completions"

    def __init__(self, **config):
        """
        Initialize the xAI provider with the given configuration.
        The API key is fetched from the config or environment variables.
        """
        self.api_key = config.get("api_key", os.getenv("XAI_API_KEY"))
        if not self.api_key:
            raise ValueError(
                "xAI API key is missing. Please provide it in the config or set the XAI_API_KEY environment variable."
            )

        # Optionally set a custom timeout (default to 30s)
        self.timeout = config.get("timeout", 30)

    def chat_completions_create(self, model, messages, **kwargs):
        """
        Makes a request to the xAI chat completions endpoint using httpx.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": model,
            "messages": messages,
            **kwargs,  # Pass any additional arguments to the API
        }

        try:
            # Make the request to xAI endpoint.
            response = httpx.post(
                self.BASE_URL, json=data, headers=headers, timeout=self.timeout
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as http_err:
            raise LLMError(f"xAI request failed: {http_err}")
        except Exception as e:
            raise LLMError(f"An error occurred: {e}")

        # Return the normalized response
        return self._normalize_response(response.json())

    def _normalize_response(self, response_data):
        """
        Normalize the response to a common format (ChatCompletionResponse).
        """
        normalized_response = ChatCompletionResponse()
        normalized_response.choices[0].message.content = response_data["choices"][0][
            "message"
        ]["content"]
        return normalized_response

```

