"""Queue management routes."""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from database import get_db
from services import QueueService

router = APIRouter(prefix="/queue", tags=["Queue"])


class QueueAddRequest(BaseModel):
    track_ids: list[str]
    clear_existing: bool = False
    source_type: Optional[str] = None
    source_id: Optional[str] = None


@router.get("")
def get_queue(db: Session = Depends(get_db)):
    """Get current play queue."""
    service = QueueService(db)
    return service.get_queue()


@router.delete("")
def clear_queue(db: Session = Depends(get_db)):
    """Clear the play queue."""
    service = QueueService(db)
    service.clear_queue()
    return {"cleared": True}


@router.post("/tracks")
def add_tracks_to_queue(request: QueueAddRequest, db: Session = Depends(get_db)):
    """Add tracks to the queue."""
    service = QueueService(db)
    count = service.add_tracks(
        request.track_ids, request.source_type, request.source_id, request.clear_existing
    )
    return {"added": count}


@router.post("/album/{album_id}")
def add_album_to_queue(album_id: str, clear: bool = False, db: Session = Depends(get_db)):
    """Add an album to the queue."""
    service = QueueService(db)
    count = service.add_album(album_id, clear)
    return {"added": count}


@router.post("/playlist/{playlist_id}")
def add_playlist_to_queue(playlist_id: str, clear: bool = False, db: Session = Depends(get_db)):
    """Add a playlist to the queue."""
    service = QueueService(db)
    try:
        count = service.add_playlist(playlist_id, clear)
        return {"added": count}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/artist/{artist_id}")
def add_artist_to_queue(artist_id: str, clear: bool = False, db: Session = Depends(get_db)):
    """Add all tracks by an artist to the queue."""
    service = QueueService(db)
    count = service.add_artist(artist_id, clear)
    return {"added": count}


@router.post("/play-next/{track_id}")
def play_next(track_id: str, db: Session = Depends(get_db)):
    """Add a track to play next."""
    service = QueueService(db)
    item = service.play_next(track_id)
    return {"position": item.position}


@router.post("/add/{track_id}")
def add_to_queue(track_id: str, db: Session = Depends(get_db)):
    """Add a track to the end of the queue."""
    service = QueueService(db)
    item = service.add_to_queue(track_id)
    return {"position": item.position}


@router.delete("/items/{item_id}")
def remove_from_queue(item_id: str, db: Session = Depends(get_db)):
    """Remove an item from the queue."""
    service = QueueService(db)
    if service.remove_track(item_id):
        return {"removed": True}
    raise HTTPException(status_code=404, detail="Queue item not found")


@router.put("/items/{item_id}/move")
def move_queue_item(item_id: str, new_position: int, db: Session = Depends(get_db)):
    """Move a queue item to a new position."""
    service = QueueService(db)
    if service.move_track(item_id, new_position):
        return {"moved": True}
    raise HTTPException(status_code=404, detail="Queue item not found")


@router.get("/current")
def get_current_track(db: Session = Depends(get_db)):
    """Get currently playing track."""
    service = QueueService(db)
    track = service.get_current_track()
    return {"track": track}


@router.post("/next")
def next_track(db: Session = Depends(get_db)):
    """Move to next track."""
    service = QueueService(db)
    track = service.next_track()
    return {"track": track}


@router.post("/previous")
def previous_track(db: Session = Depends(get_db)):
    """Move to previous track."""
    service = QueueService(db)
    track = service.previous_track()
    return {"track": track}


@router.post("/play/{index}")
def play_at_index(index: int, db: Session = Depends(get_db)):
    """Play track at specific index."""
    service = QueueService(db)
    track = service.play_index(index)
    if track is None:
        raise HTTPException(status_code=400, detail="Invalid index")
    return {"track": track}


@router.put("/shuffle")
def set_shuffle(enabled: bool, db: Session = Depends(get_db)):
    """Enable/disable shuffle."""
    service = QueueService(db)
    return service.set_shuffle(enabled)


@router.put("/repeat")
def set_repeat(mode: str, db: Session = Depends(get_db)):
    """Set repeat mode (off, one, all)."""
    service = QueueService(db)
    try:
        return service.set_repeat(mode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/upcoming")
def get_upcoming(limit: int = 10, db: Session = Depends(get_db)):
    """Get upcoming tracks."""
    service = QueueService(db)
    return {"tracks": service.get_upcoming(limit)}


@router.get("/history")
def get_queue_history(limit: int = 10, db: Session = Depends(get_db)):
    """Get recently played tracks from queue."""
    service = QueueService(db)
    return {"tracks": service.get_history(limit)}
