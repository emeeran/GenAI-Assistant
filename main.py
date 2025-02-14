import os
import logging
from typing import Any, Dict, List, Optional, TypeVar
from dataclasses import dataclass
from functools import lru_cache
import streamlit as st

from src import (
    Chat, Client, CONFIG,
    PERSONAS, DEFAULT_PERSONA, PersonaCategory  # Update imports
)
from src.utils import ChatExporter, ConfigManager
from src.provider import ProviderFactory
from dotenv import load_dotenv

# Load .env variables early in the startup
load_dotenv()

# Configure logging with more detailed settings
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)  # Define logger

T = TypeVar('T')

@st.cache_resource
class AppState:
    """Centralized state management with type safety"""
    def __init__(self):
        self.config = ConfigManager.load_config("config.json") or CONFIG
        self._init_session_state()  # Move this before client and chat initialization
        self.client = self._setup_client()
        self.chat = Chat(self.client, self.config)

    @staticmethod
    def _setup_client() -> Client:
        """Set up the client with a fallback for keys."""
        cohere_key = os.getenv("COHERE_API_KEY") or os.getenv("CO_API_KEY", "")
        xai_key = os.getenv("XAI_API_KEY") or os.getenv("XAIKEY", "")

        # Build provider dict, ensuring fallback keys
        provider_keys = {}
        for p in CONFIG["SUPPORTED_PROVIDERS"]:
            candidate_env = os.getenv(f"{p.upper()}_API_KEY")
            if p == "cohere" and not candidate_env:
                candidate_env = cohere_key
            if p == "xai" and not candidate_env:
                candidate_env = xai_key

            if candidate_env:
                provider_keys[p] = {"api_key": candidate_env}
            else:
                # Could log a warning instead, or skip if key missing
                pass

        return Client(provider_keys)

    def _init_session_state(self):
        """Initialize session state with default values"""
        if "initialized" not in st.session_state:
            st.session_state.update({
                "chat_history": [],
                "current_chat": None,
                "model": None,
                "temperature": 0.7,
                "provider": self.config["DEFAULT_PROVIDER"],
                "voice_output": "Off",
                "persona": DEFAULT_PERSONA,  # Set default persona
                "custom_persona": "",
                "edit_mode": False,
                "save_clicked": False,
                "load_clicked": False,
                "file_processed": False,
                "initialized": True
            })

def initialize_session_state(config: Dict):
    """Initialize session state with default values"""
    if "initialized" not in st.session_state:
        defaults = {
            # Basic settings
            "chat_history": [],
            "current_chat": None,
            "model": None,
            "temperature": 0.7,
            "provider": config["DEFAULT_PROVIDER"],
            "voice_output": "Off",
            "persona": DEFAULT_PERSONA,

            # UI states
            "settings_expanded": False,
            "load_expanded": False,
            "upload_expanded": False,
            "sidebar_expanded": False,
            "sidebar_rendered": False,
            "file_processed": False,

            # Chat states
            "custom_persona": "",
            "edit_mode": False,
            "save_clicked": False,
            "load_clicked": False,

            # Operation flags
            "initialized": True
        }
        st.session_state.update(defaults)
        logger.debug("Session state initialized with defaults")

def hide_streamlit_header():
    """Hide Streamlit's default header and footer"""
    hide_decoration_bar_style = '''
        <style>
            header {visibility: hidden;}
            footer {visibility: hidden;}
            #MainMenu {visibility: hidden;}
            [data-testid="stToolbar"] {visibility: hidden;}
            [data-testid="stDecoration"] {visibility: hidden;}
            [data-testid="stStatusWidget"] {visibility: hidden;}
            div.block-container {padding-top: 1rem;}
            div.block-container {padding-bottom: 1rem;}
        </style>
    '''
    st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

def main():
    """Main application entry point"""
    try:
        st.set_page_config(
            page_title="AI Chat Assistant",
            page_icon="💬",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Hide Streamlit's default header
        hide_streamlit_header()

        # Initialize session state before creating AppState
        initialize_session_state(CONFIG)
        app = AppState()
        app.chat.render_ui()

        # Add version info
        st.sidebar.markdown("---")
        st.sidebar.markdown(
            "<div style='text-align: center; color: #666;'>"
            "v1.0.0</div>",
            unsafe_allow_html=True
        )

    except Exception as e:
        logger.error(f"Application Error: {e}")
        st.error(
            "Application Error. Please try:\n"
            "1. Refresh the page\n"
            "2. Clear cache and restart\n"
            "3. Check API keys"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Cache"):
                st.cache_data.clear()
                st.cache_resource.clear()
                st.rerun()
        with col2:
            if st.button("Reset App"):
                st.session_state.clear()
                st.rerun()

if __name__ == "__main__":
    main()
