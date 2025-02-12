from typing import Dict, Optional, Any
from ..database import DB
from ..client import Client
from ..utils import FileHandler, ContentManager, ThreadManager
from ..config import CONFIG

class Chat:
    def __init__(self, config: Optional[Dict] = None, client: Optional[Any] = None):
        """Initialize chat with optional configuration and client"""
        self._init_session_state()
        self.config = config or CONFIG
        self.db = DB(str(self.config["DB_PATH"]))
        self.client = client or self._setup_client()
        self.file_handler = FileHandler()
        self.content_manager = ContentManager()
        self.thread_manager = ThreadManager()

    # Move existing Chat class methods here, organized by functionality
