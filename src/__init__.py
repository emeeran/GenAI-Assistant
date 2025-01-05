"""
GenAI Assistant package initialization.
"""
from typing import Dict, List, Optional, Any
from .client import Client
from .chat import Chat
from .provider import ProviderFactory
from .config import CONFIG
from .persona import PERSONAS, DEFAULT_PERSONA, PersonaCategory

__all__ = [
    'Client',
    'Chat',
    'ProviderFactory',
    'CONFIG',
    'PERSONAS',
    'DEFAULT_PERSONA',
    'PersonaCategory'
]
