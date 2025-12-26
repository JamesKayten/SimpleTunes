"""Helper functions for importing folders into playlists."""

from pathlib import Path
from datetime import datetime
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Collection, Track, collection_tracks, playlist_tracks
from services.scanner import MusicScanner


class PlaylistFolderImporter:
    """Helper class for importing folders into playlists."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_collection(self, path: str, name: str) -> Collection:
        """Get existing collection or create new one."""
        collection = (
            self.db.query(Collection).filter(Collection.path == path).first()
        )
        if not collection:
            collection = Collection(name=name, path=path)
            self.db.add(collection)
            self.db.flush()
        return collection

    def scan_folder(self, folder_path: str, collection_id: Optional[str] = None) -> tuple[dict, list[str]]:
        """
        Scan folder and return scan result and track IDs.

        Returns:
            Tuple of (scan_result, track_ids)
        """
        path = Path(folder_path).expanduser().resolve()

        # Scan for tracks
        scanner = MusicScanner(self.db)
        scan_result = scanner.scan_directory(str(path), collection_id)

        # Get all tracks from this folder
        track_ids = self._get_tracks_from_path(str(path), collection_id)

        return scan_result, track_ids

    def _get_tracks_from_path(self, path: str, collection_id: Optional[str] = None) -> list[str]:
        """Get track IDs from a given path."""
        if collection_id:
            # Get tracks from collection
            track_ids = (
                self.db.query(collection_tracks.c.track_id)
                .filter(collection_tracks.c.collection_id == collection_id)
                .all()
            )
        else:
            # Get tracks by path matching
            tracks = (
                self.db.query(Track)
                .filter(Track.path.like(f"{path}%"))
                .all()
            )
            track_ids = [(t.id,) for t in tracks]

        return [t[0] for t in track_ids]

    def add_tracks_to_playlist(
        self,
        playlist_id: str,
        track_ids: list[str],
        starting_position: Optional[int] = None,
    ) -> int:
        """
        Add tracks to playlist, returning count of tracks added.

        Args:
            playlist_id: Playlist to add to
            track_ids: List of track IDs to add
            starting_position: Position to start adding at (if None, appends)

        Returns:
            Number of tracks added
        """
        # Get current max position if needed
        if starting_position is None:
            max_pos = (
                self.db.query(func.max(playlist_tracks.c.position))
                .filter(playlist_tracks.c.playlist_id == playlist_id)
                .scalar()
            ) or 0
            position = max_pos
        else:
            position = starting_position - 1

        added_count = 0
        for track_id in track_ids:
            # Check if already in playlist
            existing = (
                self.db.query(playlist_tracks)
                .filter(
                    playlist_tracks.c.playlist_id == playlist_id,
                    playlist_tracks.c.track_id == track_id,
                )
                .first()
            )
            if not existing:
                position += 1
                self.db.execute(
                    playlist_tracks.insert().values(
                        playlist_id=playlist_id,
                        track_id=track_id,
                        position=position,
                    )
                )
                added_count += 1

        return added_count

    def update_collection_stats(self, collection: Collection, track_ids: list[str]) -> None:
        """Update collection statistics."""
        collection.track_count = len(track_ids)
        collection.last_scanned = datetime.utcnow()
        collection.total_duration = (
            self.db.query(func.sum(Track.duration))
            .filter(Track.id.in_(track_ids))
            .scalar()
            or 0
        )

    @staticmethod
    def add_single_track(
        db: Session,
        playlist_id: str,
        track_id: str,
        position: Optional[int] = None,
    ) -> bool:
        """Add a single track to a playlist."""
        from models import Playlist, Track, playlist_tracks

        playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
        track = db.query(Track).filter(Track.id == track_id).first()

        if not playlist or not track:
            return False

        # Check if already in playlist
        existing = (
            db.query(playlist_tracks)
            .filter(
                playlist_tracks.c.playlist_id == playlist_id,
                playlist_tracks.c.track_id == track_id,
            )
            .first()
        )
        if existing:
            return True  # Already in playlist

        # Get current max position
        if position is None:
            max_pos = (
                db.query(func.max(playlist_tracks.c.position))
                .filter(playlist_tracks.c.playlist_id == playlist_id)
                .scalar()
            )
            position = (max_pos or 0) + 1

        db.execute(
            playlist_tracks.insert().values(
                playlist_id=playlist_id,
                track_id=track_id,
                position=position,
            )
        )

        playlist.updated_at = datetime.utcnow()
        db.commit()
        return True

    @staticmethod
    def remove_track(db: Session, playlist_id: str, track_id: str) -> bool:
        """Remove a track from a playlist."""
        from models import Playlist, playlist_tracks

        result = db.execute(
            playlist_tracks.delete().where(
                playlist_tracks.c.playlist_id == playlist_id,
                playlist_tracks.c.track_id == track_id,
            )
        )

        if result.rowcount > 0:
            playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
            if playlist:
                playlist.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False

    @staticmethod
    def reorder_tracks(db: Session, playlist_id: str, track_ids: list[str]):
        """Reorder tracks in a playlist."""
        from models import Playlist, playlist_tracks

        playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
        if not playlist:
            raise ValueError(f"Playlist not found: {playlist_id}")

        # Remove all existing positions
        db.execute(
            playlist_tracks.delete().where(
                playlist_tracks.c.playlist_id == playlist_id
            )
        )

        # Add tracks in new order
        for i, track_id in enumerate(track_ids):
            db.execute(
                playlist_tracks.insert().values(
                    playlist_id=playlist_id,
                    track_id=track_id,
                    position=i,
                )
            )

        playlist.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(playlist)
        return playlist
