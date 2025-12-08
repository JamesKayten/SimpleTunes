"""Smart playlist routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from database import get_db
from services import SmartPlaylistService

router = APIRouter(prefix="/playlists/smart", tags=["Smart Playlists"])


class SmartPlaylistCreate(BaseModel):
    name: str
    rules: list[dict]
    match_all: bool = True
    limit: Optional[int] = None
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    description: Optional[str] = None


class SmartPlaylistUpdate(BaseModel):
    name: Optional[str] = None
    rules: Optional[list[dict]] = None
    match_all: Optional[bool] = None
    limit: Optional[int] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None
    description: Optional[str] = None


def _playlist_to_response(playlist) -> dict:
    return {
        "id": playlist.id,
        "name": playlist.name,
        "description": playlist.description,
        "is_smart": playlist.is_smart,
        "track_count": getattr(playlist, "track_count", 0),
        "total_duration": getattr(playlist, "total_duration", 0),
        "cover_path": playlist.cover_path,
        "created_at": playlist.created_at.isoformat() if playlist.created_at else None,
        "updated_at": playlist.updated_at.isoformat() if playlist.updated_at else None,
    }


def _track_to_response(track) -> dict:
    return {
        "id": track.id,
        "path": track.path,
        "title": track.title,
        "artist_id": track.artist_id,
        "artist_name": track.artist.name if track.artist else None,
        "album_id": track.album_id,
        "album_name": track.album.title if track.album else None,
        "cover_path": track.album.cover_path if track.album else None,
        "duration": track.duration,
        "track_number": track.track_number,
        "genre": track.genre,
        "year": track.year,
    }


@router.post("")
def create_smart_playlist(request: SmartPlaylistCreate, db: Session = Depends(get_db)):
    """Create a smart playlist with rules."""
    service = SmartPlaylistService(db)
    playlist = service.create_smart_playlist(
        request.name, request.rules, request.match_all,
        request.limit, request.sort_by, request.sort_order, request.description
    )
    return _playlist_to_response(playlist)


@router.put("/{playlist_id}")
def update_smart_playlist(playlist_id: str, request: SmartPlaylistUpdate, db: Session = Depends(get_db)):
    """Update a smart playlist's rules."""
    service = SmartPlaylistService(db)
    try:
        playlist = service.update_smart_playlist(
            playlist_id, request.name, request.rules, request.match_all,
            request.limit, request.sort_by, request.sort_order, request.description
        )
        return _playlist_to_response(playlist)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{playlist_id}/refresh")
def refresh_smart_playlist(playlist_id: str, db: Session = Depends(get_db)):
    """Refresh a smart playlist's tracks."""
    service = SmartPlaylistService(db)
    try:
        count = service.refresh_smart_playlist(playlist_id)
        return {"track_count": count}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/refresh-all")
def refresh_all_smart_playlists(db: Session = Depends(get_db)):
    """Refresh all smart playlists."""
    service = SmartPlaylistService(db)
    return service.refresh_all_smart_playlists()


@router.get("/{playlist_id}/rules")
def get_smart_playlist_rules(playlist_id: str, db: Session = Depends(get_db)):
    """Get the rules for a smart playlist."""
    service = SmartPlaylistService(db)
    try:
        return service.get_smart_playlist_rules(playlist_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/preview")
def preview_smart_playlist(request: SmartPlaylistCreate, db: Session = Depends(get_db)):
    """Preview what tracks would match smart playlist rules."""
    service = SmartPlaylistService(db)
    tracks = service.preview_smart_playlist(
        request.rules, request.match_all, request.limit, request.sort_by, request.sort_order
    )
    return {"tracks": [_track_to_response(t) for t in tracks], "count": len(tracks)}


@router.get("/fields")
def get_smart_playlist_fields():
    """Get available fields and operators for smart playlists."""
    return SmartPlaylistService.get_available_fields()
