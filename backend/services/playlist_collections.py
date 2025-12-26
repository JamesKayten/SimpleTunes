"""Collection management service."""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session, joinedload

from models import Collection, Track, collection_tracks, playlist_tracks
from services.scanner import MusicScanner


class CollectionService:
    """Service for managing music collections (imported folders)."""

    def __init__(self, db: Session):
        self.db = db

    def get_collections(self) -> list[Collection]:
        """Get all imported collections."""
        return self.db.query(Collection).order_by(Collection.created_at.desc()).all()

    def get_collection_tracks(self, collection_id: str) -> list[Track]:
        """Get all tracks in a collection."""
        track_ids = (
            self.db.query(collection_tracks.c.track_id)
            .filter(collection_tracks.c.collection_id == collection_id)
            .all()
        )
        track_ids = [t[0] for t in track_ids]

        return (
            self.db.query(Track)
            .filter(Track.id.in_(track_ids))
            .options(joinedload(Track.artist), joinedload(Track.album))
            .all()
        )

    def rescan_collection(self, collection_id: str) -> dict:
        """Rescan a collection for new/changed tracks."""
        collection = (
            self.db.query(Collection)
            .filter(Collection.id == collection_id)
            .first()
        )
        if not collection:
            raise ValueError(f"Collection not found: {collection_id}")

        scanner = MusicScanner(self.db)
        result = scanner.scan_directory(collection.path, collection_id)

        collection.last_scanned = datetime.utcnow()
        collection.track_count = (
            self.db.query(collection_tracks)
            .filter(collection_tracks.c.collection_id == collection_id)
            .count()
        )
        self.db.commit()

        return result

    def delete_collection(
        self, collection_id: str, delete_tracks: bool = False
    ) -> bool:
        """
        Delete a collection.

        Args:
            collection_id: Collection to delete
            delete_tracks: If True, also delete tracks from library

        Returns:
            True if deleted
        """
        collection = (
            self.db.query(Collection)
            .filter(Collection.id == collection_id)
            .first()
        )
        if not collection:
            return False

        if delete_tracks:
            # Get track IDs in this collection
            track_ids = (
                self.db.query(collection_tracks.c.track_id)
                .filter(collection_tracks.c.collection_id == collection_id)
                .all()
            )
            track_ids = [t[0] for t in track_ids]

            # Remove from all playlists
            self.db.execute(
                playlist_tracks.delete().where(
                    playlist_tracks.c.track_id.in_(track_ids)
                )
            )

            # Delete tracks
            self.db.query(Track).filter(Track.id.in_(track_ids)).delete(
                synchronize_session=False
            )

        # Remove collection track associations
        self.db.execute(
            collection_tracks.delete().where(
                collection_tracks.c.collection_id == collection_id
            )
        )

        self.db.delete(collection)
        self.db.commit()
        return True
