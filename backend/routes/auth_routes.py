"""Authentication and API key management routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from auth import APIKey, create_api_key, require_api_key

router = APIRouter(prefix="/auth", tags=["Authentication"])


class APIKeyCreate(BaseModel):
    name: str


class APIKeyResponse(BaseModel):
    id: str
    name: str
    enabled: bool
    created_at: str
    last_used: Optional[str] = None


@router.post("/keys", dependencies=[Depends(require_api_key)])
def create_new_api_key(request: APIKeyCreate, db: Session = Depends(get_db)):
    """Create a new API key (requires existing valid API key)."""
    key = create_api_key(request.name)
    return {"key": key, "name": request.name}


@router.get("/keys", dependencies=[Depends(require_api_key)])
def list_api_keys(db: Session = Depends(get_db)):
    """List all API keys (without revealing the actual key values)."""
    keys = db.query(APIKey).all()
    return {
        "keys": [
            {
                "id": k.id,
                "name": k.name,
                "enabled": k.enabled,
                "created_at": k.created_at.isoformat() if k.created_at else None,
                "last_used": k.last_used.isoformat() if k.last_used else None,
            }
            for k in keys
        ]
    }


@router.put("/keys/{key_id}/disable", dependencies=[Depends(require_api_key)])
def disable_api_key(key_id: str, db: Session = Depends(get_db)):
    """Disable an API key."""
    key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    key.enabled = False
    db.commit()
    return {"disabled": True}


@router.put("/keys/{key_id}/enable", dependencies=[Depends(require_api_key)])
def enable_api_key(key_id: str, db: Session = Depends(get_db)):
    """Enable an API key."""
    key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    key.enabled = True
    db.commit()
    return {"enabled": True}


@router.delete("/keys/{key_id}", dependencies=[Depends(require_api_key)])
def delete_api_key(key_id: str, db: Session = Depends(get_db)):
    """Delete an API key."""
    key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    # Prevent deleting the last key
    total_keys = db.query(APIKey).filter(APIKey.enabled == True).count()
    if total_keys <= 1:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the last enabled API key"
        )

    db.delete(key)
    db.commit()
    return {"deleted": True}


@router.get("/verify")
def verify_key(api_key: str = Depends(require_api_key)):
    """Verify that an API key is valid."""
    return {"valid": True, "key": api_key[:10] + "..."}
