import streamlit as st
import sqlite3
import os
import json
import time
from functools import lru_cache
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
from io import BytesIO
from src.document_processor import extract_pdf_text, extract_epub_text, perform_ocr
from src.client import Client
from src.provider import ProviderFactory
from persona import PERSONAS, DEFAULT_PERSONA
from src.text_chunker import chunk_text
from src.token_utils import ensure_token_limit, estimate_tokens
from src.file_summarizer import FileSummarizer
from src.content_manager import ContentManager
from src.thread_manager import ThreadManager

load_dotenv()

CONFIG = {
    "SUPPORTED_PROVIDERS": frozenset({"openai", "anthropic", "cohere", "groq", "xai"}),
    "DEFAULT_PROVIDER": "groq",
    "DB_PATH": "chat_history.db",
    "MODELS": {
        "openai": ("gpt-4o", "gpt-4o-mini", "o1-mini-2024-09-12"),
        "anthropic": ("claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"),
        "groq": (
            "deepseek-r1-distill-llama-70b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ),
        "cohere": ("command-r7b-12-2024",),
        "xai": ("grok-2-vision-1212",),
    },
    "MAX_TOKENS": 2000,  # Reduced from 4000
    "CHUNK_OVERLAP": 100,  # Reduced from 200
    "RATE_LIMIT_DELAY": 2,  # Seconds between API calls
    "SUMMARY_MAX_TOKENS": 500,  # Max tokens for summary
}


class DB:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history
            (chat_name TEXT PRIMARY KEY, data JSON)
        """
        )
        self.conn.commit()

    @lru_cache(maxsize=100)
    def load(self, name: str) -> Optional[List[Dict]]:
        try:
            result = self.conn.execute(
                "SELECT data FROM chat_history WHERE chat_name = ?", (name,)
            ).fetchone()
            return json.loads(result[0]) if result else None
        except Exception as e:
            st.error(f"Load error: {e}")
            return None

    def save(self, name: str, history: List[Dict]) -> bool:
        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO chat_history (chat_name, data) VALUES (?, ?)",
                (name, json.dumps(history)),
            )
            self.conn.commit()
            self.load.cache_clear()
            self._export_to_markdown(name, history)
            return True
        except Exception as e:
            st.error(f"Save error: {e}")
            return False

    def _export_to_markdown(self, name: str, history: List[Dict]):
        os.makedirs("./exports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = f"./exports/{name}_{timestamp}.md"
        content = self._format_markdown(history)
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def _format_markdown(history: List[Dict]) -> str:
        lines = ["# Chat Export\n"]
        for msg in history:
            role = "🤖 Assistant" if msg["role"] == "assistant" else "👤 User"
            lines.extend([f"### {role}\n", f"{msg['content']}\n"])
        return "\n".join(lines)

    def delete(self, name: str) -> bool:
        try:
            self.conn.execute("DELETE FROM chat_history WHERE chat_name = ?", (name,))
            self.conn.commit()
            self.load.cache_clear()
            return True
        except Exception as e:
            st.error(f"Delete error: {e}")
            return False

    def get_names(self) -> List[str]:
        try:
            return [
                row[0]
                for row in self.conn.execute(
                    "SELECT chat_name FROM chat_history ORDER BY chat_name"
                )
            ]
        except Exception as e:
            st.error(f"List error: {e}")
            return []


class Chat:
    def __init__(self):
        self._init_session_state()
        self.db = DB(CONFIG["DB_PATH"])
        self.client = self._setup_client()
        self.file_summarizer = FileSummarizer()
        self.content_manager = ContentManager()
        self.thread_manager = ThreadManager()

    def _init_session_state(self):
        default_state = {
            "chat_history": [],
            "current_chat": None,
            "model": None,
            "temperature": 0.7,
            "provider": CONFIG["DEFAULT_PROVIDER"],
            "persona": DEFAULT_PERSONA,
            "custom_persona": "",
            "edit_mode": False,
            "save_clicked": False,
            "load_clicked": False,
            "file_processed": False,
            "current_file_context": None,
            "file_summary": None,
            "current_content_id": None,
            "initialized": True,
        }
        for key, value in default_state.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    @lru_cache(maxsize=1)
    def _setup_client():
        return Client(
            {
                p: {"api_key": os.getenv(f"{p.upper()}_API_KEY")}
                for p in CONFIG["SUPPORTED_PROVIDERS"]
                if os.getenv(f"{p.upper()}_API_KEY")
            }
        )

    @staticmethod
    @lru_cache(maxsize=50)
    def _process_file(file_content: bytes, file_type: str) -> Optional[str]:
        try:
            if file_type == "application/pdf":
                return extract_pdf_text(BytesIO(file_content))
            elif file_type == "application/epub+zip":
                return extract_epub_text(BytesIO(file_content))
            elif file_type.startswith("image/"):
                return perform_ocr(BytesIO(file_content))
            return file_content.decode("utf-8")
        except Exception as e:
            st.error(f"File error: {e}")
            return None

    def _build_messages(self, prompt: str) -> List[Dict]:
        messages = []
        if st.session_state.persona:
            persona = (
                st.session_state.custom_persona
                if st.session_state.persona == "Custom"
                else PERSONAS[st.session_state.persona]
            )
            if persona:
                messages.append({"role": "system", "content": persona})

        # Reduce context by limiting summary tokens
        if st.session_state.current_content_id:
            content_info = self.content_manager.get_content(
                st.session_state.current_content_id
            )
            if content_info:
                summary = ensure_token_limit(
                    content_info["content"], CONFIG["SUMMARY_MAX_TOKENS"]
                )
                messages.append(
                    {
                        "role": "system",
                        "content": f"Current content context: {content_info['file_name']}\n"
                        f"Summary: {summary}",
                    }
                )

        messages.extend(st.session_state.chat_history)
        messages.append({"role": "user", "content": prompt})
        return messages

    def _handle_chat(self, prompt: str):
        if not st.session_state.model:
            st.warning("Please select a model first")
            return

        prompt = ensure_token_limit(prompt, CONFIG["MAX_TOKENS"])
        estimated_tokens = estimate_tokens(prompt)

        if estimated_tokens > CONFIG["MAX_TOKENS"]:
            chunks = chunk_text(
                prompt, CONFIG["MAX_TOKENS"] // 2
            )  # Aggressive chunking
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                tasks = [lambda c=chunk: self._process_chunk(c) for chunk in chunks]
                combined_response = self.thread_manager.process_tasks(tasks)
                if combined_response:
                    final_response = "\n\n".join(combined_response)
                    st.session_state.chat_history.extend(
                        [
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": final_response},
                        ]
                    )
        else:
            messages = self._build_messages(prompt)
            try:
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Generating response..."):
                        response = self.client.chat.completions.create(
                            model=f"{st.session_state.provider}:{st.session_state.model}",
                            messages=messages,
                            temperature=st.session_state.temperature,
                        )
                        content = response.choices[0].message.content
                        st.markdown(content)
                        st.session_state.chat_history.extend(
                            [
                                {"role": "user", "content": prompt},
                                {"role": "assistant", "content": content},
                            ]
                        )
            except Exception as e:
                if "too many tokens" in str(e).lower():
                    st.error(
                        "The input is too large. Please try a shorter prompt or upload a smaller file."
                    )
                else:
                    st.error(f"Response error: {e}")

    def render_ui(self):
        st.markdown(
            "<h1 style='text-align: center; color: #6ca395'>GenAI- Assistant 💬</h1>",
            unsafe_allow_html=True,
        )
        self.render_sidebar()
        self._render_chat()

    def _render_chat(self):
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Enter your message"):
            self._handle_chat(prompt)

    def render_sidebar(self):
        with st.sidebar:
            st.markdown(
                '<h2 style="text-align: center; color: #6ca395;">Settings 🔧</h2>',
                unsafe_allow_html=True,
            )
            self._render_settings()
            self._render_actions()
            self._render_file_context()
            self._handle_uploads()

    def _render_settings(self):
        with st.expander("Configuration", expanded=False):
            providers = sorted(
                ProviderFactory.get_supported_providers(CONFIG["SUPPORTED_PROVIDERS"])
            )
            provider = st.selectbox(
                "Provider", providers, index=providers.index(st.session_state.provider)
            )

            if provider and (models := CONFIG["MODELS"].get(provider)):
                st.session_state.model = st.selectbox("Model", models)
                st.session_state.provider = provider

            personas = tuple(PERSONAS.keys())
            selected_persona = st.selectbox(
                "Select Persona",
                personas,
                index=personas.index(st.session_state.persona),
            )

            if selected_persona == "Custom":
                st.session_state.custom_persona = st.text_area(
                    "Define Custom Persona", value=st.session_state.custom_persona
                )
                st.session_state.persona = "Custom"
            else:
                st.session_state.persona = selected_persona

            st.session_state.temperature = st.slider(
                "Response Creativity", 0.0, 1.0, 0.7, 0.01
            )

    def _render_actions(self):
        col1, col2 = st.columns(2)
        if col1.button("Refresh", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        if col2.button("✏️ Edit", use_container_width=True):
            st.session_state.edit_mode = not st.session_state.edit_mode

        self._handle_save_load()

        if st.button("📝 Export", use_container_width=True):
            if st.session_state.chat_history:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = f"./exports/chat_export_{timestamp}.md"
                os.makedirs("./exports", exist_ok=True)
                try:
                    with open(export_path, "w", encoding="utf-8") as f:
                        f.write(DB._format_markdown(st.session_state.chat_history))
                    st.success(f"Chat exported to `{export_path}`")
                except Exception as e:
                    st.error(f"Export failed: {e}")
            else:
                st.warning("No chat to export")

    def _handle_save_load(self):
        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Save", use_container_width=True):
                st.session_state.save_clicked = True
                st.session_state.load_clicked = False

            if st.session_state.save_clicked and st.session_state.chat_history:
                name = st.text_input("Enter chat name:")
                if name and st.button("Confirm"):
                    if self.db.save(name, st.session_state.chat_history):
                        st.success(f"Saved as '{name}'")
                        st.session_state.save_clicked = False
                        st.rerun()

        with col2:
            if st.button("📂 Load", use_container_width=True):
                st.session_state.load_clicked = True
                st.session_state.save_clicked = False

            if st.session_state.load_clicked:
                if saved_chats := self.db.get_names():
                    selected = st.selectbox("Select chat:", saved_chats)
                    if selected:
                        if st.button("Load"):
                            if history := self.db.load(selected):
                                st.session_state.chat_history = history
                                st.session_state.current_chat = selected
                                st.rerun()

                        if st.checkbox("🗑️ Delete this chat"):
                            if st.button("Confirm Delete"):
                                if self.db.delete(selected):
                                    st.success(f"Deleted '{selected}'")
                                    st.session_state.load_clicked = False
                                    st.rerun()
                else:
                    st.warning("No saved chats found")

    def _handle_uploads(self):
        file = st.sidebar.file_uploader(
            "📎 Upload File",
            type=[
                "txt",
                "py",
                "js",
                "json",
                "csv",
                "md",
                "pdf",
                "epub",
                "jpg",
                "jpeg",
                "png",
            ],
        )

        if file and not st.session_state.get("file_processed"):
            try:
                content = self._process_file(file.read(), file.type)
                if content:
                    st.session_state.current_file_context = {
                        "name": file.name,
                        "content": content,
                        "type": file.type,
                    }
                    # NEW: Store file content for model access
                    content_id = self.content_manager.store_content(
                        file.name, content, file.type
                    )
                    st.session_state.current_content_id = content_id

                    summary_prompt = self.file_summarizer.get_summary_prompt(
                        content, file.type, file.name
                    )

                    chunks = chunk_text(summary_prompt, CONFIG["MAX_TOKENS"] - 200)
                    st.info("📄 Analyzing file content...")

                    tasks = [lambda c=chunk: self._process_chunk(c) for chunk in chunks]
                    combined_summary = self.thread_manager.process_tasks(tasks)

                    if combined_summary:
                        st.session_state.file_summary = "\n".join(combined_summary)
                        context_prompt = self.file_summarizer.get_context_prompt(
                            content, file.name
                        )
                        self._handle_chat(context_prompt)

                    st.session_state.file_processed = True
                    st.success(
                        "File content is ready and accessible for AI processing!"
                    )

            except Exception as e:
                st.error(f"File processing error: {e}")

        if not file:
            st.session_state.file_processed = False
            st.session_state.current_file_context = None
            st.session_state.file_summary = None

    def _process_chunk(self, chunk: str) -> Optional[str]:
        """Process a single chunk and return the response"""
        try:
            messages = self._build_messages(chunk)
            response = self.client.chat.completions.create(
                model=f"{st.session_state.provider}:{st.session_state.model}",
                messages=messages,
                temperature=st.session_state.temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"Error processing chunk: {e}")
            return None

    def _render_file_context(self):
        """Display current file context in sidebar"""
        if st.session_state.current_file_context:
            with st.expander("📎 Current File", expanded=True):
                st.write(f"File: {st.session_state.current_file_context['name']}")
                if st.session_state.file_summary:
                    st.write("Summary:")
                    st.write(st.session_state.file_summary)
                # New: allow users to view the full file content
                if st.checkbox("Show File Content", key="show_file_content"):
                    st.text_area(
                        "File Content",
                        value=st.session_state.current_file_context.get("content", ""),
                        height=200,
                    )


def main():
    st.set_page_config(page_title="GenAI-Assistant", page_icon="💬", layout="wide")
    Chat().render_ui()


if __name__ == "__main__":
    main()
