def estimate_tokens(text: str) -> int:
    """Rough estimation of tokens (4 chars ~ 1 token)"""
    return len(text) // 4


def ensure_token_limit(text: str, max_tokens: int = 3000) -> str:
    """Truncate text to stay within token limit"""
    if estimate_tokens(text) <= max_tokens:
        return text
    return text[: max_tokens * 4]
