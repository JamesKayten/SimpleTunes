"""Collection management API routes."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from services import CollectionService
from response_helpers import collection_to_response, track_to_response

router = APIRouter(prefix="/collections", tags=["Collections"])


@router.get("")
def get_collections(db: Session = Depends(get_db)):
    """Get all imported collections."""
    service = CollectionService(db)
    collections = service.get_collections()
    return {"collections": [collection_to_response(c) for c in collections]}


@router.get("/{collection_id}/tracks")
def get_collection_tracks(collection_id: str, db: Session = Depends(get_db)):
    """Get all tracks in a collection."""
    service = CollectionService(db)
    tracks = service.get_collection_tracks(collection_id)
    return {"tracks": [track_to_response(t) for t in tracks]}


@router.post("/{collection_id}/rescan")
def rescan_collection(collection_id: str, db: Session = Depends(get_db)):
    """Rescan a collection for new/changed tracks."""
    service = CollectionService(db)
    try:
        result = service.rescan_collection(collection_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{collection_id}")
def delete_collection(
    collection_id: str,
    delete_tracks: bool = False,
    db: Session = Depends(get_db),
):
    """Delete a collection."""
    service = CollectionService(db)
    if service.delete_collection(collection_id, delete_tracks):
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="Collection not found")
