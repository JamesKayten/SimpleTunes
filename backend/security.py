"""Security utilities for SimpleTunes."""

import os
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64

from database import APP_DATA_DIR


# Encryption key management
ENCRYPTION_KEY_FILE = APP_DATA_DIR / ".encryption_key"


def get_or_create_encryption_key() -> bytes:
    """Get or create the encryption key for sensitive data."""
    if ENCRYPTION_KEY_FILE.exists():
        with open(ENCRYPTION_KEY_FILE, "rb") as f:
            return f.read()

    # Generate new key
    key = Fernet.generate_key()

    # Save it securely (only readable by owner)
    old_umask = os.umask(0o077)  # Only owner can read/write
    try:
        with open(ENCRYPTION_KEY_FILE, "wb") as f:
            f.write(key)
    finally:
        os.umask(old_umask)

    return key


def get_cipher() -> Fernet:
    """Get Fernet cipher for encryption/decryption."""
    key = get_or_create_encryption_key()
    return Fernet(key)


def encrypt_value(value: str) -> str:
    """Encrypt a sensitive string value."""
    if not value:
        return ""

    cipher = get_cipher()
    encrypted = cipher.encrypt(value.encode('utf-8'))
    return base64.b64encode(encrypted).decode('utf-8')


def decrypt_value(encrypted: str) -> str:
    """Decrypt a sensitive string value."""
    if not encrypted:
        return ""

    try:
        cipher = get_cipher()
        decoded = base64.b64decode(encrypted.encode('utf-8'))
        decrypted = cipher.decrypt(decoded)
        return decrypted.decode('utf-8')
    except Exception:
        # If decryption fails, return empty string
        return ""


# Path validation for security
ALLOWED_MUSIC_DIRECTORIES = [
    Path.home() / "Music",
    Path.home() / "Documents" / "Music",
    Path.home() / "Downloads",
    Path("/Volumes"),  # External drives on macOS
]


def add_allowed_directory(path: str) -> None:
    """Add a directory to the allowed list."""
    normalized = Path(path).expanduser().resolve()
    if normalized not in ALLOWED_MUSIC_DIRECTORIES:
        ALLOWED_MUSIC_DIRECTORIES.append(normalized)


def is_path_allowed(path: str) -> bool:
    """
    Check if a path is allowed for scanning/import.

    Returns True if the path is within an allowed directory.
    """
    # Allow override via environment variable for development
    if os.getenv("SIMPLETUNES_DISABLE_PATH_VALIDATION", "false").lower() == "true":
        return True

    try:
        normalized = Path(path).expanduser().resolve()

        # Check if path is within any allowed directory
        for allowed in ALLOWED_MUSIC_DIRECTORIES:
            try:
                normalized.relative_to(allowed)
                return True
            except ValueError:
                continue

        return False
    except Exception:
        return False


def validate_scan_path(path: str) -> Path:
    """
    Validate and normalize a scan path.

    Raises:
        ValueError: If path is not allowed or doesn't exist
    """
    normalized = Path(path).expanduser().resolve()

    if not normalized.exists():
        raise ValueError(f"Path does not exist: {path}")

    if not normalized.is_dir():
        raise ValueError(f"Path is not a directory: {path}")

    if not is_path_allowed(str(normalized)):
        raise ValueError(
            f"Path is not in allowed directories. "
            f"Allowed: {', '.join(str(p) for p in ALLOWED_MUSIC_DIRECTORIES)}"
        )

    return normalized


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal attacks.

    Removes path separators and special characters.
    """
    # Remove any path separators
    filename = filename.replace("/", "_").replace("\\", "_")

    # Remove any parent directory references
    filename = filename.replace("..", "_")

    # Remove null bytes
    filename = filename.replace("\x00", "")

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    return filename


def get_allowed_directories() -> list[str]:
    """Get list of allowed scan directories."""
    return [str(p) for p in ALLOWED_MUSIC_DIRECTORIES]
