import hashlib
import hmac
import time
from typing import Any, Dict

from app.config import settings


def verify_telegram_login_widget(data: Dict[str, Any]) -> bool:
    """
    Verify the hash provided by Telegram Login Widget.

    Official Telegram algorithm (https://core.telegram.org/widgets/login):
    1. Remove the 'hash' field from data.
    2. Sort remaining fields alphabetically as "key=value" lines.
    3. Compute secret_key = SHA-256(bot_token).
    4. Compute HMAC-SHA-256(data_check_string, secret_key).
    5. Compare with received hash (constant-time).
    6. Reject if auth_date is older than 24 hours.
    """
    received_hash = data.get("hash", "")
    if not received_hash:
        return False

    # Build sorted data-check string (all fields except 'hash')
    filtered = {k: str(v) for k, v in data.items() if k != "hash" and v is not None}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(filtered.items()))

    # Secret key is SHA-256 of the bot token (raw bytes, not hex)
    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()

    # Compute expected hash
    computed = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed, received_hash):
        return False

    # Reject stale auth (older than 24 h)
    auth_date = int(data.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        return False

    return True
