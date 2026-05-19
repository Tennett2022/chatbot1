"""
JWT handler — HS256 implementation using Python's standard library only.
Uses HMAC-SHA256: no external cryptography dependencies required.
"""
import base64
import hashlib
import hmac
import json
import time
from datetime import timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException, status

from app.config import settings

ROLES = frozenset({"public_client", "admin", "sales", "integration"})


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    # Re-pad to a multiple of 4
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate a signed HS256 JWT."""
    if not settings.JWT_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET_KEY is not configured on this server.",
        )
    payload = data.copy()
    expire = int(time.time()) + int(
        (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)).total_seconds()
    )
    payload["exp"] = expire
    payload["iat"] = int(time.time())

    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64url_encode(json.dumps(payload, default=str).encode())
    signing_input = f"{header}.{body}"
    sig = _b64url_encode(
        hmac.new(
            settings.JWT_SECRET_KEY.encode(),
            signing_input.encode(),
            hashlib.sha256,
        ).digest()
    )
    return f"{signing_input}.{sig}"


def decode_access_token(token: str) -> Dict[str, Any]:
    """Verify and decode an HS256 JWT. Raises 401 if invalid or expired."""
    if not settings.JWT_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET_KEY is not configured on this server.",
        )
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Malformed token")

        header_b64, body_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{body_b64}"

        expected_sig = _b64url_encode(
            hmac.new(
                settings.JWT_SECRET_KEY.encode(),
                signing_input.encode(),
                hashlib.sha256,
            ).digest()
        )
        if not hmac.compare_digest(expected_sig, sig_b64):
            raise ValueError("Invalid signature")

        payload = json.loads(_b64url_decode(body_b64))
        if payload.get("exp", 0) < time.time():
            raise ValueError("Token expired")

        return payload

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido o expirado: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
