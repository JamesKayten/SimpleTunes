"""Basic playlist management service."""

from pathlib import Path
from datetime import datetime
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models import Playlist, Track, playlist_tracks
from .helpers.playlist_folder import PlaylistFolderImporter


class PlaylistService:
    """Service for managing playlists."""

    def __init__(self, db: Session):
        self.db = db
        self.folder_importer = PlaylistFolderImporter(db)

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
        collection = self.folder_importer.get_or_create_collection(str(path), playlist_name)

        # Scan folder and get track IDs
        scan_result, track_ids = self.folder_importer.scan_folder(str(path), collection.id)

        # Update collection stats
        self.folder_importer.update_collection_stats(collection, track_ids)

        # Create playlist with these tracks
        playlist = Playlist(name=playlist_name)
        self.db.add(playlist)
        self.db.flush()

        # Add tracks to playlist
        self.folder_importer.add_tracks_to_playlist(playlist.id, track_ids, starting_position=0)

        self.db.commit()
        self.db.refresh(playlist)

        return playlist, len(track_ids)

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
        return PlaylistFolderImporter.add_single_track(self.db, playlist_id, track_id, position)

    def remove_track_from_playlist(
        self, playlist_id: str, track_id: str
    ) -> bool:
        """Remove a track from a playlist."""
        return PlaylistFolderImporter.remove_track(self.db, playlist_id, track_id)

    def reorder_playlist(
        self, playlist_id: str, track_ids: list[str]
    ) -> Playlist:
        """Reorder tracks in a playlist."""
        return PlaylistFolderImporter.reorder_tracks(self.db, playlist_id, track_ids)

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

        # Scan folder and get track IDs
        scan_result, track_ids = self.folder_importer.scan_folder(str(path))

        # Add tracks to playlist
        added_count = self.folder_importer.add_tracks_to_playlist(playlist_id, track_ids)

        playlist.updated_at = datetime.utcnow()
        self.db.commit()
        return added_count
