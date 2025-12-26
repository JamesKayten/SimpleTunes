"""Artist browsing API routes."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Artist
from services import LibraryService
from response_helpers import artist_to_response, album_to_response, track_to_response

router = APIRouter(prefix="/artists", tags=["Artists"])


@router.get("")
def get_artists(sort_by: str = "name", db: Session = Depends(get_db)):
    """Get all artists."""
    service = LibraryService(db)
    artists = service.get_artists(sort_by)
    return {"artists": [artist_to_response(a, db) for a in artists]}


@router.get("/{artist_id}")
def get_artist(artist_id: str, db: Session = Depends(get_db)):
    """Get artist details with albums."""
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    service = LibraryService(db)
    albums = service.get_albums(artist_id=artist_id)
    tracks = service.get_tracks_by_artist(artist_id)

    return {
        **artist_to_response(artist, db),
        "albums": [album_to_response(a, db) for a in albums],
        "tracks": [track_to_response(t) for t in tracks],
    }
