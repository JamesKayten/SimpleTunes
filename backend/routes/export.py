"""Playlist export routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from database import get_db
from services import PlaylistExportService

router = APIRouter(prefix="/export", tags=["Export/Import"])


class ExportRequest(BaseModel):
    format: str = "m3u"
    output_path: Optional[str] = None
    relative_paths: bool = False
    base_path: Optional[str] = None


class ImportRequest(BaseModel):
    file_path: str
    name: Optional[str] = None


@router.post("/playlist/{playlist_id}")
def export_playlist(playlist_id: str, request: ExportRequest, db: Session = Depends(get_db)):
    """Export a playlist to file (M3U, M3U8, PLS, XSPF, JSON)."""
    service = PlaylistExportService(db)
    result = service.export_playlist(
        playlist_id,
        format=request.format,
        output_path=request.output_path,
        relative_paths=request.relative_paths,
        base_path=request.base_path,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/library")
def export_library(format: str = "json", db: Session = Depends(get_db)):
    """Export entire library metadata to JSON or CSV."""
    service = PlaylistExportService(db)
    result = service.export_library(format)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/import/playlist")
def import_playlist(request: ImportRequest, db: Session = Depends(get_db)):
    """Import a playlist from file (M3U, M3U8, PLS)."""
    service = PlaylistExportService(db)
    result = service.import_playlist(request.file_path, request.name)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/files")
def list_exports(db: Session = Depends(get_db)):
    """List all exported files."""
    service = PlaylistExportService(db)
    return {"exports": service.get_exports()}


@router.delete("/files/{filename}")
def delete_export(filename: str, db: Session = Depends(get_db)):
    """Delete an exported file."""
    service = PlaylistExportService(db)
    if service.delete_export(filename):
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="File not found")
