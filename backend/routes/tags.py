"""Tag editing routes."""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from database import get_db
from services import TagEditorService

router = APIRouter(prefix="/tags", tags=["Tag Editing"])


class TagUpdateRequest(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    album_artist: Optional[str] = None
    composer: Optional[str] = None
    write_to_file: bool = True


class BatchTagUpdateRequest(BaseModel):
    track_ids: list[str]
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    write_to_file: bool = True


@router.get("/{track_id}")
def get_tags(track_id: str, db: Session = Depends(get_db)):
    """Get all editable tags for a track (from file and database)."""
    service = TagEditorService(db)
    result = service.get_tags(track_id)
    if not result:
        raise HTTPException(status_code=404, detail="Track not found")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.put("/{track_id}")
def update_tags(track_id: str, request: TagUpdateRequest, db: Session = Depends(get_db)):
    """Update track tags in database and optionally in file."""
    service = TagEditorService(db)
    result = service.update_tags(
        track_id,
        title=request.title,
        artist=request.artist,
        album=request.album,
        genre=request.genre,
        year=request.year,
        track_number=request.track_number,
        disc_number=request.disc_number,
        album_artist=request.album_artist,
        composer=request.composer,
        write_to_file=request.write_to_file,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{track_id}/sync")
def sync_tags_from_file(track_id: str, db: Session = Depends(get_db)):
    """Sync database tags from file (useful when file was edited externally)."""
    service = TagEditorService(db)
    result = service.sync_from_file(track_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.put("/batch")
def batch_update_tags(request: BatchTagUpdateRequest, db: Session = Depends(get_db)):
    """Update tags for multiple tracks at once."""
    service = TagEditorService(db)
    return service.batch_update(
        request.track_ids,
        artist=request.artist,
        album=request.album,
        genre=request.genre,
        year=request.year,
        write_to_file=request.write_to_file,
    )
