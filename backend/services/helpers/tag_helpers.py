"""Helper functions for tag writing."""

from typing import Optional
from sqlalchemy.orm import Session

from models import Artist, Album


class TagHelper:
    """Helper class for tag writing operations."""

    @staticmethod
    def get_or_create_artist(db: Session, name: str) -> Artist:
        """Get or create artist by name."""
        artist = (
            db.query(Artist)
            .filter(Artist.name.ilike(name))
            .first()
        )
        if not artist:
            artist = Artist(name=name)
            db.add(artist)
            db.flush()
        return artist

    @staticmethod
    def get_or_create_album(
        db: Session,
        title: str,
        artist_id: Optional[str],
        year: Optional[int],
        genre: Optional[str],
    ) -> Album:
        """Get or create album by title and artist."""
        query = db.query(Album).filter(Album.title.ilike(title))
        if artist_id:
            query = query.filter(Album.artist_id == artist_id)
        album = query.first()

        if not album:
            album = Album(
                title=title,
                artist_id=artist_id,
                year=year,
                genre=genre,
            )
            db.add(album)
            db.flush()
        return album
