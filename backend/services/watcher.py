"""Folder watching service for auto-importing new music."""

import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
from watchdog.observers import Observer
from sqlalchemy.orm import Session

from models import WatchFolder, WatchEvent, Track
from services.scanner import MusicScanner, SUPPORTED_EXTENSIONS
from database import get_db_session
from .watcher_processor import MusicFileHandler, WatchEventProcessor


class FolderWatcherService:
    """Service for watching folders and auto-importing new music."""

    def __init__(self, db: Session):
        self.db = db
        self._observer = None
        self._handlers = {}
        self._event_queue = asyncio.Queue()
        self._running = False

    def add_watch_folder(
        self,
        path: str,
        name: Optional[str] = None,
        auto_import: bool = True,
        create_playlist: bool = False,
    ) -> WatchFolder:
        """Add a folder to watch for new music."""
        folder_path = Path(path).expanduser().resolve()
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {path}")
        if not folder_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        # Check if already watching
        existing = (
            self.db.query(WatchFolder)
            .filter(WatchFolder.path == str(folder_path))
            .first()
        )
        if existing:
            return existing

        # Count existing files
        file_count = sum(
            1 for f in folder_path.rglob("*")
            if f.suffix.lower() in SUPPORTED_EXTENSIONS
        )

        watch_folder = WatchFolder(
            path=str(folder_path),
            name=name or folder_path.name,
            auto_import=auto_import,
            create_playlist=create_playlist,
            file_count=file_count,
        )
        self.db.add(watch_folder)
        self.db.commit()
        self.db.refresh(watch_folder)

        return watch_folder

    def remove_watch_folder(self, folder_id: str) -> bool:
        """Remove a watch folder."""
        folder = (
            self.db.query(WatchFolder)
            .filter(WatchFolder.id == folder_id)
            .first()
        )
        if not folder:
            return False

        # Stop watching if active
        if folder_id in self._handlers:
            self._stop_watching_folder(folder_id)

        # Delete events
        self.db.query(WatchEvent).filter(
            WatchEvent.watch_folder_id == folder_id
        ).delete()

        self.db.delete(folder)
        self.db.commit()
        return True

    def get_watch_folders(self) -> list[WatchFolder]:
        """Get all watch folders."""
        return self.db.query(WatchFolder).all()

    def get_watch_folder(self, folder_id: str) -> Optional[WatchFolder]:
        """Get a specific watch folder."""
        return (
            self.db.query(WatchFolder)
            .filter(WatchFolder.id == folder_id)
            .first()
        )

    def update_watch_folder(
        self,
        folder_id: str,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
        auto_import: Optional[bool] = None,
        create_playlist: Optional[bool] = None,
    ) -> Optional[WatchFolder]:
        """Update watch folder settings."""
        folder = self.get_watch_folder(folder_id)
        if not folder:
            return None

        if name is not None:
            folder.name = name
        if enabled is not None:
            folder.enabled = enabled
            if enabled and folder_id not in self._handlers:
                self._start_watching_folder(folder)
            elif not enabled and folder_id in self._handlers:
                self._stop_watching_folder(folder_id)
        if auto_import is not None:
            folder.auto_import = auto_import
        if create_playlist is not None:
            folder.create_playlist = create_playlist

        self.db.commit()
        self.db.refresh(folder)
        return folder

    def start_watching(self):
        """Start watching all enabled folders."""
        if self._running:
            return

        self._observer = Observer()
        self._running = True

        folders = (
            self.db.query(WatchFolder)
            .filter(WatchFolder.enabled == True)
            .all()
        )

        for folder in folders:
            self._start_watching_folder(folder)

        self._observer.start()

    def stop_watching(self):
        """Stop watching all folders."""
        if not self._running:
            return

        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None

        self._handlers.clear()

    def _start_watching_folder(self, folder: WatchFolder):
        """Start watching a specific folder."""
        if not self._observer:
            return

        if not Path(folder.path).exists():
            return

        handler = MusicFileHandler(folder.id, self._handle_event)
        watch = self._observer.schedule(handler, folder.path, recursive=True)
        self._handlers[folder.id] = (handler, watch)

    def _stop_watching_folder(self, folder_id: str):
        """Stop watching a specific folder."""
        if folder_id not in self._handlers:
            return

        handler, watch = self._handlers[folder_id]
        if self._observer:
            self._observer.unschedule(watch)
        del self._handlers[folder_id]

    def _handle_event(self, watch_folder_id: str, event_type: str, file_path: str):
        """Handle a file system event."""
        # Record event
        with get_db_session() as db:
            event = WatchEvent(
                watch_folder_id=watch_folder_id,
                event_type=event_type,
                file_path=file_path,
            )
            db.add(event)

            folder = (
                db.query(WatchFolder)
                .filter(WatchFolder.id == watch_folder_id)
                .first()
            )

            if folder and folder.auto_import:
                WatchEventProcessor.process_event(db, folder, event)

            db.commit()

    def get_events(
        self,
        folder_id: Optional[str] = None,
        processed: Optional[bool] = None,
        limit: int = 100,
    ) -> list[WatchEvent]:
        """Get watch events."""
        return WatchEventProcessor.get_events(self.db, folder_id, processed, limit)

    def process_pending_events(self) -> dict:
        """Process any pending (unprocessed) events."""
        return WatchEventProcessor.process_pending_events(self.db)

    def rescan_folder(self, folder_id: str) -> dict:
        """Rescan a watch folder for changes."""
        return WatchEventProcessor.rescan_folder(self.db, folder_id)

    def check_for_removed_tracks(self) -> dict:
        """Check for tracks whose files no longer exist."""
        return WatchEventProcessor.check_for_removed_tracks(self.db)

    def cleanup_missing_tracks(self, delete: bool = False) -> dict:
        """Remove or mark tracks whose files are missing."""
        return WatchEventProcessor.cleanup_missing_tracks(self.db, delete)

    def get_stats(self) -> dict:
        """Get folder watching statistics."""
        return WatchEventProcessor.get_stats(self.db, self._running)


# Global watcher instance
_watcher_instance: Optional[FolderWatcherService] = None


def get_watcher(db: Session) -> FolderWatcherService:
    """Get or create the global folder watcher."""
    global _watcher_instance
    if _watcher_instance is None:
        _watcher_instance = FolderWatcherService(db)
    return _watcher_instance
