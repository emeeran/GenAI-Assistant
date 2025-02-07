from typing import List
import re
from .token_utils import estimate_tokens

# Precompile the sentence splitting pattern once.
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text: str, max_chunk_size: int = 2000) -> List[str]:
    """Split text into chunks of approximately max_chunk_size tokens."""
    chunks = []
    current_chunk = []
    current_size = 0
    sentences = SENTENCE_SPLIT_PATTERN.split(text)

    for sentence in sentences:
        sentence_tokens = estimate_tokens(sentence)
        if current_size + sentence_tokens > max_chunk_size:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_size = 0
        current_chunk.append(sentence)
        current_size += sentence_tokens

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
