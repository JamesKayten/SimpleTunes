"""Library scanning and import API routes."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas import ScanRequest, ScanResponse, ImportFolderRequest, ImportResponse
from services import MusicScanner, PlaylistService

router = APIRouter(prefix="/library", tags=["Library"])


@router.post("/scan", response_model=ScanResponse)
def scan_directory(request: ScanRequest, db: Session = Depends(get_db)):
    """Scan a directory for music files."""
    try:
        scanner = MusicScanner(db)
        result = scanner.scan_directory(request.directory)
        return ScanResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/import", response_model=ImportResponse)
def import_folder(request: ImportFolderRequest, db: Session = Depends(get_db)):
    """Import a folder and optionally create a playlist."""
    try:
        playlist_service = PlaylistService(db)

        if request.create_playlist:
            playlist, tracks_added = playlist_service.create_playlist_from_folder(
                request.folder_path, request.playlist_name
            )
            return ImportResponse(
                collection_id=playlist.id,  # Using playlist as collection reference
                playlist_id=playlist.id,
                tracks_added=tracks_added,
                total_tracks=tracks_added,
            )
        else:
            scanner = MusicScanner(db)
            result = scanner.scan_directory(request.folder_path)
            return ImportResponse(
                collection_id="",
                playlist_id=None,
                tracks_added=result["added"],
                total_tracks=result["total"],
            )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
