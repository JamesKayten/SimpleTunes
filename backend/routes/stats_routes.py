"""Statistics API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas import LibraryStats
from services import LibraryService

router = APIRouter(tags=["Statistics"])


@router.get("/stats", response_model=LibraryStats)
def get_stats(db: Session = Depends(get_db)):
    """Get library statistics."""
    service = LibraryService(db)
    return service.get_stats()
