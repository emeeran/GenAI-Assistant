from typing import Dict
import streamlit as st
from .provider import ProviderFactory

def render_sidebar(config: Dict):
    """Render sidebar with configuration options"""
    with st.sidebar:
        st.markdown(
            '<h2 style="text-align: center; color: #6ca395;">Settings 🔧</h2>',
            unsafe_allow_html=True
        )

        with st.expander("Configuration", expanded=False):
            _render_provider_settings(config)
            _render_voice_settings(config)

            st.session_state.temperature = st.slider(
                "Response Creativity",
                0.0, 1.0, 0.7, 0.01
            )

        # Add theme selection
        with st.expander("Theme", expanded=False):
            theme = st.selectbox(
                "Choose Theme",
                ["Light", "Dark", "Blue"],
                index=0
            )
            _apply_theme(theme)

def _render_provider_settings(config: Dict):
    """Render model provider selection"""
    providers = sorted(ProviderFactory.get_supported_providers(config["SUPPORTED_PROVIDERS"]))
    provider = st.selectbox(
        "Provider",
        providers,
        index=providers.index(st.session_state.provider),
        key="sidebar_provider_selectbox_ui_1"  # Updated unique key
    )

    if provider and (models := config["MODELS"].get(provider)):
        st.session_state.model = st.selectbox(
            "Model",
            models,
            key="sidebar_model_selectbox_ui_1"  # Updated unique key
        )
        st.session_state.provider = provider

def _render_voice_settings(config: Dict):
    """Render voice output settings"""
    languages = ["Off"] + list(config["VOICE_LANGUAGES"].keys())
    st.session_state.voice_output = st.selectbox(
        "Voice Output",
        languages,
        index=0,
        key="voice_output_selectbox_ui_1"  # Updated unique key
    )

def _apply_theme(theme: str):
    """Apply selected theme to the application."""
    if theme == "Dark":
        st.markdown("""
            <style>
                body {
                    background-color: #2E2E2E;
                    color: #FFFFFF;
                }
            </style>
        """, unsafe_allow_html=True)
    elif theme == "Blue":
        st.markdown("""
            <style>
                body {
                    background-color: #E0F7FA;
                    color: #006064;
                }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
                body {
                    background-color: #FFFFFF;
                    color: #000000;
                }
            </style>
        """, unsafe_allow_html=True)

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
            st.rerun()Comprehensive overview of  Chennai

    with col2:
        if st.button("📝 Export Chat", use_container_width=True):
            _handle_export()

def _handle_export():
    """Handle chat export functionality"""
    if not st.session_state.chat_history:
        st.warning("No chat to export")
        return

    from .utils import ChatExporter
    try:
        export_path = ChatExporter.export_markdown(
            st.session_state.chat_history,
            "chat_export"
        )
        st.success(f"Chat exported to: {export_path}")
    except Exception as e:
        st.error(f"Export failed: {e}")
