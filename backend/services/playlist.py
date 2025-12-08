"""Playlist management service."""

from pathlib import Path
from datetime import datetime
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models import Playlist, Track, playlist_tracks, Collection, collection_tracks
from services.scanner import MusicScanner, SUPPORTED_EXTENSIONS


class PlaylistService:
    """Service for managing playlists and collections."""

    def __init__(self, db: Session):
        self.db = db

    def create_playlist(
        self, name: str, description: Optional[str] = None
    ) -> Playlist:
        """Create a new empty playlist."""
        playlist = Playlist(name=name, description=description)
        self.db.add(playlist)
        self.db.commit()
        self.db.refresh(playlist)
        return playlist

    def create_playlist_from_folder(
        self,
        folder_path: str,
        name: Optional[str] = None,
    ) -> tuple[Playlist, int]:
        """
        Create a playlist from a folder dropped by user.

        This is the main entry point for drag-and-drop folder import.

        Returns:
            Tuple of (playlist, tracks_added)
        """
        path = Path(folder_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {folder_path}")

        # Use folder name if no name provided
        playlist_name = name or path.name

        # Create or find collection for this folder
        collection = self._get_or_create_collection(str(path), playlist_name)

        # Scan for tracks
        scanner = MusicScanner(self.db)
        scan_result = scanner.scan_directory(str(path), collection.id)

        # Update collection stats
        collection.track_count = scan_result["added"] + scan_result.get("updated", 0)
        collection.last_scanned = datetime.utcnow()

        # Get all tracks from this collection
        track_ids = (
            self.db.query(collection_tracks.c.track_id)
            .filter(collection_tracks.c.collection_id == collection.id)
            .all()
        )
        track_ids = [t[0] for t in track_ids]

        # Create playlist with these tracks
        playlist = Playlist(name=playlist_name)
        self.db.add(playlist)
        self.db.flush()

        # Add tracks to playlist in order
        for i, track_id in enumerate(track_ids):
            self.db.execute(
                playlist_tracks.insert().values(
                    playlist_id=playlist.id,
                    track_id=track_id,
                    position=i,
                )
            )

        collection.total_duration = (
            self.db.query(func.sum(Track.duration))
            .filter(Track.id.in_(track_ids))
            .scalar()
            or 0
        )

        self.db.commit()
        self.db.refresh(playlist)

        return playlist, len(track_ids)

    def _get_or_create_collection(self, path: str, name: str) -> Collection:
        """Get existing collection or create new one."""
        collection = (
            self.db.query(Collection).filter(Collection.path == path).first()
        )
        if not collection:
            collection = Collection(name=name, path=path)
            self.db.add(collection)
            self.db.flush()
        return collection

    def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """Get playlist with tracks."""
        playlist = (
            self.db.query(Playlist)
            .options(joinedload(Playlist.tracks).joinedload(Track.artist))
            .options(joinedload(Playlist.tracks).joinedload(Track.album))
            .filter(Playlist.id == playlist_id)
            .first()
        )
        return playlist

    def get_all_playlists(self) -> list[Playlist]:
        """Get all playlists with track counts."""
        playlists = self.db.query(Playlist).all()

        # Add computed fields
        for pl in playlists:
            pl.track_count = (
                self.db.query(playlist_tracks)
                .filter(playlist_tracks.c.playlist_id == pl.id)
                .count()
            )
            pl.total_duration = (
                self.db.query(func.sum(Track.duration))
                .join(playlist_tracks)
                .filter(playlist_tracks.c.playlist_id == pl.id)
                .scalar()
                or 0
            )

        return playlists

    def update_playlist(
        self,
        playlist_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Playlist:
        """Update playlist metadata."""
        playlist = (
            self.db.query(Playlist).filter(Playlist.id == playlist_id).first()
        )
        if not playlist:
            raise ValueError(f"Playlist not found: {playlist_id}")

        if name is not None:
            playlist.name = name
        if description is not None:
            playlist.description = description

        playlist.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(playlist)
        return playlist

    def delete_playlist(self, playlist_id: str) -> bool:
        """Delete a playlist (doesn't delete tracks)."""
        playlist = (
            self.db.query(Playlist).filter(Playlist.id == playlist_id).first()
        )
        if not playlist:
            return False

        # Remove track associations
        self.db.execute(
            playlist_tracks.delete().where(
                playlist_tracks.c.playlist_id == playlist_id
            )
        )

        self.db.delete(playlist)
        self.db.commit()
        return True

    def add_track_to_playlist(
        self, playlist_id: str, track_id: str, position: Optional[int] = None
    ) -> bool:
        """Add a track to a playlist."""
        playlist = (
            self.db.query(Playlist).filter(Playlist.id == playlist_id).first()
        )
        track = self.db.query(Track).filter(Track.id == track_id).first()

        if not playlist or not track:
            return False

        # Check if already in playlist
        existing = (
            self.db.query(playlist_tracks)
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
                self.db.query(func.max(playlist_tracks.c.position))
                .filter(playlist_tracks.c.playlist_id == playlist_id)
                .scalar()
            )
            position = (max_pos or 0) + 1

        self.db.execute(
            playlist_tracks.insert().values(
                playlist_id=playlist_id,
                track_id=track_id,
                position=position,
            )
        )

        playlist.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def remove_track_from_playlist(
        self, playlist_id: str, track_id: str
    ) -> bool:
        """Remove a track from a playlist."""
        result = self.db.execute(
            playlist_tracks.delete().where(
                playlist_tracks.c.playlist_id == playlist_id,
                playlist_tracks.c.track_id == track_id,
            )
        )

        if result.rowcount > 0:
            playlist = (
                self.db.query(Playlist)
                .filter(Playlist.id == playlist_id)
                .first()
            )
            if playlist:
                playlist.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def reorder_playlist(
        self, playlist_id: str, track_ids: list[str]
    ) -> Playlist:
        """Reorder tracks in a playlist."""
        playlist = (
            self.db.query(Playlist).filter(Playlist.id == playlist_id).first()
        )
        if not playlist:
            raise ValueError(f"Playlist not found: {playlist_id}")

        # Remove all existing positions
        self.db.execute(
            playlist_tracks.delete().where(
                playlist_tracks.c.playlist_id == playlist_id
            )
        )

        # Add tracks in new order
        for i, track_id in enumerate(track_ids):
            self.db.execute(
                playlist_tracks.insert().values(
                    playlist_id=playlist_id,
                    track_id=track_id,
                    position=i,
                )
            )

        playlist.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(playlist)
        return playlist

    def add_folder_to_playlist(
        self, playlist_id: str, folder_path: str
    ) -> int:
        """
        Add all tracks from a folder to existing playlist.

        Returns number of tracks added.
        """
        playlist = (
            self.db.query(Playlist).filter(Playlist.id == playlist_id).first()
        )
        if not playlist:
            raise ValueError(f"Playlist not found: {playlist_id}")

        path = Path(folder_path).expanduser().resolve()
        if not path.exists() or not path.is_dir():
            raise ValueError(f"Invalid folder: {folder_path}")

        # Scan folder
        scanner = MusicScanner(self.db)
        scan_result = scanner.scan_directory(str(path))

        # Find tracks that were just added from this folder
        added_tracks = (
            self.db.query(Track)
            .filter(Track.path.like(f"{path}%"))
            .all()
        )

        # Get current max position
        max_pos = (
            self.db.query(func.max(playlist_tracks.c.position))
            .filter(playlist_tracks.c.playlist_id == playlist_id)
            .scalar()
        ) or 0

        added_count = 0
        for track in added_tracks:
            # Check if already in playlist
            existing = (
                self.db.query(playlist_tracks)
                .filter(
                    playlist_tracks.c.playlist_id == playlist_id,
                    playlist_tracks.c.track_id == track.id,
                )
                .first()
            )
            if not existing:
                max_pos += 1
                self.db.execute(
                    playlist_tracks.insert().values(
                        playlist_id=playlist_id,
                        track_id=track.id,
                        position=max_pos,
                    )
                )
                added_count += 1

        playlist.updated_at = datetime.utcnow()
        self.db.commit()
        return added_count

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
