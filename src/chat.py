from dataclasses import dataclass
from typing import Dict, List
import streamlit as st
from .client import Client
from .utils import ChatExporter
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
        if not hasattr(st.session_state, "file_processed"):
            st.session_state.file_processed = False

    @st.cache_data(ttl=600, show_spinner=False)
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

                        # Collect user feedback
                        rating = st.radio("Feedback:", ["👍", "👎"], horizontal=True, key=f"feedback-{len(st.session_state.chat_history)}")
                        st.session_state.chat_history.append({"role": "assistant", "content": response, "rating": rating})

        except Exception as e:
            st.error(f"Error processing message: {str(e)}")

    def render_ui(self):
        """Render the main chat interface"""
        st.markdown(
            "<h1 style='text-align: center; color: #6ca395;'>AI Chat Assistant 💬</h1>",
            unsafe_allow_html=True
        )
        # Change rendering order and prevent duplicate rendering
        self._render_feedback()  # Render feedback first
        self._render_sidebar()   # Then render sidebar
        self._render_chat_interface()  # Finally render chat interface

    def _render_feedback(self):
        """Render aggregated user feedback statistics."""
        feedback = [msg.get("rating") for msg in st.session_state.chat_history if msg.get("rating")]
        # Remove recursive rendering calls that cause duplicate keys
        if feedback:
            thumbs_up = feedback.count("👍")
            thumbs_down = feedback.count("👎")
            st.sidebar.markdown("### Feedback Summary")
            st.sidebar.text(f"👍 {thumbs_up} | 👎 {thumbs_down}")

    def _render_sidebar(self):
        with st.sidebar:
            # Update CSS for improved button layout
            st.markdown("""
                <style>
                    section[data-testid="stSidebar"] {
                        background-color: #2E2E2E;
                        width: 300px !important;
                        padding-top: 0;
                    }
                    div[data-testid="stExpander"] {
                        background-color: #3E3E3E;
                        border-radius: 4px;
                        border: 1px solid #4A4A4A;
                        margin-bottom: 0.5rem;
                    }
                    .css-1544g2n {padding-top: 0rem;}
                    .block-container {padding: 0 !important;}

                    /* Improved button styling */
                    .stButton button {
                        width: 100% !important;
                        margin: 0.2rem 0;
                        padding: 0.25rem 0.5rem;
                        font-size: 0.85rem;
                        border-radius: 4px;
                        min-height: 2rem;
                    }

                    /* Section styling */
                    .sidebar-section {
                        background: #3E3E3E;
                        padding: 0.75rem;
                        border-radius: 4px;
                        margin: 0.75rem 0;
                    }

                    /* Header styling */
                    .sidebar-header {
                        color: #6ca395;
                        font-size: 0.9rem;
                        font-weight: 600;
                        margin-bottom: 0.5rem;
                        padding-left: 0.25rem;
                    }

                    /* Expander styling */
                    .streamlit-expanderHeader {
                        font-size: 0.9rem;
                        padding: 0.75rem;
                        background: #2E2E2E;
                    }

                    /* Column gaps */
                    .row-widget.stColumns {
                        gap: 0.5rem;
                    }

                    /* Compact button row */
                    .button-row {
                        display: flex;
                        gap: 0.5rem;
                        margin: 0.5rem 0;
                    }
                    .button-row .stButton {
                        flex: 1;
                    }
                    .button-row .stButton button {
                        width: 100% !important;
                    }

                    /* Secondary buttons */
                    .secondary-buttons {
                        display: flex;
                        gap: 0.5rem;
                    }
                    .secondary-buttons .stButton {
                        flex: 1;
                    }

                    /* More compact sections */
                    .sidebar-section {
                        background: #3E3E3E;
                        padding: 0.5rem;
                        border-radius: 4px;
                        margin: 0.5rem 0;
                    }
                </style>
            """, unsafe_allow_html=True)

            # Settings Expander
            with st.expander("Settings", expanded=False):
                # Provider Selection
                providers = sorted(ProviderFactory.get_supported_providers(self.config["SUPPORTED_PROVIDERS"]))
                provider = st.selectbox(
                    "Provider",
                    providers,
                    index=providers.index(st.session_state.provider),
                    key="settings_provider_select"
                )

                # Model Selection
                if provider and (models := self.config["MODELS"].get(provider)):
                    st.session_state.model = st.selectbox(
                        "Model",
                        models,
                        key="settings_model_select"
                    )
                    st.session_state.provider = provider

                st.markdown("---")

                # Persona Settings
                personas = tuple(PERSONAS.keys())
                selected_persona = st.selectbox(
                    "Persona",
                    personas,
                    index=personas.index(st.session_state.persona),
                    key="settings_persona_select"
                )

                if selected_persona == "Custom":
                    st.session_state.custom_persona = st.text_area(
                        "Custom Instructions",
                        value=st.session_state.custom_persona,
                        placeholder="Enter custom instructions...",
                        key="settings_custom_instructions"
                    )
                    st.session_state.persona = "Custom"
                else:
                    st.session_state.persona = selected_persona

                st.markdown("---")

                # Temperature Setting
                st.session_state.temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.temperature,
                    step=0.1,
                    help="Higher values make output more random, lower values more deterministic",
                    key="settings_temperature"
                )

            # Chat Actions with improved layout
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-header">Chat Actions</div>', unsafe_allow_html=True)

            # Primary actions in two columns
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("New", type="primary"):
                    st.session_state.chat_history = []
                    st.rerun()
            with c2:
                if st.button("Clear"):
                    st.session_state.chat_history = []
                    st.rerun()

            # Load and Save actions in same row
            st.markdown('<div class="secondary-buttons">', unsafe_allow_html=True)
            col1, col2 = st.columns([1, 1])
            with col1:
                with st.expander("Load", expanded=False):
                    self._handle_load()
            with col2:
                if st.button("Save"):
                    self._handle_save()
            st.markdown('</div>', unsafe_allow_html=True)

            # Export button
            if st.button("Export"):
                self._handle_export()
            st.markdown('</div>', unsafe_allow_html=True)

            # File Management section
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-header">File Upload</div>', unsafe_allow_html=True)
            with st.expander("Upload", expanded=False):
                self._handle_uploads()
            st.markdown('</div>', unsafe_allow_html=True)

            # Footer
            st.markdown(
                """<div class="sidebar-footer">
                    <span style='color: #888;'>Made with ❤️ using Streamlit</span>
                </div>""",
                unsafe_allow_html=True
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

            selected = st.selectbox(
                "Select chat:",
                saved_chats,
                key="sidebar_load_chat_select"  # Updated unique key with better prefix
            )
            if selected and st.button("Load Selected", key="sidebar_load_button"):  # Added unique key for button
                history = ChatExporter.load_markdown(selected)
                if history:
                    st.session_state.chat_history = history
                    st.success(f"Loaded: {selected}")
                    st.rerun()
        except Exception as e:
            st.error(f"Load failed: {e}")

    def _handle_export(self):
        """Handle export functionality"""
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

    def _render_settings(self):
        """Render settings within the chat interface"""
        with st.expander("Settings", expanded=True):
            provider = st.selectbox(
                "Select Provider",
                ["openai", "anthropic", "cohere", "groq", "xai"],
                key="settings_expander_provider"  # Updated unique key
            )

            model = st.selectbox(
                "Select Model",
                self.config["MODELS"].get(provider, []),
                key="settings_expander_model"  # Updated unique key
            )

            persona = st.selectbox(
                "Select Persona",
                list(PERSONAS.keys()),
                key="settings_expander_persona"  # Updated unique key
            )

    def _handle_uploads(self):
        """Handle file uploads"""
        uploaded_file = st.file_uploader(
            "Upload a file",
            type=["txt", "py", "js", "json", "csv", "md", "pdf"],
            help="Select a file to process"
        )

        if uploaded_file:
            file_details = f"{uploaded_file.name} ({uploaded_file.type})"
            st.text(file_details)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Process", type="primary", use_container_width=True, key="process_upload"):
                    try:
                        content = self._process_file(uploaded_file)
                        self.handle_message(f"📎 File contents:\n```\n{content}\n```")
                        st.session_state.file_processed = True
                        st.success("File processed!")
                    except Exception as e:
                        st.error(f"Error processing file: {str(e)}")
            with c2:
                if st.button("Clear", use_container_width=True, key="clear_upload"):
                    st.session_state.file_processed = False
                    st.rerun()

    def _process_file(self, uploaded_file) -> str:
        """Process uploaded file and return its contents"""
        try:
            # Read file content based on type
            if uploaded_file.type == "application/pdf":
                # Add PDF processing if needed
                return "PDF processing not implemented yet"

            # For text-based files
            content = uploaded_file.getvalue().decode('utf-8')
            # Truncate if content is too long
            max_length = 2000
            if len(content) > max_length:
                content = content[:max_length] + "\n...(truncated)"
            return content
        except Exception as e:
            raise Exception(f"Failed to process file: {str(e)}")