"""Security utilities: password hashing, JWT token creation/validation."""
import hashlib
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level key cache
_private_key: bytes | None = None
_public_key: bytes | None = None
DEFAULT_KEYS_DIR = Path(__file__).resolve().parent.parent.parent / "keys"


def _resolve_key_pair_paths() -> tuple[Path, Path]:
    """Resolve JWT key paths from config, falling back to backend/keys/."""
    private_path = (
        Path(settings.JWT_PRIVATE_KEY_PATH)
        if settings.JWT_PRIVATE_KEY_PATH
        else DEFAULT_KEYS_DIR / "private_key.pem"
    )
    public_path = (
        Path(settings.JWT_PUBLIC_KEY_PATH)
        if settings.JWT_PUBLIC_KEY_PATH
        else DEFAULT_KEYS_DIR / "public_key.pem"
    )
    return private_path, public_path


def ensure_jwt_key_pair() -> tuple[Path, Path]:
    """Create an Ed25519 key pair when the configured files are missing."""
    private_path, public_path = _resolve_key_pair_paths()
    if private_path.exists() and public_path.exists():
        return private_path, public_path

    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    private_path.chmod(0o600)
    public_path.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    logger.warning(
        "JWT key files were missing. Generated a new Ed25519 key pair at %s",
        private_path.parent,
    )
    return private_path, public_path


def _load_key_pair() -> tuple[bytes, bytes]:
    """Load Ed25519 key pair from PEM files. Cached after first call."""
    global _private_key, _public_key
    if _private_key and _public_key:
        return _private_key, _public_key

    private_path, public_path = ensure_jwt_key_pair()

    _private_key = private_path.read_bytes()
    _public_key = public_path.read_bytes()
    logger.info("Loaded JWT key pair from %s", private_path.parent)
    return _private_key, _public_key


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def validate_password(password: str) -> None:
    """Enforce password policy. Raises ValueError on failure."""
    errors = []
    if len(password) < 12:
        errors.append("at least 12 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("at least one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("at least one digit")
    if errors:
        raise ValueError(f"Password must contain: {', '.join(errors)}")


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

def create_access_token(user_id: int, role: str) -> str:
    """Create a short-lived JWT access token signed with Ed25519."""
    private_key, _ = _load_key_pair()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, private_key, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT access token. Raises jwt.PyJWTError on failure."""
    _, public_key = _load_key_pair()
    return jwt.decode(
        token,
        public_key,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "role", "exp", "iat"]},
    )


def create_refresh_token() -> tuple[str, str]:
    """Create a cryptographically random refresh token.

    Returns:
        (raw_token, sha256_hash) - store hash in DB, send raw to client
    """
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash


def hash_refresh_token(raw_token: str) -> str:
    """Hash a raw refresh token for DB lookup."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def create_ingestion_api_key() -> tuple[str, str, str]:
    """Create a long-lived ingestion API key.

    Returns:
        raw_key, key_prefix, key_hash
    """
    raw_key = f"bod_live_{secrets.token_urlsafe(32)}"
    key_prefix = raw_key[:18]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_prefix, key_hash


def hash_ingestion_api_key(raw_key: str) -> str:
    """Hash a raw ingestion API key for DB lookup."""
    return hashlib.sha256(raw_key.encode()).hexdigest()
