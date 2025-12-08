"""Lyrics routes."""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from database import get_db
from services import LyricsService

router = APIRouter(prefix="/lyrics", tags=["Lyrics"])


class CustomLyricsRequest(BaseModel):
    plain_lyrics: Optional[str] = None
    synced_lyrics: Optional[list[dict]] = None


@router.get("/{track_id}")
async def get_lyrics(track_id: str, force_refresh: bool = False, db: Session = Depends(get_db)):
    """Get lyrics for a track, fetching if not cached."""
    service = LyricsService(db)
    lyrics = await service.get_lyrics(track_id, force_refresh)
    if lyrics:
        return lyrics
    return {
        "track_id": track_id,
        "plain_lyrics": None,
        "synced_lyrics": None,
        "has_synced": False,
    }


@router.get("/{track_id}/line")
def get_lyrics_line(track_id: str, time: float, db: Session = Depends(get_db)):
    """Get current lyrics line at playback time (for synced lyrics display)."""
    service = LyricsService(db)
    result = service.get_line_at_time(track_id, time)
    if result:
        return result
    return {"current": None, "next": None, "progress": 0}


@router.post("/{track_id}/custom")
def save_custom_lyrics(track_id: str, request: CustomLyricsRequest, db: Session = Depends(get_db)):
    """Save user-provided custom lyrics."""
    service = LyricsService(db)
    return service.save_custom_lyrics(track_id, request.plain_lyrics, request.synced_lyrics)


@router.delete("/{track_id}")
def delete_lyrics(track_id: str, db: Session = Depends(get_db)):
    """Delete cached lyrics for a track."""
    service = LyricsService(db)
    if service.delete_lyrics(track_id):
        return {"deleted": True}
    return {"deleted": False}


@router.post("/fetch-missing")
async def fetch_missing_lyrics(limit: int = 50, db: Session = Depends(get_db)):
    """Fetch lyrics for tracks that don't have them."""
    service = LyricsService(db)
    return await service.fetch_missing_lyrics(limit)


@router.get("/search")
def search_by_lyrics(query: str, db: Session = Depends(get_db)):
    """Search tracks by lyrics content."""
    service = LyricsService(db)
    return {"results": service.search_lyrics(query)}
