from typing import Optional
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

def extract_pdf_text(file_content: BytesIO) -> str:
    """Extract text from PDF files"""
    from pdfminer.high_level import extract_text
    return extract_text(file_content)

def extract_epub_text(file_content: BytesIO) -> str:
    """Extract text from EPUB files"""
    try:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup

        book = epub.read_epub(file_content)
        texts = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            texts.append(soup.get_text())
        return "\n".join(texts)
    except ImportError as e:
        logger.error(f"EPUB support requires ebooklib: {e}")
        return "Error: EPUB support not available. Please install ebooklib."

def perform_ocr(file_content: BytesIO) -> str:
    """Perform OCR on image files"""
    import pytesseract
    from PIL import Image
    return pytesseract.image_to_string(Image.open(file_content))

def process_file(content: bytes, file_type: str) -> Optional[str]:
    """Process various file types and return text content"""
    try:
        file_content = BytesIO(content)
        if file_type == "application/pdf":
            return extract_pdf_text(file_content)
        elif file_type == "application/epub+zip":
            return extract_epub_text(file_content)
        elif file_type.startswith("image/"):
            return perform_ocr(file_content)
        return content.decode('utf-8')
    except Exception as e:
        logger.error(f"File processing error: {e}")
        return None
