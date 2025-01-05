from dataclasses import dataclass
from typing import Dict, List
import streamlit as st
import logging
import socket
import time
from .client import Client
from .utils import ChatExporter
from .provider import ProviderFactory
from .context import ContextManager
from .offline import OfflineStorage
from .persona import PERSONAS, DEFAULT_PERSONA

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    role: str
    content: str

    def to_dict(self) -> Dict: return {"role": self.role, "content": self.content}
    @staticmethod
    def from_dict(data: Dict) -> 'ChatMessage': return ChatMessage(**data)

class Chat:
    def __init__(self, client: Client, config: Dict):
        self.client = client
        self.config = config
        self.context_manager = ContextManager()
        self.offline_storage = OfflineStorage()
        self._init_session()

    def _init_session(self):
        """Initialize session state variables"""
        defaults = {
            "provider": self.config["DEFAULT_PROVIDER"],
            "model": None,
            "file_processed": False,
            "chat_title": "New Chat",
            "error_count": 0,
            "chat_history": [],
            "page": 0,
            "is_offline": not self._check_connectivity(),
            "persona": PERSONAS[DEFAULT_PERSONA]  # Add default persona
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def _check_connectivity(self) -> bool:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def generate_response(self, messages: List[Dict], temperature: float) -> str:
        """Generate response with exponential backoff retry"""
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=f"{st.session_state.provider}:{st.session_state.model}",
                    messages=messages,
                    temperature=temperature
                )
                return response.choices[0].message.content
            except Exception as e:
                wait_time = 2 ** attempt
                if "429" in str(e):
                    time.sleep(wait_time)
                    continue
                logger.error(f"Response error: {str(e)}")
                return "I'm having trouble generating a response. Please try again."
        return "Service temporarily unavailable. Please try again later."

    def handle_message(self, prompt: str):
        if not prompt.strip():
            st.warning("Please enter a message")
            return
        if not st.session_state.model:
            st.sidebar.error("Please select a model in Settings")
            return

        try:
            with st.chat_message("user"):
                st.markdown(prompt)
                st.session_state.chat_history.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = self.generate_response(
                        self._build_messages(prompt),
                        st.session_state.get("temperature", 0.7)  # Added default fallback
                    )
                    if response:
                        st.markdown(response)
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": response}
                        )
                        self._collect_feedback()
        except Exception as e:
            logger.error(f"Message error: {str(e)}")
            st.error("Failed to process message")

    # ...existing code for UI rendering methods...

    def _build_messages(self, prompt: str) -> List[Dict]:
        return (
            [{"role": "system", "content": st.session_state.get("persona", "")}] +
            [{"role": m["role"], "content": m["content"]}
             for m in st.session_state.chat_history] +
            [{"role": "user", "content": prompt}]
        )

    def _process_file(self, file) -> str:
        try:
            content = file.getvalue().decode('utf-8')
            return content[:2000] + "\n...(truncated)" if len(content) > 2000 else content
        except Exception as e:
            raise Exception(f"File processing failed: {str(e)}")

    def render_ui(self):
        """Render the main chat interface"""
        st.markdown(
            "<h1 style='text-align: center; color: #6ca395;'>AI Chat Assistant 💬</h1>",
            unsafe_allow_html=True
        )

        # Render components in correct order
        self._render_sidebar()
        self._render_chat_history()
        self._render_chat_input()

    def _render_sidebar(self):
        with st.sidebar:
            # Custom CSS for sidebar
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
                    .box-label {
                        color: #6ca395;
                        font-size: 0.7rem;
                        margin-bottom: 0.3rem;
                        border-bottom: 1px solid #4A4A4A;
                    }
                </style>
            """, unsafe_allow_html=True)

            # Display current Gen AI details at the top
            if st.session_state.provider and st.session_state.model:
                st.markdown(
                    f"""
                    <div style='
                        background-color: #3a3a3a;
                        padding: 10px;
                        border-radius: 5px;
                        margin-bottom: 10px;
                        font-size: 0.9em;
                    '>
                        <div style='
                            color: #6ca395;
                            text-align: center;
                            font-weight: bold;
                            margin-bottom: 8px;
                            border-bottom: 1px solid #4A4A4A;
                            padding-bottom: 4px;
                        '>
                            Gen AI Details
                        </div>
                        <div style='padding: 0 5px;'>
                            <span style='color: #6ca395;'>Provider:</span> {st.session_state.provider}<br>
                            <span style='color: #6ca395;'>Model:</span> {st.session_state.model}<br>
                            <span style='color: #6ca395;'>Persona:</span> {
                                "Custom" if st.session_state.get("custom_persona")
                                else next((k for k, v in PERSONAS.items() if v == st.session_state.persona), "Default")
                            }
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Settings Section
            with st.expander("**⚙️ Settings**", expanded=False):
                st.markdown('<div class="box-label">Model Settings</div>', unsafe_allow_html=True)
                with st.container():
                    provider = st.selectbox(
                        "Provider",
                        sorted(ProviderFactory.get_supported_providers(self.config["SUPPORTED_PROVIDERS"])),
                        index=sorted(self.config["SUPPORTED_PROVIDERS"]).index("groq"),
                        key="provider_select",
                        label_visibility="collapsed"
                    )

                    if provider and (models := self.config["MODELS"].get(provider)):
                        model = st.selectbox(
                            "Model",
                            models,
                            index=0,
                            key="model_select",
                            label_visibility="collapsed"
                        )
                        st.session_state.provider = provider
                        st.session_state.model = model

                    # Add Persona Selection
                    st.markdown('<div class="box-label">Persona</div>', unsafe_allow_html=True)
                    persona_options = list(PERSONAS.keys()) + ["Custom"]
                    selected_persona = st.selectbox(
                        "Persona",
                        persona_options,
                        index=persona_options.index(DEFAULT_PERSONA),
                        key="persona_select",
                        label_visibility="collapsed"
                    )

                    if selected_persona == "Custom":
                        custom_persona = st.text_area(
                            "Enter custom persona instructions:",
                            key="custom_persona",
                            label_visibility="collapsed",
                            placeholder="Enter instructions for the AI assistant..."
                        )
                        st.session_state.persona = custom_persona
                    else:
                        st.session_state.persona = PERSONAS[selected_persona]

                    # Temperature control (existing)
                    st.markdown('<div class="box-label">Temperature</div>', unsafe_allow_html=True)
                    temperature = st.slider(
                        "T",
                        0.0, 1.0, 0.7, 0.1,
                        key="temp_slider",
                        label_visibility="collapsed"
                    )
                    st.session_state.temperature = temperature

            # Chat Actions
            c1, c2 = st.columns(2)
            with c1:
                st.button("New", type="primary", use_container_width=True)
            with c2:
                if st.button("Clear", use_container_width=True):
                    self._handle_clear()

            # File Operations
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Save", use_container_width=True):
                    self._handle_save()
            with c2:
                if st.button("Export", use_container_width=True):
                    self._handle_export()

            # Load Chat
            with st.expander("**📂 Load Chat**", expanded=False):
                st.markdown('<div class="box-label">Load Chat</div>', unsafe_allow_html=True)
                self._handle_load()

            # File Upload
            with st.expander("**📄 Upload File**", expanded=False):
                st.markdown('<div class="box-label">Upload File</div>', unsafe_allow_html=True)
                self._handle_uploads()

    def _render_chat_history(self):
        """Render paginated chat history with controls"""
        messages_per_page = 10
        total_messages = len(st.session_state.chat_history)
        total_pages = max((total_messages - 1) // messages_per_page + 1, 1)

        # Initialize page in session state if not exists
        if "page" not in st.session_state:
            st.session_state.page = 0

        # Ensure page is within bounds
        st.session_state.page = min(st.session_state.page, total_pages - 1)

        # Calculate slice indices
        start_idx = st.session_state.page * messages_per_page
        end_idx = min(start_idx + messages_per_page, total_messages)

        # Display messages for current page
        for msg in st.session_state.chat_history[start_idx:end_idx]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Show pagination controls if needed
        if total_pages > 1:
            cols = st.columns([1, 2, 2, 2, 1])
            with cols[1]:
                if st.button("◀️", disabled=st.session_state.page == 0, key="prev_page"):
                    st.session_state.page = max(0, st.session_state.page - 1)
                    st.rerun()
            with cols[2]:
                st.write(f"Page {st.session_state.page + 1}/{total_pages}")
            with cols[3]:
                if st.button("▶️", disabled=st.session_state.page >= total_pages-1, key="next_page"):
                    st.session_state.page = min(total_pages - 1, st.session_state.page + 1)
                    st.rerun()

    def _render_chat_input(self):
        if prompt := st.chat_input("Message Groq..."):
            self.handle_message(prompt)

    def _handle_clear(self):
        """Reset all settings and chat state to defaults"""
        # Reset core settings
        defaults = {
            "provider": self.config["DEFAULT_PROVIDER"],
            "model": None,
            "temperature": 0.7,
            "persona": PERSONAS[DEFAULT_PERSONA],
            "chat_history": [],
            "page": 0,
            "file_processed": False,
            "chat_title": "New Chat"
        }

        # Clear any file upload state
        if 'uploaded_file' in st.session_state:
            del st.session_state.uploaded_file

        # Reset custom persona if it exists
        if 'custom_persona' in st.session_state:
            del st.session_state.custom_persona

        # Apply all defaults
        for key, value in defaults.items():
            st.session_state[key] = value

        # Force UI refresh
        st.rerun()

    def _handle_load(self):
        """Handle loading saved chats"""
        try:
            saved_chats = ChatExporter.get_saved_chats()
            if not saved_chats:
                st.warning("No saved chats found")
                return

            selected = st.selectbox(
                "Select chat:",
                saved_chats,
                label_visibility="collapsed",
                key="load_chat_select"
            )

            if st.button("Load", use_container_width=True, key="load_chat_button"):
                if selected and (history := ChatExporter.load_markdown(selected)):
                    st.session_state.chat_history = history
                    st.success(f"Loaded: {selected}")
                    st.rerun()

        except Exception as e:
            logger.error(f"Load error: {str(e)}")
            st.error("Failed to load chat")

    def _handle_uploads(self):
        """Handle file uploads"""
        uploaded_file = st.file_uploader(
            "Upload",
            type=["txt", "py", "js", "json", "csv", "md"],
            label_visibility="collapsed",
            key="file_uploader"
        )

        if uploaded_file:
            st.text(f"{uploaded_file.name} ({uploaded_file.type})")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Process", type="primary", use_container_width=True):
                    try:
                        content = self._process_file(uploaded_file)
                        self.handle_message(f"📎 File contents:\n```\n{content}\n```")
                        st.session_state.file_processed = True
                    except Exception as e:
                        st.error(f"Error processing file: {str(e)}")
            with c2:
                if st.button("Clear", use_container_width=True):
                    st.session_state.file_processed = False
                    st.rerun()

    def _collect_feedback(self):
        """Collect user feedback for the last assistant message"""
        feedback = st.radio(
            "Was this response helpful?",
            ["👍", "👎"],
            horizontal=True,
            label_visibility="collapsed",
            key=f"feedback_{len(st.session_state.chat_history)}"
        )

        # Store feedback with the last message
        if st.session_state.chat_history:
            last_msg = st.session_state.chat_history[-1]
            if last_msg["role"] == "assistant":
                last_msg["feedback"] = feedback

    def _handle_save(self):
        """Handle save functionality"""
        name = st.text_input("Enter chat name:", key="save_chat_name")
        if name and st.button("Save", key="confirm_save"):
            try:
                ChatExporter.export_markdown(st.session_state.chat_history, name)
                st.success(f"Chat saved as: {name}")
                st.rerun()
            except Exception as e:
                logger.error(f"Save error: {str(e)}")
                st.error("Failed to save chat")

    def _handle_export(self):
        """Export chat history to file"""
        if not st.session_state.chat_history:
            st.warning("No chat to export")
            return

        try:
            # Convert chat history to simple dict format
            formatted_history = [
                {k: str(v) for k, v in msg.items()}
                for msg in st.session_state.chat_history
            ]

            # Generate filename with timestamp
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"chat_export_{timestamp}"

            # Export with error handling
            try:
                export_path = ChatExporter.export_markdown(formatted_history, filename)
                if export_path:
                    st.success(f"Chat exported successfully to: {export_path}")
                    with open(export_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        st.download_button(
                            "Download Export",
                            content,
                            file_name=f"{filename}.md",
                            mime="text/markdown",
                            key="download_export"
                        )
            except Exception as e:
                logger.error(f"Export failed: {str(e)}")
                st.error("Failed to export chat. Please try again.")

        except Exception as e:
            logger.error(f"Export preparation error: {str(e)}")
            st.error("Failed to prepare chat for export")

    # ...existing code for other helper methods...