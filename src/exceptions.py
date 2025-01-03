class AssistantError(Exception):
    """Base exception for the assistant."""
    pass

class ProviderError(AssistantError):
    """Raised when there's an issue with the AI provider."""
    pass

class ConfigurationError(AssistantError):
    """Raised when there's a configuration issue."""
    pass

class StorageError(AssistantError):
    """Raised when there's an issue with data storage."""
    pass
