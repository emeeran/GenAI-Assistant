from dataclasses import dataclass
from typing import Dict, List
import streamlit as st
from .client import Client
from .utils import ChatExporter
from .provider import ProviderFactory
from persona import PERSONAS, DEFAULT_PERSONA  # Fix relative import
import asyncio
import logging
from .context import ContextManager
from .offline import OfflineStorage
import streamlit as st

# Configure logger
logger = logging.getLogger(__name__)

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
        self.context_manager = ContextManager()
        self.offline_storage = OfflineStorage()
        self._check_connectivity()

    def _ensure_session_state(self):
        """Ensure all required session state variables exist"""
        if not hasattr(st.session_state, "provider"):
            st.session_state.provider = self.config["DEFAULT_PROVIDER"]
        if not hasattr(st.session_state, "model"):
            st.session_state.model = None
        if not hasattr(st.session_state, "file_processed"):
            st.session_state.file_processed = False
        if not hasattr(st.session_state, "chat_title"):
            st.session_state.chat_title = "New Chat"
        if not hasattr(st.session_state, "error_count"):
            st.session_state.error_count = 0

    def _check_connectivity(self):
        """Check internet connectivity"""
        try:
            # Simple connectivity check
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            st.session_state.is_offline = False
        except OSError:
            st.session_state.is_offline = True

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

    def generate_response(self, messages: List[Dict], temperature: float) -> str:
        """Generate response with retry for 429 errors."""
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=f"{st.session_state.provider}:{st.session_state.model}",
                    messages=messages,
                    temperature=temperature
                )
                return response.choices[0].message.content
            except Exception as e:
                err_msg = str(e)
                if "429 Too Many Requests" in err_msg:
                    logger.warning(f"Rate-limited. Retry {attempt+1}/{max_retries}...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Response generation error: {err_msg}")
                    return "I'm having trouble generating a response. Please try again."
        return "Too many rate-limit errors from xAI. Please wait and try again."

    async def generate_streaming_response(self, messages: List[Dict], temperature: float) -> str:
        """Generate response asynchronously"""
        try:
            response = self.client.chat.completions.create(
                model=f"{st.session_state.provider}:{st.session_state.model}",
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Response generation error: {str(e)}")
            return "I'm having trouble generating a response. Please try again."

    def handle_message(self, prompt: str):
        """Process user message and generate response"""
        if not prompt.strip():
            st.warning("Please enter a message")
            return

        if not st.session_state.model:
            with st.sidebar:
                st.error("Please select a model in Settings")
            return

        try:
            with st.chat_message("user"):
                st.markdown(prompt)
                # Add user message to history immediately
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": prompt
                })

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Use synchronous response generation
                    response = self.generate_response(
                        self._build_messages(prompt),
                        st.session_state.temperature
                    )

                    if response:
                        st.markdown(response)
                        # Add assistant response to history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response
                        })
                        self._collect_feedback(response)

        except Exception as e:
            logger.error(f"Message processing error: {str(e)}")
            st.error("Failed to process message. Please try again.")

    def _get_offline_response(self, prompt: str) -> str:
        """Get response in offline mode"""
        if cached := self.offline_storage.get_offline_response(prompt):
            return cached
        return "I'm currently in offline mode and don't have a cached response for this query."

    def _update_context(self, prompt: str, response: str):
        """Update context with new message pair"""
        self.context_manager.add_to_context({
            "role": "user",
            "content": prompt
        })
        self.context_manager.add_to_context({
            "role": "assistant",
            "content": response
        })

    def _collect_feedback(self, response: str):
        """Collect user feedback"""
        rating = st.radio(
            "Feedback:",
            ["👍", "👎"],
            horizontal=True,
            key=f"feedback-{len(st.session_state.chat_history)}"
        )
        # Update the last assistant message with feedback
        if st.session_state.chat_history:
            last_msg = st.session_state.chat_history[-1]
            if last_msg["role"] == "assistant":
                last_msg["rating"] = rating

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
            # Update CSS to include inner box labels
            st.markdown("""
                <style>
                    section[data-testid="stSidebar"] {
                        width: 260px !important;
                        background-color: #2E2E2E;
                        padding: 0.5rem;
                    }
                    .stButton button {
                        width: 100%;
                        padding: 0.15rem;
                        font-size: 0.8rem;
                        min-height: 1.5rem;
                        margin: 0.1rem 0;
                    }
                    div.sidebar-section {
                        background: #3E3E3E;
                        padding: 0.4rem;
                        border-radius: 4px;
                        margin: 0.2rem 0;
                    }
                    /* Remove dividers */
                    hr {display: none !important;}
                    .css-12w0qpk {display: none;}

                    /* Compact selectors and inputs */
                    .stSelectbox > div > div {
                        padding: 0.2rem;
                        min-height: 1.5rem;
                    }
                    .stSlider {margin: 0.5rem 0;}

                    /* Box label styling */
                    .box-label {
                        color: #6ca395;
                        font-size: 0.7rem;
                        margin-bottom: 0.3rem;
                        padding: 0.1rem 0.3rem;
                        border-bottom: 1px solid #4A4A4A;
                    }

                    /* Compact content padding */
                    .content-box {
                        padding: 0.3rem;
                        margin-top: 0.2rem;
                    }
                </style>
            """, unsafe_allow_html=True)

            # Settings Section
            with st.expander("⚙️", expanded=False):
                st.markdown('<div class="box-label">Model Settings</div>', unsafe_allow_html=True)
                with st.container():
                    # Pre-select Groq
                    provider = st.selectbox(
                        "Provider",
                        sorted(ProviderFactory.get_supported_providers(self.config["SUPPORTED_PROVIDERS"])),
                        index=sorted(self.config["SUPPORTED_PROVIDERS"]).index("groq"),  # Force Groq selection
                        key="provider_select",
                        label_visibility="collapsed"
                    )

                    if provider and (models := self.config["MODELS"].get(provider)):
                        model = st.selectbox(
                            "Model",
                            models,
                            index=0,  # Select first Groq model by default
                            key="model_select",
                            label_visibility="collapsed"
                        )
                        st.session_state.provider = provider
                        st.session_state.model = model

                    # Temperature slider
                    st.markdown('<div class="box-label">Temperature</div>', unsafe_allow_html=True)
                    st.slider("T", 0.0, 1.0, 0.7, 0.1,
                        key="temp_slider",
                        label_visibility="collapsed"
                    )

            # Chat Actions
            c1, c2 = st.columns(2)
            with c1:
                st.button("New", type="primary", use_container_width=True)
            with c2:
                st.button("Clear", use_container_width=True)

            # File Operations
            c1, c2 = st.columns(2)
            with c1:
                st.button("Save", use_container_width=True)
            with c2:
                st.button("Export", use_container_width=True)

            # Load Chat with label
            with st.expander("📂", expanded=False):
                st.markdown('<div class="box-label">Load Chat</div>', unsafe_allow_html=True)
                self._handle_load()

            # File Upload with label
            with st.expander("📄", expanded=False):
                st.markdown('<div class="box-label">Upload File</div>', unsafe_allow_html=True)
                self._handle_uploads()

            # Mini footer
            st.markdown(
                """<div style='text-align: center; color: #666; font-size: 0.7rem;
                margin-top: 0.5rem;'>v1.0.0</div>""",
                unsafe_allow_html=True
            )

    def _build_messages(self, prompt: str) -> List[Dict]:
        """Exclude 'rating' to avoid invalid_request_error."""
        safe_history = []
        for msg in st.session_state.chat_history:
            safe_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        return (
            [{"role": "system", "content": st.session_state.get("persona", "")}]
            + safe_history
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
        """Render main chat interface with pagination"""
        messages_per_page = self.config.get("MESSAGES_PER_PAGE", 10)
        page = st.session_state.get('page', 0)

        total_messages = len(st.session_state.chat_history)
        total_pages = (total_messages - 1) // messages_per_page + 1

        start_idx = page * messages_per_page
        end_idx = min(start_idx + messages_per_page, total_messages)

        # Display paginated messages
        for msg in st.session_state.chat_history[start_idx:end_idx]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Pagination controls
        if total_pages > 1:
            cols = st.columns([1, 2, 2, 2, 1])
            with cols[1]:
                if st.button("◀️", disabled=page==0, key="prev_page"):
                    st.session_state.page = max(0, page - 1)
                    st.rerun()
            with cols[2]:
                st.write(f"Page {page + 1}/{total_pages}")
            with cols[3]:
                if st.button("▶️", disabled=page==total_pages-1, key="next_page"):
                    st.session_state.page = min(total_pages - 1, page + 1)
                    st.rerun()

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
            # Get saved chats directly from ChatExporter class method
            saved_chats = ChatExporter.get_saved_chats()
            if not saved_chats:
                st.warning("No saved chats found")
                return

            selected = st.selectbox(
                "Select chat:",
                saved_chats,
                key="sidebar_load_chat_select"
            )
            if selected and st.button("Load Selected", key="sidebar_load_button"):
                # Use class method to load chat
                history = ChatExporter.load_markdown(selected)
                if history:
                    st.session_state.chat_history = history
                    st.success(f"Loaded: {selected}")
                    st.rerun()
        except Exception as e:
            st.error(f"Load failed: {str(e)}")
            logger.error(f"Load error: {str(e)}")

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