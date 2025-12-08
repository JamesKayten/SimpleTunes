"""Scrobbling routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from database import get_db
from services import ScrobbleService

router = APIRouter(prefix="/scrobble", tags=["Scrobbling"])


class ScrobbleConfigRequest(BaseModel):
    service: str
    api_key: str
    api_secret: str
    session_key: Optional[str] = None
    username: Optional[str] = None
    enabled: bool = True


@router.get("/config")
def get_scrobble_configs(db: Session = Depends(get_db)):
    """Get all scrobbling configurations."""
    service = ScrobbleService(db)
    configs = service.get_all_configs()
    return {
        "configs": [
            {
                "service": c.service,
                "enabled": c.enabled,
                "username": c.username,
            }
            for c in configs
        ]
    }


@router.post("/config")
def save_scrobble_config(request: ScrobbleConfigRequest, db: Session = Depends(get_db)):
    """Save scrobbling configuration."""
    service = ScrobbleService(db)
    config = service.save_config(
        request.service, request.api_key, request.api_secret,
        request.session_key, request.username, request.enabled
    )
    return {"service": config.service, "enabled": config.enabled}


@router.put("/config/{svc}/enable")
def enable_scrobble(svc: str, enabled: bool, db: Session = Depends(get_db)):
    """Enable or disable a scrobbling service."""
    service = ScrobbleService(db)
    if service.set_enabled(svc, enabled):
        return {"service": svc, "enabled": enabled}
    raise HTTPException(status_code=404, detail="Config not found")


@router.delete("/config/{svc}")
def delete_scrobble_config(svc: str, db: Session = Depends(get_db)):
    """Delete scrobbling configuration."""
    service = ScrobbleService(db)
    if service.delete_config(svc):
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="Config not found")


@router.get("/auth/lastfm/url")
def get_lastfm_auth_url(api_key: str, callback_url: Optional[str] = None, db: Session = Depends(get_db)):
    """Get Last.fm authentication URL."""
    service = ScrobbleService(db)
    url = service.get_lastfm_auth_url(api_key, callback_url)
    return {"url": url}


@router.post("/auth/lastfm/complete")
async def complete_lastfm_auth(
    api_key: str, api_secret: str, token: str, db: Session = Depends(get_db)
):
    """Complete Last.fm authentication."""
    service = ScrobbleService(db)
    try:
        result = await service.complete_lastfm_auth(api_key, api_secret, token)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{track_id}")
async def scrobble_track(
    track_id: str, timestamp: Optional[int] = None, db: Session = Depends(get_db)
):
    """Scrobble a track to all enabled services."""
    service = ScrobbleService(db)
    try:
        result = await service.scrobble(track_id, timestamp)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{track_id}/now-playing")
async def update_now_playing(track_id: str, db: Session = Depends(get_db)):
    """Update now playing status on all enabled services."""
    service = ScrobbleService(db)
    try:
        result = await service.update_now_playing(track_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/history")
def get_scrobble_history(
    svc: Optional[str] = None, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)
):
    """Get scrobble history."""
    service = ScrobbleService(db)
    history = service.get_scrobble_history(svc, limit, offset)
    return {
        "history": [
            {
                "id": h.id,
                "track_id": h.track_id,
                "service": h.service,
                "status": h.status,
                "scrobbled_at": h.scrobbled_at.isoformat() if h.scrobbled_at else None,
                "error_message": h.error_message,
            }
            for h in history
        ]
    }


@router.post("/retry-failed")
async def retry_failed_scrobbles(db: Session = Depends(get_db)):
    """Retry all failed scrobbles."""
    service = ScrobbleService(db)
    return await service.retry_failed_scrobbles()


@router.get("/stats")
def get_scrobble_stats(db: Session = Depends(get_db)):
    """Get scrobbling statistics."""
    service = ScrobbleService(db)
    return service.get_stats()
