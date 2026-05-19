import re
from typing import Optional


def clean_text(text: str) -> str:
    """Remove extra whitespace and normalize text."""
    return re.sub(r'\s+', ' ', text.strip())


def truncate(text: str, max_len: int = 4000) -> str:
    """Truncate text to max_len characters, breaking at word boundary."""
    if len(text) <= max_len:
        return text
    truncated = text[:max_len - 3]
    # Try to break at last space to avoid cutting mid-word
    last_space = truncated.rfind(' ')
    if last_space > max_len * 0.8:
        truncated = truncated[:last_space]
    return truncated + "..."


def chunk_text(text: str, max_len: int = 4096) -> list[str]:
    """
    Split text into chunks that fit within max_len.
    Breaks at paragraph boundaries, then sentence boundaries, then word boundaries.
    Used to split long bot responses into multiple Telegram messages.
    """
    if not text:
        return []
    if len(text) <= max_len:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= max_len:
            chunks.append(remaining)
            break

        # Try paragraph break
        idx = remaining.rfind('\n\n', 0, max_len)
        if idx > max_len * 0.5:
            chunks.append(remaining[:idx].strip())
            remaining = remaining[idx:].strip()
            continue

        # Try line break
        idx = remaining.rfind('\n', 0, max_len)
        if idx > max_len * 0.5:
            chunks.append(remaining[:idx].strip())
            remaining = remaining[idx:].strip()
            continue

        # Try sentence break (period followed by space)
        idx = remaining.rfind('. ', 0, max_len)
        if idx > max_len * 0.5:
            chunks.append(remaining[:idx + 1].strip())
            remaining = remaining[idx + 2:].strip()
            continue

        # Fall back to word break
        idx = remaining.rfind(' ', 0, max_len)
        if idx > 0:
            chunks.append(remaining[:idx])
            remaining = remaining[idx + 1:]
        else:
            chunks.append(remaining[:max_len])
            remaining = remaining[max_len:]

    return [c for c in chunks if c]


def extract_email(text: str) -> Optional[str]:
    """Extract the first valid email address found in text."""
    pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0).lower() if match else None


def extract_phone(text: str) -> Optional[str]:
    """
    Extract first phone number from text.
    Supports Chilean (+56 9 XXXX XXXX) and generic 9-digit mobile numbers.
    Uses word boundaries to avoid matching IDs or other numeric sequences.
    """
    patterns = [
        # +56 9 XXXX XXXX or +569XXXXXXXX
        r'(?<!\d)\+56[\s\-]?9[\s\-]?\d{4}[\s\-]?\d{4}(?!\d)',
        # 9XXXXXXXX (9 followed by 8 digits, word boundary)
        r'(?<!\d)9\d{8}(?!\d)',
        # Generic 8-digit landline (requires specific phone context word, not "número" which is too broad)
        r'(?:teléfono|celular|fono|tel\.?)\s*:?\s*(\d[\d\s\-]{6,10}\d)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # For the context-pattern, return captured group
            result = match.group(1) if match.lastindex else match.group(0)
            return re.sub(r'\s+', ' ', result.strip())
    return None


def escape_markdown(text: str) -> str:
    """
    Escape Telegram MarkdownV1 special characters that could break formatting.
    Only escapes characters that cause parse errors, not formatting markers.
    """
    # In MarkdownV1, only [ ] ( ) ~ ` > # + - = | { } . ! need escaping in certain contexts
    # For simplicity, escape the most problematic ones
    for char in ['_', '*', '[', ']', '`']:
        text = text.replace(char, f'\\{char}')
    return text
