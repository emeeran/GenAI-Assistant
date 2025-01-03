from typing import Dict
import streamlit as st
from .provider import ProviderFactory

def render_sidebar(config: Dict):
    """Replicate the sidebar UI from chat.py (or app.py)."""
    with st.sidebar:
        st.markdown("""
            <style>
                section[data-testid="stSidebar"] {
                    width: 300px !important;
                    background-color: #2E2E2E;
                }
                .stButton button {
                    width: 100%;
                    padding: 0.25rem;
                    font-size: 0.85rem;
                }
                div.sidebar-section {
                    background: #3E3E3E;
                    padding: 0.75rem;
                    border-radius: 4px;
                    margin: 0.5rem 0;
                }
                div.sidebar-header {
                    color: #6ca395;
                    font-size: 0.9rem;
                    font-weight: 600;
                    margin-bottom: 0.5rem;
                }
            </style>
        """, unsafe_allow_html=True)

        # Settings Section
        with st.expander("⚙️ Settings", expanded=False):
            provider = st.selectbox(
                "Provider",
                sorted(ProviderFactory.get_supported_providers(config["SUPPORTED_PROVIDERS"])),
                key="provider_select"
            )
            if provider and (models := config["MODELS"].get(provider)):
                model = st.selectbox("Model", models, key="model_select")
                st.session_state.provider = provider
                st.session_state.model = model

            st.slider("Temperature", 0.0, 1.0, 0.7, 0.1, key="temp_slider")

        # Chat Actions
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">Chat</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("New Chat", type="primary"):
                st.session_state.chat_history = []
                st.rerun()
        with c2:
            if st.button("Clear"):
                st.session_state.chat_history = []
                st.rerun()

        # File Operations
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">Files</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Save Chat"):
                _handle_save()
        with c2:
            if st.button("Export"):
                _handle_export()

        with st.expander("Load Chat", expanded=False):
            _handle_load()

        st.markdown('</div>', unsafe_allow_html=True)

def _handle_save():
    """Placeholder for save functionality."""
    st.info("Implement _handle_save() in ui.py or reuse from chat.py")

def _handle_export():
    """Placeholder for export functionality."""
    st.info("Implement _handle_export() in ui.py or reuse from chat.py")

def _handle_load():
    """Placeholder for load functionality."""
    st.info("Implement _handle_load() in ui.py or reuse from chat.py")

def render_chat_interface(chat_instance):
    """Render main chat interface"""
    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg.role):
            st.markdown(msg.content)

    # Chat input
    if prompt := st.chat_input("Enter your message"):
        chat_instance.handle_message(prompt)

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    with col2:
        if st.button("📝 Export Chat", use_container_width=True):
            _handle_export()
