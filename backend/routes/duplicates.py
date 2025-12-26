"""Duplicate detection routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services import DuplicateDetector, DuplicateResolver

router = APIRouter(prefix="/duplicates", tags=["Duplicates"])


@router.post("/scan")
def scan_duplicates(
    match_type: str = "metadata",
    min_similarity: float = 0.8,
    db: Session = Depends(get_db)
):
    """
    Scan library for duplicate tracks.

    match_type: 'exact' (file hash), 'metadata' (title/artist/duration), 'audio' (fingerprint)
    """
    detector = DuplicateDetector(db)
    try:
        return detector.scan_for_duplicates(match_type, min_similarity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
def get_duplicate_groups(
    reviewed: Optional[bool] = None,
    match_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all duplicate groups."""
    resolver = DuplicateResolver(db)
    return {"groups": resolver.get_duplicate_groups(reviewed, match_type)}


@router.get("/{group_id}")
def get_duplicate_group(group_id: str, db: Session = Depends(get_db)):
    """Get a duplicate group with all member tracks."""
    resolver = DuplicateResolver(db)
    group = resolver.get_duplicate_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.post("/{group_id}/resolve")
def resolve_duplicate(group_id: str, keep_track_id: str, db: Session = Depends(get_db)):
    """Mark a duplicate group as reviewed and select track to keep."""
    resolver = DuplicateResolver(db)
    if resolver.mark_reviewed(group_id, keep_track_id):
        return {"resolved": True}
    raise HTTPException(status_code=404, detail="Group not found")


@router.delete("/{group_id}")
def delete_duplicates(
    group_id: str,
    delete_files: bool = False,
    db: Session = Depends(get_db)
):
    """Delete duplicate tracks, keeping the primary one."""
    resolver = DuplicateResolver(db)
    result = resolver.delete_duplicates(group_id, delete_files)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/auto-resolve")
def auto_resolve_duplicates(
    delete_files: bool = False,
    match_types: Optional[list[str]] = None,
    db: Session = Depends(get_db)
):
    """Automatically resolve all unreviewed duplicate groups."""
    resolver = DuplicateResolver(db)
    return resolver.auto_resolve_duplicates(delete_files, match_types)


@router.get("/stats")
def get_duplicate_stats(db: Session = Depends(get_db)):
    """Get duplicate detection statistics."""
    detector = DuplicateDetector(db)
    return detector.get_stats()
