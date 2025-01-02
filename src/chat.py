from dataclasses import dataclass
from typing import Dict, List, Optional
import streamlit as st
from .client import Client
from .utils import ChatExporter
from .audio import play_audio, generate_audio
from .provider import ProviderFactory
from persona import PERSONAS, DEFAULT_PERSONA  # Fix relative import

@dataclass
class ChatMessage:
    role: str
    content: str


    def to_dict(self) -> Dict:
        """Convert ChatMessage to dictionary for JSON serialization"""
        return {
            "role": self.role,
            "content": self.content
        }

    @staticmethod
    def from_dict(data: Dict) -> 'ChatMessage':
        """Create ChatMessage from dictionary"""
        return ChatMessage(
            role=data["role"],
            content=data["content"]
        )

class Chat:
    """Handles chat functionality and UI rendering"""

    def __init__(self, client: Client, config: Dict):
        self.client = client
        self.config = config
        self._ensure_session_state()

    def _ensure_session_state(self):
        """Ensure all required session state variables exist"""
        if not hasattr(st.session_state, "provider"):
            st.session_state.provider = self.config["DEFAULT_PROVIDER"]
        if not hasattr(st.session_state, "model"):
            st.session_state.model = None
        if not hasattr(st.session_state, "voice_output"):
            st.session_state.voice_output = "Off"

    @st.cache_data(ttl=600)
    def generate_response(_self, messages: List[Dict], temperature: float) -> str:
        """Generate response with caching"""
        try:
            response = _self.client.chat.completions.create(
                model=f"{st.session_state.provider}:{st.session_state.model}",
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"Failed to generate response: {str(e)}")
            return ""

    def handle_message(self, prompt: str):
        """Process user message and generate response"""
        if not st.session_state.model:
            st.warning("Please select a model first")
            return

        try:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Generating response..."):
                    response = self.generate_response(
                        self._build_messages(prompt),
                        st.session_state.temperature
                    )

                    if response:
                        st.markdown(response)
                        if st.session_state.voice_output != "Off":
                            gender = st.session_state.get("voice_gender", "Male")
                            play_audio(response, st.session_state.voice_output, gender)

                        self._update_history(prompt, response)

        except Exception as e:
            st.error(f"Error processing message: {str(e)}")

    def render_ui(self):
        """Render the main chat interface"""
        st.markdown(
            "<h1 style='text-align: center'>AI Chat Assistant 💬</h1>",
            unsafe_allow_html=True
        )

        self._render_sidebar()
        self._render_chat_interface()

    def _render_sidebar(self):
        with st.sidebar:
            # Add custom CSS for more compact sidebar
            st.markdown("""
                <style>
                    section[data-testid="stSidebar"] {
                        background-color: #2E2E2E;
                        width: 320px !important;
                        padding-top: 0;
                    }
                    div[data-testid="stExpander"] {
                        background-color: #3E3E3E;
                        border-radius: 4px;
                        border: 1px solid #4A4A4A;
                        margin-bottom: 0.5rem;
                    }
                    .css-1544g2n {
                        padding-top: 0rem;
                    }
                    .block-container {
                        padding: 0 !important;
                    }
                    section[data-testid="stSidebar"] > div {
                        padding-top: 1rem;
                    }
                    section[data-testid="stSidebar"] .block-container {
                        margin-top: -4rem;
                    }
                    /* Rest of your existing styles */
                </style>
            """, unsafe_allow_html=True)

            # Combined Settings Section
            with st.expander("⚙️ Settings", expanded=False):
                # Model Settings
                self._render_provider_settings()

                # Audio Settings
                st.markdown("---")
                audio_enabled = st.radio(
                    "Text-to-Speech",  # Restore label
                    ["Disabled", "Enabled"],
                    index=0 if st.session_state.voice_output == "Off" else 1,
                    horizontal=True
                )

                if audio_enabled == "Enabled":
                    col1, col2 = st.columns(2)
                    with col1:
                        st.session_state.voice_output = st.selectbox(
                            "Language",  # Restore label
                            ["English", "Tamil"]
                        )
                    with col2:
                        st.session_state.voice_gender = st.radio(
                            "Voice",  # Restore label
                            ["Male", "Female"],
                            horizontal=True
                        )
                else:
                    st.session_state.voice_output = "Off"

            # Action Buttons (without header)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("New Chat", use_container_width=True, type="primary"):
                    st.session_state.chat_history = []
                    st.rerun()
                if st.button("Save", use_container_width=True):
                    self._handle_save()
            with c2:
                if st.button("Load", use_container_width=True):
                    self._handle_load()
                if st.button("Export", use_container_width=True):
                    self._handle_export()

            # File Upload (without header)
            with st.expander("📂 Upload", expanded=False):
                uploaded_file = st.file_uploader(
                    "Upload File",  # Restore label
                    type=["txt", "py", "js", "json", "csv", "md", "pdf"]
                )
                # ...rest of upload handling...

            # Footer
            st.markdown(
                """
                <div class="sidebar-footer">
                    <span style='color: #888;'>Made with ❤️ using Streamlit</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    def _render_provider_settings(self):
        """Render provider and model selection"""
        providers = sorted(ProviderFactory.get_supported_providers(self.config["SUPPORTED_PROVIDERS"]))

        provider = st.selectbox(
            "Provider",  # Restore label
            providers,
            index=providers.index(st.session_state.provider)
        )

        if provider and (models := self.config["MODELS"].get(provider)):
            st.session_state.model = st.selectbox(
                "Model",  # Restore label
                models
            )
            st.session_state.provider = provider

        # Add Persona Settings
        st.markdown("---")
        personas = tuple(PERSONAS.keys())
        selected_persona = st.selectbox(
            "Persona",  # Restore label
            personas,
            index=personas.index(st.session_state.persona)
        )

        if selected_persona == "Custom":
            st.session_state.custom_persona = st.text_area(
                "Custom Instructions",  # Restore label
                value=st.session_state.custom_persona,
                placeholder="Enter custom instructions..."
            )
            st.session_state.persona = "Custom"
        else:
            st.session_state.persona = selected_persona

        # Temperature Setting
        st.markdown("---")
        st.session_state.temperature = st.slider(
            "Creativity",  # Restore label
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.temperature,
            step=0.1
        )

    def _build_messages(self, prompt: str) -> List[Dict]:
        """Build message history for API request"""
        return (
            [{"role": "system", "content": st.session_state.get("persona", "")}]
            + st.session_state.chat_history
            + [{"role": "user", "content": prompt}]
        )

    def _update_history(self, prompt: str, response: str):
        """Update chat history with new messages"""
        messages = [
            ChatMessage("user", prompt),
            ChatMessage("assistant", response)
        ]
        st.session_state.chat_history.extend([msg.to_dict() for msg in messages])

    def _render_chat_interface(self):
        """Render main chat interface"""
        # Display chat history
        for msg in st.session_state.chat_history:
            # Convert dict to ChatMessage if needed
            if isinstance(msg, dict):
                msg = ChatMessage.from_dict(msg)
            with st.chat_message(msg.role):
                st.markdown(msg.content)

        # Chat input
        if prompt := st.chat_input("Enter your message"):
            self.handle_message(prompt)

    def _handle_save(self):
        """Handle save functionality"""
        name = st.text_input("Enter chat name:")
        if name and st.button("Confirm Save"):
            try:
                # Convert ChatMessage objects to dicts before saving
                history = [
                    msg if isinstance(msg, dict) else msg.to_dict()
                    for msg in st.session_state.chat_history
                ]
                export_path = ChatExporter.export_markdown(history, name)
                st.success(f"Chat saved as: {name}")
                st.rerun()
            except Exception as e:
                st.error(f"Save failed: {e}")

    def _handle_load(self):
        """Handle load functionality"""
        try:
            saved_chats = ChatExporter.get_saved_chats()
            if not saved_chats:
                st.warning("No saved chats found")
                return

            selected = st.selectbox("Select chat:", saved_chats)
            if selected and st.button("Load Selected"):
                history = ChatExporter.load_markdown(selected)
                if history:
                    st.session_state.chat_history = history
                    st.success(f"Loaded: {selected}")
                    st.rerun()  # Force UI refresh
        except Exception as e:
            st.error(f"Load failed: {e}")

    def _handle_uploads(self):
        """Handle file uploads"""
        uploaded_file = st.file_uploader(
            "Upload File",  # Keep meaningful label
            type=["txt", "py", "js", "json", "csv", "md", "pdf"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            col1, col2 = st.columns(2)
            with col1:
                process_button = st.button("Process File", use_container_width=True)
            with col2:
                clear_button = st.button("Clear", use_container_width=True)

            if process_button and not st.session_state.get('file_processed'):
                try:
                    content = self._process_file(uploaded_file)
                    if content:
                        st.session_state.file_processed = True
                        self.handle_message(f"📎 {uploaded_file.name}:\n\n```\n{content}\n```")

                except Exception as e:
                    st.error(f"Upload failed: {e}")

            if clear_button:
                st.session_state.file_processed = False
                st.rerun()

    def _handle_export(self):
        """Handle chat export functionality"""
        if not st.session_state.chat_history:
            st.warning("No chat to export")
            return

        try:
            export_path = ChatExporter.export_markdown(
                st.session_state.chat_history,
                "chat_export"
            )
            st.success(f"Chat exported to: {export_path}")
        except Exception as e:
            st.error(f"Export failed: {e}")
