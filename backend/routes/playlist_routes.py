"""Playlist management API routes."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from schemas import (
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistResponse,
    PlaylistFromFolderRequest,
)
from services import PlaylistService
from response_helpers import playlist_to_response, track_to_response

router = APIRouter(prefix="/playlists", tags=["Playlists"])


@router.get("")
def get_playlists(db: Session = Depends(get_db)):
    """Get all playlists."""
    service = PlaylistService(db)
    playlists = service.get_all_playlists()
    return {"playlists": [playlist_to_response(p) for p in playlists]}


@router.post("", response_model=PlaylistResponse)
def create_playlist(request: PlaylistCreate, db: Session = Depends(get_db)):
    """Create a new empty playlist."""
    service = PlaylistService(db)
    playlist = service.create_playlist(request.name, request.description)
    return playlist_to_response(playlist)


@router.post("/from-folder")
def create_playlist_from_folder(
    request: PlaylistFromFolderRequest, db: Session = Depends(get_db)
):
    """Create a playlist from a dropped folder."""
    service = PlaylistService(db)
    try:
        playlist, tracks_added = service.create_playlist_from_folder(
            request.folder_path, request.name
        )
        return {
            "playlist": playlist_to_response(playlist),
            "tracks_added": tracks_added,
        }
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{playlist_id}")
def get_playlist(playlist_id: str, db: Session = Depends(get_db)):
    """Get playlist with tracks."""
    service = PlaylistService(db)
    playlist = service.get_playlist(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return {
        **playlist_to_response(playlist),
        "tracks": [track_to_response(t) for t in playlist.tracks],
    }


@router.put("/{playlist_id}", response_model=PlaylistResponse)
def update_playlist(
    playlist_id: str, request: PlaylistUpdate, db: Session = Depends(get_db)
):
    """Update playlist metadata."""
    service = PlaylistService(db)
    try:
        playlist = service.update_playlist(
            playlist_id, request.name, request.description
        )
        return playlist_to_response(playlist)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{playlist_id}")
def delete_playlist(playlist_id: str, db: Session = Depends(get_db)):
    """Delete a playlist."""
    service = PlaylistService(db)
    if service.delete_playlist(playlist_id):
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="Playlist not found")


@router.post("/{playlist_id}/tracks/{track_id}")
def add_track_to_playlist(
    playlist_id: str,
    track_id: str,
    position: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Add a track to a playlist."""
    service = PlaylistService(db)
    if service.add_track_to_playlist(playlist_id, track_id, position):
        return {"added": True}
    raise HTTPException(status_code=404, detail="Playlist or track not found")


@router.delete("/{playlist_id}/tracks/{track_id}")
def remove_track_from_playlist(
    playlist_id: str, track_id: str, db: Session = Depends(get_db)
):
    """Remove a track from a playlist."""
    service = PlaylistService(db)
    if service.remove_track_from_playlist(playlist_id, track_id):
        return {"removed": True}
    raise HTTPException(status_code=404, detail="Track not in playlist")


@router.put("/{playlist_id}/reorder")
def reorder_playlist(
    playlist_id: str, track_ids: list[str], db: Session = Depends(get_db)
):
    """Reorder tracks in a playlist."""
    service = PlaylistService(db)
    try:
        playlist = service.reorder_playlist(playlist_id, track_ids)
        return {"reordered": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{playlist_id}/add-folder")
def add_folder_to_playlist(
    playlist_id: str, folder_path: str, db: Session = Depends(get_db)
):
    """Add all tracks from a folder to an existing playlist."""
    service = PlaylistService(db)
    try:
        added = service.add_folder_to_playlist(playlist_id, folder_path)
        return {"added": added}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
