import PyPDF2
import pytesseract
from PIL import Image
import io
import logging
from typing import List, Tuple

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logging.warning("PyMuPDF not installed. Image extraction will be limited.")

class PDFProcessor:
    @staticmethod
    def extract_text_from_pdf(pdf_file) -> str:
        """Extract text content from PDF"""
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text

    @staticmethod
    def extract_images_and_ocr(pdf_file) -> Tuple[str, List[Image.Image]]:
        """Extract images from PDF and perform OCR"""
        if not PYMUPDF_AVAILABLE:
            return "PyMuPDF not installed. Cannot extract images.", []

        try:
            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
            images = []
            ocr_text = ""

            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()

                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]

                        # Convert to PIL Image
                        image = Image.open(io.BytesIO(image_bytes))
                        images.append(image)

                        # Perform OCR
                        ocr_text += pytesseract.image_to_string(image) + "\n"
                    except Exception as e:
                        logging.error(f"Error processing image {img_index} on page {page_num}: {e}")
                        continue

            return ocr_text, images
        except Exception as e:
            logging.error(f"Error processing PDF: {e}")
            return f"Error processing PDF: {str(e)}", []

    @staticmethod
    def summarize_text(text: str, client) -> str:
        """Summarize the extracted text using the AI client"""
        prompt = f"""Please provide a concise summary of the following text:

        {text[:2000]}...  # Limiting text length for API constraints

        Provide the summary in bullet points covering the main topics."""

        response = client.get_completion(prompt)
        return response
