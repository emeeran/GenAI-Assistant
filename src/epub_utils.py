import warnings
from typing import Optional, List
from io import BytesIO
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache


def process_item(item) -> Optional[str]:
    """Process a single EPUB item"""
    if item.get_type() == ebooklib.ITEM_DOCUMENT:
        soup = BeautifulSoup(item.get_content(), "html.parser", parser="lxml")
        return soup.get_text(separator="\n", strip=True)
    return None


@lru_cache(maxsize=50)
def read_epub(file_content: BytesIO) -> Optional[str]:
    """Read EPUB content with parallel processing"""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="In the future version we will turn default option ignore_ncx to True.",
        )

        try:
            book = epub.read_epub(file_content, ignore_ncx=True)

            # Process items in parallel
            with ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(process_item, book.get_items()))

            # Filter None values and join text
            return "\n\n".join(filter(None, results))

        except Exception as e:
            print(f"Error reading EPUB: {e}")
            return None
