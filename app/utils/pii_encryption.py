"""
PII encryption/decryption using Fernet (symmetric).
Used for hybrid PostgreSQL storage so PII is never stored in plain text.
"""
import os
import base64
import json
from typing import Any, Dict, Optional

from app.utils.logger import get_logger

logger = get_logger("pii_encryption", "logs/governance.log")

_FERNET = None
_KEY_ID = "default"


def _get_fernet():
    global _FERNET
    if _FERNET is not None:
        return _FERNET
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode("ascii")
        logger.warning("ENCRYPTION_KEY not set; using ephemeral key (not persisted)")
    try:
        from cryptography.fernet import Fernet
        _FERNET = Fernet(key.encode() if isinstance(key, str) else key)
        return _FERNET
    except Exception as e:
        logger.error("Failed to initialize Fernet: %s", e)
        raise


def encrypt_pii(data: Dict[str, Any]) -> bytes:
    """Encrypt a dict (e.g. passage with 'text', 'id', 'source') to bytes."""
    try:
        f = _get_fernet()
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        return f.encrypt(payload)
    except Exception as e:
        logger.error("Encrypt failed: %s", e)
        raise


def decrypt_pii(encrypted: bytes) -> Dict[str, Any]:
    """Decrypt bytes to a dict."""
    try:
        f = _get_fernet()
        decrypted = f.decrypt(encrypted)
        return json.loads(decrypted.decode("utf-8"))
    except Exception as e:
        logger.error("Decrypt failed: %s", e)
        raise


def get_encryption_key_id() -> str:
    return _KEY_ID
