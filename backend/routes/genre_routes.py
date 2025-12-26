"""Genre and year browsing API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from services import LibraryService

router = APIRouter(tags=["Genres & Years"])


@router.get("/genres")
def get_genres(db: Session = Depends(get_db)):
    """Get all genres with track counts."""
    service = LibraryService(db)
    return {"genres": service.get_genres()}


@router.get("/years")
def get_years(db: Session = Depends(get_db)):
    """Get all years with track counts."""
    service = LibraryService(db)
    return {"years": service.get_years()}


@router.get("/decades")
def get_decades(db: Session = Depends(get_db)):
    """Get decades with track counts."""
    service = LibraryService(db)
    return {"decades": service.get_decades()}
