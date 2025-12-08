"""Folder watching routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from database import get_db
from services import FolderWatcherService

router = APIRouter(prefix="/watch", tags=["Folder Watching"])


class WatchFolderRequest(BaseModel):
    path: str
    name: Optional[str] = None
    auto_import: bool = True
    create_playlist: bool = False


class WatchFolderUpdateRequest(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    auto_import: Optional[bool] = None
    create_playlist: Optional[bool] = None


def _folder_to_response(folder) -> dict:
    return {
        "id": folder.id,
        "path": folder.path,
        "name": folder.name,
        "enabled": folder.enabled,
        "auto_import": folder.auto_import,
        "create_playlist": folder.create_playlist,
        "file_count": folder.file_count,
        "last_checked": folder.last_checked.isoformat() if folder.last_checked else None,
        "created_at": folder.created_at.isoformat() if folder.created_at else None,
    }


@router.get("")
def get_watch_folders(db: Session = Depends(get_db)):
    """Get all watch folders."""
    service = FolderWatcherService(db)
    folders = service.get_watch_folders()
    return {"folders": [_folder_to_response(f) for f in folders]}


@router.post("")
def add_watch_folder(request: WatchFolderRequest, db: Session = Depends(get_db)):
    """Add a folder to watch for new music."""
    service = FolderWatcherService(db)
    try:
        folder = service.add_watch_folder(
            request.path, request.name, request.auto_import, request.create_playlist
        )
        return _folder_to_response(folder)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{folder_id}")
def get_watch_folder(folder_id: str, db: Session = Depends(get_db)):
    """Get a specific watch folder."""
    service = FolderWatcherService(db)
    folder = service.get_watch_folder(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return _folder_to_response(folder)


@router.put("/{folder_id}")
def update_watch_folder(
    folder_id: str, request: WatchFolderUpdateRequest, db: Session = Depends(get_db)
):
    """Update watch folder settings."""
    service = FolderWatcherService(db)
    folder = service.update_watch_folder(
        folder_id, request.name, request.enabled, request.auto_import, request.create_playlist
    )
    if folder:
        return _folder_to_response(folder)
    raise HTTPException(status_code=404, detail="Folder not found")


@router.delete("/{folder_id}")
def remove_watch_folder(folder_id: str, db: Session = Depends(get_db)):
    """Remove a watch folder."""
    service = FolderWatcherService(db)
    if service.remove_watch_folder(folder_id):
        return {"removed": True}
    raise HTTPException(status_code=404, detail="Folder not found")


@router.post("/{folder_id}/rescan")
def rescan_watch_folder(folder_id: str, db: Session = Depends(get_db)):
    """Rescan a watch folder for changes."""
    service = FolderWatcherService(db)
    result = service.rescan_folder(folder_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/events")
def get_watch_events(
    folder_id: Optional[str] = None,
    processed: Optional[bool] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get watch folder events."""
    service = FolderWatcherService(db)
    events = service.get_events(folder_id, processed, limit)
    return {
        "events": [
            {
                "id": e.id,
                "watch_folder_id": e.watch_folder_id,
                "event_type": e.event_type,
                "file_path": e.file_path,
                "track_id": e.track_id,
                "processed": e.processed,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]
    }


@router.post("/events/process")
def process_pending_events(db: Session = Depends(get_db)):
    """Process any pending (unprocessed) events."""
    service = FolderWatcherService(db)
    return service.process_pending_events()


@router.get("/stats")
def get_watch_stats(db: Session = Depends(get_db)):
    """Get folder watching statistics."""
    service = FolderWatcherService(db)
    return service.get_stats()


@router.get("/missing")
def check_missing_tracks(db: Session = Depends(get_db)):
    """Check for tracks whose files no longer exist."""
    service = FolderWatcherService(db)
    return service.check_for_removed_tracks()


@router.post("/cleanup")
def cleanup_missing_tracks(delete: bool = False, db: Session = Depends(get_db)):
    """Remove or mark tracks with missing files."""
    service = FolderWatcherService(db)
    return service.cleanup_missing_tracks(delete)
