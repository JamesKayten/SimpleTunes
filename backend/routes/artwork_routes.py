"""Artwork fetching and serving API routes."""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db, ARTWORK_DIR
from services import ArtworkFetcherService

router = APIRouter(prefix="/artwork", tags=["Artwork"])


@router.post("/album/{album_id}")
async def fetch_album_artwork(
    album_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Fetch album artwork from online sources."""
    service = ArtworkFetcherService(db)
    result = await service.fetch_album_cover(album_id)
    if result:
        return {"path": result}
    return {"path": None, "message": "No artwork found"}


@router.post("/artist/{artist_id}")
async def fetch_artist_artwork(
    artist_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Fetch artist image from online sources."""
    service = ArtworkFetcherService(db)
    result = await service.fetch_artist_image(artist_id)
    if result:
        return {"path": result}
    return {"path": None, "message": "No artwork found"}


@router.post("/fetch-missing")
async def fetch_missing_artwork(
    limit: int = 50, db: Session = Depends(get_db)
):
    """Fetch artwork for all albums missing covers."""
    service = ArtworkFetcherService(db)
    result = await service.fetch_all_missing_covers(limit)
    return result


@router.get("/{filename}")
def serve_artwork(filename: str):
    """Serve cached artwork files."""
    file_path = ARTWORK_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Artwork not found")
    return FileResponse(file_path)
