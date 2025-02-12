import streamlit as st
from typing import Callable, Any
from functools import wraps

def cached_component(ttl_seconds: int = 3600):
    """Cache decorator for Streamlit components"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            if cache_key in st.session_state:
                return st.session_state[cache_key]
            result = func(*args, **kwargs)
            st.session_state[cache_key] = result
            return result
        return wrapper
    return decorator

class ChatUI:
    """Reusable chat UI components"""
    @staticmethod
    @cached_component(ttl_seconds=60)
    def message_box(message: str, role: str) -> None:
        with st.chat_message(role):
            st.markdown(message)

    @staticmethod
    def input_area() -> str:
        return st.chat_input("Enter your message...")

    @staticmethod
    def file_uploader(label: str, types: list) -> Any:
        return st.sidebar.file_uploader(label, type=types)
