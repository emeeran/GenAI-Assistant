import os
import logging  # Added import for logging
from typing import Any, Dict, List, Optional, TypeVar
from dataclasses import dataclass
from functools import lru_cache
import streamlit as st
from src.utils import ChatExporter, ConfigManager
from src.client import Client
from src.provider import ProviderFactory
from src.chat import Chat
from src.config import CONFIG
from persona import PERSONAS, DEFAULT_PERSONA  # Add persona imports

# Configure logging
logging.basicConfig(level=logging.ERROR)
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
        return Client({
            p: {"api_key": os.getenv(f"{p.upper()}_API_KEY")}
            for p in CONFIG["SUPPORTED_PROVIDERS"]
            if os.getenv(f"{p.upper()}_API_KEY")
        })

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
            "chat_history": [],
            "current_chat": None,
            "model": None,
            "temperature": 0.7,
            "provider": config["DEFAULT_PROVIDER"],
            "voice_output": "Off",
            "persona": DEFAULT_PERSONA,  # Set default persona
            "custom_persona": "",
            "edit_mode": False,
            "save_clicked": False,
            "load_clicked": False,
            "file_processed": False,
            "initialized": True
        }
        st.session_state.update(defaults)

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

    except Exception as e:
        logger.error(f"Application Error: {e}")
        st.error(f"Application Error: {str(e)}")
        if st.button("Reset Application"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
