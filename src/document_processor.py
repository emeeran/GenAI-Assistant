import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from typing import Optional
from PIL import Image
import pytesseract
import whisper


def extract_pdf_text(file_content: bytes) -> Optional[str]:
    try:
        pdf_reader = PyPDF2.PdfReader(file_content)
        text = []
        for page in pdf_reader.pages:
            text.append(page.extract_text())
        return "\n".join(text)
    except Exception as e:
        return f"Error extracting PDF: {e}"


def extract_epub_text(file_content: bytes) -> Optional[str]:
    try:
        book = epub.read_epub(file_content)
        text = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), "html.parser")
                text.append(soup.get_text())
        return "\n".join(text)
    except Exception as e:
        return f"Error extracting EPUB: {e}"


def perform_ocr(image_file):
    """Perform OCR on the uploaded image file."""
    try:
        image = Image.open(image_file)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        return f"Error performing OCR: {e}"


def transcribe_audio(uploaded_file) -> str:
    file_content = uploaded_file.read()
    model = whisper.load_model("base")
    result = model.transcribe(file_content)
    return result["text"]


def process_uploaded_file(uploaded_file):
    # Handles the uploaded file and returns its text content
    file_handlers = {
        "application/pdf": extract_pdf_text,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": lambda f: " ".join(
            paragraph.text for paragraph in docx.Document(f).paragraphs
        ),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.document": process_excel_file,
        "application/vnd.ms-powerpoint": process_ppt_file,
        "text/plain": lambda f: f.getvalue().decode("utf-8"),
        "text/markdown": lambda f: f.getvalue().decode("utf-8"),
        "image/jpeg": perform_ocr,
        "image/png": perform_ocr,
        "audio/mpeg": transcribe_audio,
        "audio/wav": transcribe_audio,
        "audio/x-wav": transcribe_audio,
    }

    handler = next(
        (
            func
            for file_type, func in file_handlers.items()
            if uploaded_file.type.startswith(file_type)
        ),
        None,
    )
    if handler:
        return handler(uploaded_file)
    raise ValueError("Unsupported file type")
