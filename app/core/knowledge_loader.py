"""
Knowledge Loader — canonical interface for accessing the Crovenett knowledge base.

Files are read once per process via lru_cache. Restart the server to pick up
changes to .md files in production.
"""
from functools import lru_cache
from pathlib import Path
from typing import Dict

from app.utils.logger import get_logger

logger = get_logger(__name__)

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

KNOWLEDGE_FILES = [
    "crovenett_profile.md",
    "services.md",
    "faqs.md",
    "pricing_guidelines.md",
    "sales_script.md",
]


@lru_cache(maxsize=None)
def load_file(filename: str) -> str:
    """Load and cache a knowledge file. Returns a placeholder if missing."""
    path = KNOWLEDGE_DIR / filename
    if not path.exists():
        logger.warning(f"Knowledge file not found: {filename}")
        return f"[{filename} no disponible]"
    content = path.read_text(encoding="utf-8").strip()
    logger.info(f"Knowledge loaded: {filename} ({len(content)} chars)")
    return content


def get_status() -> Dict[str, dict]:
    """Return presence/size status for all expected knowledge files."""
    result: Dict[str, dict] = {}
    for filename in KNOWLEDGE_FILES:
        path = KNOWLEDGE_DIR / filename
        if path.exists() and path.stat().st_size > 0:
            result[filename] = {"status": "ok", "size_bytes": path.stat().st_size}
        else:
            result[filename] = {"status": "missing_or_empty"}
    return result
