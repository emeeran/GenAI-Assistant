import streamlit as st
import sqlite3
import os
import json
from functools import lru_cache
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
from io import BytesIO
from src.document_processor import (
    extract_pdf_text,
    extract_epub_text,
    perform_ocr,
)
from src.client import Client
from src.provider import ProviderFactory
from persona import PERSONAS, DEFAULT_PERSONA

load_dotenv()

CONFIG = {
    "SUPPORTED_PROVIDERS": frozenset({"openai", "anthropic", "cohere", "groq", "xai"}),
    "DEFAULT_PROVIDER": "groq",
    "DB_PATH": "chat_history.db",
    "MODELS": {
        "openai": ("gpt-4o", "gpt-4o-mini"),
        "anthropic": ("claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"),
        "groq": ("llama-3.3-70b-versatile", "llama-3.1-8b-instant"),
        "cohere": ("command-r7b-12-2024",),
        "xai": ("grok-2-vision-1212",),
    },
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

    def _init_session_state(self):
        if not hasattr(st.session_state, "initialized"):
            st.session_state.update(
                {
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
                    "initialized": True,
                }
            )

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
        messages.extend(st.session_state.chat_history)
        messages.append({"role": "user", "content": prompt})
        return messages

    def _handle_chat(self, prompt: str):
        if not st.session_state.model:
            st.warning("Please select a model first")
            return

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
            st.error(f"Response error: {e}")

    def render_ui(self):
        st.markdown(
            "<h1 style='text-align: center; color: #6ca395'>AI Chat Assistant 💬</h1>",
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
        if col1.button("🔄 Refresh", use_container_width=True):
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
                    st.session_state.file_processed = True
                    self._handle_chat(f"📎 File: {file.name}\n\n```\n{content}\n```")
            except Exception as e:
                st.error(f"File processing error: {e}")

        if not file:
            st.session_state.file_processed = False


def main():
    st.set_page_config(page_title="AI Chat Assistant", page_icon="💬", layout="wide")
    Chat().render_ui()


if __name__ == "__main__":
    main()
