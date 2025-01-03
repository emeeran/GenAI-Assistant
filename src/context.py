from typing import List, Dict, Optional
import json
from pathlib import Path
import streamlit as st

class ContextManager:
    def __init__(self, max_context_length: int = 10):
        self.max_context_length = max_context_length
        self._init_context_state()

    def _init_context_state(self):
        """Initialize context-related session state"""
        if "context_history" not in st.session_state:
            st.session_state.context_history = []
        if "context_topics" not in st.session_state:
            st.session_state.context_topics = set()

    def add_to_context(self, message: Dict):
        """Add message to context history"""
        st.session_state.context_history.append(message)
        if len(st.session_state.context_history) > self.max_context_length:
            st.session_state.context_history.pop(0)

    def get_relevant_context(self, query: str) -> List[Dict]:
        """Get relevant context for the query"""
        # Simple relevance by recent history
        return st.session_state.context_history[-5:]

    def extract_topics(self, text: str) -> List[str]:
        """Extract main topics from text"""
        # Implement topic extraction logic
        return []

    def clear_context(self):
        """Clear context history"""
        st.session_state.context_history = []
        st.session_state.context_topics = set()
