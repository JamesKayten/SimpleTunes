"""Audio file streaming API routes."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from database import get_db
from models import Track
from response_helpers import get_media_type

router = APIRouter(prefix="/stream", tags=["Streaming"])


@router.get("/{track_id}")
def stream_track(track_id: str, db: Session = Depends(get_db)):
    """Stream a music file."""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    file_path = Path(track.path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_path,
        media_type=get_media_type(file_path.suffix),
        filename=file_path.name,
    )
