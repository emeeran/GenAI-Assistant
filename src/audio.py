from typing import Optional
import streamlit as st
from gtts import gTTS
from io import BytesIO

# Language mapping
LANGUAGE_MAP = {
    "English": "en",
    "Tamil": "ta"
}

@st.cache_data(ttl=3600)
def generate_audio(text: str, language: str, voice_gender: str) -> Optional[BytesIO]:
    """Generate audio bytes from text."""
    try:
        if language == "Off":
            return None

        lang_code = LANGUAGE_MAP.get(language, "en")
        tld_value = "co.in" if voice_gender == "Male" else "com"
        tts = gTTS(text=text, lang=lang_code, tld=tld_value)

        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes

    except Exception as e:
        st.error(f"Text-to-speech error: {str(e)}")
        return None

def play_audio(text: str, language: str, voice_gender: str) -> None:
    """Generate and play audio."""
    if audio_bytes := generate_audio(text, language, voice_gender):
        st.audio(audio_bytes, format="audio/mp3")
