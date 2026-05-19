import re


def clean_text(text: str) -> str:
    """Remove extra whitespace and normalize text."""
    return re.sub(r'\s+', ' ', text.strip())


def truncate(text: str, max_len: int = 4000) -> str:
    """Truncate text to max_len characters."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def extract_email(text: str) -> str | None:
    """Extract first email found in text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    """Extract first phone number found in text (Chilean/international formats)."""
    pattern = r'(?:\+?56)?[\s\-]?(?:9\d{8}|\d{8,9})'
    match = re.search(pattern, text)
    return match.group(0).strip() if match else None
