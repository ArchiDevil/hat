import re


def count_words(text: str) -> int:
    """
    Count words in a text string.
    Simple approach: split by whitespace and count non-empty tokens.
    This is intentionally not super-precise as per requirements.
    """
    # Remove extra whitespace and split by any whitespace
    words = re.findall(r"\S+", text)
    return len(words)
