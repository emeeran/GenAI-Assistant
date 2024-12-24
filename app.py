import streamlit as st
import sqlite3
import uuid
import datetime
import os
import json
import markdown
from src.client import Client
from pathlib import Path

# --- Constants ---
DB_FILE = "chat_history.db"
CACHE_FILE = "chat_cache.json"
DEFAULT_PROVIDER = "openai"  # Default provider
CHAT_TABLE = "chat_history"
MODEL_TABLE = "model_list"


# --- Database Operations ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create chat_history table if it doesn't exist
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {CHAT_TABLE} (
            id TEXT PRIMARY KEY,
            chat_name TEXT,
            timestamp TEXT,
            provider TEXT,
            model TEXT,
            messages TEXT
        )
    """
    )

    # Create model_list table if it doesn't exist
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {MODEL_TABLE} (
            provider TEXT,
            models TEXT,
             PRIMARY KEY (provider)
        )
    """
    )
    conn.commit()
    conn.close()


def save_chat(chat_name, provider, model, messages):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    chat_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute(
        f"""
        INSERT INTO {CHAT_TABLE} (id, chat_name, timestamp, provider, model, messages)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (chat_id, chat_name, timestamp, provider, model, json.dumps(messages)),
    )
    conn.commit()
    conn.close()
    st.success(f"Chat saved as '{chat_name}'")
    return chat_id


def load_chats():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(f"SELECT chat_name FROM {CHAT_TABLE}")
    chat_names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return chat_names


def load_chat(chat_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT provider, model, messages FROM {CHAT_TABLE} WHERE chat_name = ?",
        (chat_name,),
    )
    result = cursor.fetchone()
    conn.close()

    if result:
        provider, model, messages = result
        return provider, model, json.loads(messages)
    else:
        return None, None, None


def export_chat_to_markdown(chat_name):
    """
    Fetch the full messages from the database and export them to a markdown format.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT messages FROM {CHAT_TABLE} WHERE chat_name = ?", (chat_name,)
    )
    result = cursor.fetchone()
    conn.close()

    if result:
        messages = json.loads(result[0])
        markdown_text = ""
        for message in messages:
            role = message["role"]
            content = message["content"]
            if role == "user":
                markdown_text += f"**User:**\n\n{content}\n\n"
            elif role == "assistant":
                markdown_text += f"**Assistant:**\n\n{content}\n\n"
        return markdown_text
    else:
        return None


def get_models_for_provider(provider):
    """Fetch the models associated with the given provider from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT models FROM {MODEL_TABLE} WHERE provider = ?",
        (provider,),
    )
    result = cursor.fetchone()
    conn.close()

    if result:
        return json.loads(result[0])
    else:
        return []


def update_models_for_provider(provider, models):
    """Updates the list of models for the given provider in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        f"""
        INSERT OR REPLACE INTO {MODEL_TABLE} (provider, models)
        VALUES (?, ?)
    """,
        (provider, json.dumps(models)),
    )
    conn.commit()
    conn.close()


# --- Caching ---
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def clear_cache():
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
    st.success("Cache cleared.")


# --- Streamlit UI ---
def main():
    st.set_page_config(page_title="Dynamic Chat App", page_icon="💬")
    st.title("Dynamic Chat App")

    # Initialize database
    init_db()

    # Load the cache
    cache = load_cache()
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "provider" not in st.session_state:
        st.session_state["provider"] = DEFAULT_PROVIDER
    if "model" not in st.session_state:
        st.session_state["model"] = None
    if "temperature" not in st.session_state:
        st.session_state["temperature"] = 0.7

    # Initialize client object
    if "client" not in st.session_state:
        st.session_state["client"] = Client()

    # Sidebar - Provider and Model Selection
    with st.sidebar:
        st.header("Settings")
        all_providers = st.session_state["client"].providers.keys()
        provider = st.selectbox(
            "Select API Provider",
            options=all_providers,
            index=list(all_providers).index(st.session_state["provider"])
            if st.session_state["provider"] in all_providers
            else 0,
        )
        st.session_state["provider"] = provider

        # Update the available models when a new provider is selected
        available_models = get_models_for_provider(provider)
        if not available_models:
            st.write("No models found, try refresh button.")
        else:
            if st.session_state["model"] not in available_models:
                st.session_state["model"] = available_models[0]
            model = st.selectbox(
                "Select Model",
                options=available_models,
                index=available_models.index(st.session_state["model"])
                if st.session_state["model"] in available_models
                else 0,
            )
            st.session_state["model"] = model

        st.session_state["temperature"] = st.slider(
            "Temperature", 0.0, 2.0, st.session_state["temperature"]
        )
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Refresh"):
                st.session_state["chat_history"] = []
                clear_cache()

                # Fetch the supported models for a provider
                try:
                    provider_instance = st.session_state["client"].providers[provider]
                    if hasattr(provider_instance, "get_supported_models"):
                        models = provider_instance.get_supported_models()
                        update_models_for_provider(provider, models)

                    else:
                        st.warning(
                            f"Provider {provider} does not have method get_supported_models to fetch the supported model list."
                        )
                except Exception as e:
                    st.error(f"Error fetching models: {e}")

        with col2:
            if st.button("Edit"):
                st.session_state["edit_mode"] = True

        col3, col4 = st.columns(2)
        with col3:
            if st.button("Save"):
                chat_name = st.text_input("Enter a name to save the chat")
                if chat_name:
                    save_chat(
                        chat_name,
                        st.session_state["provider"],
                        st.session_state["model"],
                        st.session_state["chat_history"],
                    )

        with col4:
            if st.button("Load"):
                saved_chats = load_chats()
                if saved_chats:
                    selected_chat = st.selectbox("Select a chat to load", saved_chats)
                    if selected_chat:
                        provider, model, messages = load_chat(selected_chat)
                        if messages:
                            st.session_state["provider"] = provider
                            st.session_state["model"] = model
                            st.session_state["chat_history"] = messages
                            st.experimental_rerun()

                else:
                    st.warning("No saved chats found.")

        if st.button("Export"):
            chat_name = st.text_input("Enter chat name to export the chat as markdown:")
            if chat_name:
                markdown_text = export_chat_to_markdown(chat_name)
                if markdown_text:
                    st.download_button(
                        label="Download Markdown File",
                        data=markdown_text,
                        file_name=f"{chat_name}.md",
                        mime="text/markdown",
                    )
                else:
                    st.error("Could not find the chat by the provided name.")

    # Chat Window
    chat_container = st.container()
    with chat_container:
        for message in st.session_state["chat_history"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Input box setup
        if "edit_mode" in st.session_state and st.session_state["edit_mode"]:
            st.session_state["edit_index"] = st.number_input(
                "Select message index to edit:",
                min_value=0,
                max_value=len(st.session_state["chat_history"]) - 1
                if st.session_state["chat_history"]
                else 0,
                step=1,
            )
            if st.session_state["chat_history"]:
                edited_message = st.text_area(
                    "Edit Message:",
                    value=st.session_state["chat_history"][
                        st.session_state["edit_index"]
                    ]["content"],
                )
            else:
                edited_message = None
            if st.button("Update Message"):
                if (
                    st.session_state["chat_history"]
                    and edited_message is not None
                    and st.session_state["edit_index"] < len(st.session_state["chat_history"])
                ):
                    st.session_state["chat_history"][
                        st.session_state["edit_index"]
                    ]["content"] = edited_message
                    st.session_state["edit_mode"] = False  # Exit edit mode
                    st.experimental_rerun()
        else:
            if prompt := st.chat_input("Enter prompt here..."):
                with st.chat_message("user"):
                    st.markdown(prompt)
                st.session_state["chat_history"].append({"role": "user", "content": prompt})
                # Create a unique key for caching based on the provider, model, temperature and prompt
                cache_key = (
                    st.session_state["provider"],
                    st.session_state["model"],
                    st.session_state["temperature"],
                    prompt
                )
                if cache_key in cache:
                    with st.chat_message("assistant"):
                        st.markdown(cache[cache_key])
                    st.session_state["chat_history"].append(
                        {"role": "assistant", "content": cache[cache_key]}
                    )
                else:
                    with st.spinner("Loading"):
                        try:
                            # Retrieve the selected provider
                            selected_provider = st.session_state["provider"]
                            selected_model = st.session_state["model"]
                            response = st.session_state["client"].chat.completions.create(
                                model=f"{selected_provider}:{selected_model}",
                                messages=st.session_state["chat_history"],
                                temperature=st.session_state["temperature"]
                            )
                            response_content = response.choices[0].message.content
                            cache[cache_key] = response_content
                            save_cache(cache)
                            with st.chat_message("assistant"):
                                st.markdown(response_content)
                            st.session_state["chat_history"].append(
                                {"role": "assistant", "content": response_content}
                            )

                        except Exception as e:
                            st.error(f"Error: {e}")

    # CSS Styling
    st.markdown(
        """
        <style>
            .stTextInput > div > div > div > textarea {
                background-color: #f5f5f5;
                border-radius: 10px;
                padding: 10px;
            }
            div.stChatMessage {
                background-color: #f0f0f0;
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 10px;
            }
             div.stChatMessage[data-testid="stChatMessageContent"] {
                display:flex;
             }
        </style>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()