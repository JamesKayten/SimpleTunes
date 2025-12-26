"""Album browsing API routes."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import Album
from services import LibraryService
from response_helpers import album_to_response, track_to_response

router = APIRouter(prefix="/albums", tags=["Albums"])


@router.get("")
def get_albums(
    artist_id: Optional[str] = None,
    genre: Optional[str] = None,
    year: Optional[int] = None,
    sort_by: str = "title",
    sort_order: str = "asc",
    db: Session = Depends(get_db),
):
    """Get albums with optional filtering."""
    service = LibraryService(db)
    albums = service.get_albums(artist_id, genre, year, sort_by, sort_order)
    return {"albums": [album_to_response(a, db) for a in albums]}


@router.get("/{album_id}")
def get_album(album_id: str, db: Session = Depends(get_db)):
    """Get album details with tracks."""
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    service = LibraryService(db)
    tracks = service.get_tracks_by_album(album_id)

    return {
        **album_to_response(album, db),
        "tracks": [track_to_response(t) for t in tracks],
    }
