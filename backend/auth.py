"""Authentication and authorization for SimpleTunes API."""

import os
import secrets
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Boolean
from datetime import datetime

from models import Base
from database import get_db_session


# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKey(Base):
    """API Key model for authentication."""
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: secrets.token_urlsafe(32))
    key = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)


def generate_api_key() -> str:
    """Generate a new API key."""
    return f"sk_{secrets.token_urlsafe(32)}"


def create_api_key(name: str = "default") -> str:
    """Create a new API key in the database."""
    with get_db_session() as db:
        key = generate_api_key()
        api_key = APIKey(key=key, name=name)
        db.add(api_key)
        db.commit()
        return key


def verify_api_key(api_key: str, db: Session) -> bool:
    """Verify an API key is valid and enabled."""
    if not api_key:
        return False

    key_obj = db.query(APIKey).filter(APIKey.key == api_key).first()
    if not key_obj or not key_obj.enabled:
        return False

    # Update last used timestamp
    key_obj.last_used = datetime.utcnow()
    db.commit()

    return True


async def require_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> str:
    """
    Dependency to require API key authentication.

    Usage:
        @app.get("/protected")
        def protected_route(api_key: str = Depends(require_api_key)):
            ...
    """
    # Check if auth is disabled (for development)
    if os.getenv("SIMPLETUNES_DISABLE_AUTH", "false").lower() == "true":
        return "dev-key"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify the key
    with get_db_session() as db:
        if not verify_api_key(api_key, db):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or disabled API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

    return api_key


async def optional_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[str]:
    """
    Optional API key authentication (doesn't raise error if missing).

    Useful for endpoints that have different behavior for authenticated users.
    """
    if os.getenv("SIMPLETUNES_DISABLE_AUTH", "false").lower() == "true":
        return "dev-key"

    if not api_key:
        return None

    with get_db_session() as db:
        if verify_api_key(api_key, db):
            return api_key

    return None


def init_default_api_key():
    """Initialize a default API key if none exist."""
    with get_db_session() as db:
        existing = db.query(APIKey).first()
        if not existing:
            key = create_api_key("default")
            print(f"\n{'='*60}")
            print(f"SIMPLETUNES DEFAULT API KEY CREATED")
            print(f"{'='*60}")
            print(f"API Key: {key}")
            print(f"\nAdd this to your frontend configuration:")
            print(f'X-API-Key: {key}')
            print(f"\nOr disable auth for development:")
            print(f"export SIMPLETUNES_DISABLE_AUTH=true")
            print(f"{'='*60}\n")
            return key
    return None
