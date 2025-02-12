from typing import Dict, Optional, Any
from dataclasses import dataclass
from ..database.models import Message, Chat
from ..utils.caching import TTLCache

@dataclass
class Response:
    """Standardized response object"""
    content: str
    metadata: Dict[str, Any] = None
    error: Optional[str] = None

class BaseProvider:
    """Base class for AI providers"""
    def __init__(self, api_key: str, cache: Optional[TTLCache] = None):
        self.api_key = api_key
        self.cache = cache or TTLCache()

    async def generate_response(self, messages: list[Message]) -> Response:
        """Generate response from messages"""
        raise NotImplementedError
