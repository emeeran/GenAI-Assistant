from typing import Optional, Union
from pathlib import Path
import os


def read_file_content(file_path: Union[str, Path]) -> Optional[str]:
    """Read and return file content as string."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def make_content_available(file_path: Union[str, Path]) -> bool:
    """Make file content available for processing."""
    content = read_file_content(file_path)
    if content:
        cache_dir = Path("./cache")
        cache_dir.mkdir(exist_ok=True)

        try:
            cache_path = cache_dir / f"{Path(file_path).stem}_processed.txt"
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error caching content: {e}")
    return False
