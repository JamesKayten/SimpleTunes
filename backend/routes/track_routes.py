"""Track management API routes."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from schemas import (
    LibraryQuery,
    RatingUpdate,
    RatingResponse,
    SortField,
    SortOrder,
)
from services import LibraryService
from response_helpers import track_to_response

router = APIRouter(prefix="/tracks", tags=["Tracks"])


@router.get("")
def get_tracks(
    search: Optional[str] = None,
    genre: Optional[str] = None,
    artist_id: Optional[str] = None,
    album_id: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    rating_min: Optional[int] = None,
    favorites_only: bool = False,
    exclude_removed: bool = True,
    sort_by: SortField = SortField.TITLE,
    sort_order: SortOrder = SortOrder.ASC,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Query tracks with filtering and sorting."""
    query = LibraryQuery(
        search=search,
        genre=genre,
        artist_id=artist_id,
        album_id=album_id,
        year_from=year_from,
        year_to=year_to,
        rating_min=rating_min,
        favorites_only=favorites_only,
        exclude_removed=exclude_removed,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )

    service = LibraryService(db)
    tracks, total = service.query_tracks(query)

    return {
        "tracks": [track_to_response(t) for t in tracks],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# IMPORTANT: Specific routes MUST come before /{track_id} to avoid being intercepted
@router.get("/recent/played")
def get_recently_played(limit: int = 50, db: Session = Depends(get_db)):
    """Get recently played tracks."""
    service = LibraryService(db)
    tracks = service.get_recently_played(limit)
    return {"tracks": [track_to_response(t) for t in tracks]}


@router.get("/recent/added")
def get_recently_added(limit: int = 50, db: Session = Depends(get_db)):
    """Get recently added tracks."""
    service = LibraryService(db)
    tracks = service.get_recently_added(limit)
    return {"tracks": [track_to_response(t) for t in tracks]}


@router.get("/top/played")
def get_most_played(limit: int = 50, db: Session = Depends(get_db)):
    """Get most played tracks."""
    service = LibraryService(db)
    tracks = service.get_most_played(limit)
    return {"tracks": [track_to_response(t) for t in tracks]}


@router.get("/top/rated")
def get_top_rated(limit: int = 50, db: Session = Depends(get_db)):
    """Get highest rated tracks."""
    service = LibraryService(db)
    tracks = service.get_top_rated(limit)
    return {"tracks": [track_to_response(t) for t in tracks]}


@router.get("/favorites")
def get_favorites(db: Session = Depends(get_db)):
    """Get all favorite tracks."""
    service = LibraryService(db)
    tracks = service.get_favorites()
    return {"tracks": [track_to_response(t) for t in tracks]}


@router.get("/excluded")
def get_excluded(db: Session = Depends(get_db)):
    """Get all excluded tracks."""
    service = LibraryService(db)
    tracks = service.get_excluded()
    return {"tracks": [track_to_response(t) for t in tracks]}


# Dynamic route - must come AFTER all specific /tracks/* routes
@router.get("/{track_id}")
def get_track(track_id: str, db: Session = Depends(get_db)):
    """Get a single track by ID."""
    service = LibraryService(db)
    track = service.get_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track_to_response(track)


@router.post("/{track_id}/play")
def play_track(track_id: str, db: Session = Depends(get_db)):
    """Record a track play and increment play count."""
    service = LibraryService(db)
    try:
        track = service.increment_play_count(track_id)
        return {"play_count": track.play_count}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{track_id}/rating", response_model=RatingResponse)
def update_rating(
    track_id: str, rating: RatingUpdate, db: Session = Depends(get_db)
):
    """Update track rating, favorite status, or exclusion."""
    service = LibraryService(db)
    try:
        track_rating = service.rate_track(
            track_id,
            rating=rating.rating,
            excluded=rating.excluded,
            favorite=rating.favorite,
            notes=rating.notes,
        )
        return RatingResponse(
            track_id=track_rating.track_id,
            rating=track_rating.rating,
            excluded=track_rating.excluded,
            favorite=track_rating.favorite,
            notes=track_rating.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
