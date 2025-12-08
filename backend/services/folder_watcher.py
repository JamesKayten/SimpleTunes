"""Folder watching service for auto-importing new music."""

import asyncio
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, FileDeletedEvent
from sqlalchemy.orm import Session

from models import WatchFolder, WatchEvent, Track
from services.scanner import MusicScanner, SUPPORTED_EXTENSIONS
from database import get_db_session


class MusicFileHandler(FileSystemEventHandler):
    """Handles file system events for music files."""

    def __init__(
        self,
        watch_folder_id: str,
        on_event: Callable[[str, str, str], None],
    ):
        self.watch_folder_id = watch_folder_id
        self.on_event = on_event
        self._debounce_timers = {}
        self._debounce_delay = 2.0  # seconds

    def _is_music_file(self, path: str) -> bool:
        """Check if path is a supported music file."""
        return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS

    def _debounced_event(self, event_type: str, path: str):
        """Debounce events to avoid processing during file copies."""
        key = f"{event_type}:{path}"

        # Cancel existing timer
        if key in self._debounce_timers:
            self._debounce_timers[key].cancel()

        # Set new timer
        timer = threading.Timer(
            self._debounce_delay,
            lambda: self.on_event(self.watch_folder_id, event_type, path)
        )
        self._debounce_timers[key] = timer
        timer.start()

    def on_created(self, event):
        if not event.is_directory and self._is_music_file(event.src_path):
            self._debounced_event("added", event.src_path)

    def on_modified(self, event):
        if not event.is_directory and self._is_music_file(event.src_path):
            self._debounced_event("modified", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory and self._is_music_file(event.src_path):
            # No debounce for deletions
            self.on_event(self.watch_folder_id, "deleted", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            if self._is_music_file(event.src_path):
                self.on_event(self.watch_folder_id, "deleted", event.src_path)
            if self._is_music_file(event.dest_path):
                self._debounced_event("added", event.dest_path)


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
                self._process_event(db, folder, event)

            db.commit()

    def _process_event(
        self,
        db: Session,
        folder: WatchFolder,
        event: WatchEvent,
    ):
        """Process a file system event."""
        if event.event_type == "added":
            # Import new track
            scanner = MusicScanner(db)
            try:
                result = scanner._process_file(event.file_path)
                if result == "added":
                    # Find the track
                    track = (
                        db.query(Track)
                        .filter(Track.path == event.file_path)
                        .first()
                    )
                    if track:
                        event.track_id = track.id
                        event.processed = True
                        folder.file_count += 1
            except Exception:
                pass

        elif event.event_type == "modified":
            # Re-scan track
            track = db.query(Track).filter(Track.path == event.file_path).first()
            if track:
                scanner = MusicScanner(db)
                scanner._process_file(event.file_path)
                event.track_id = track.id
                event.processed = True

        elif event.event_type == "deleted":
            # Mark track as removed or delete
            track = db.query(Track).filter(Track.path == event.file_path).first()
            if track:
                event.track_id = track.id
                # Don't delete track, just mark event
                event.processed = True
                folder.file_count = max(0, folder.file_count - 1)

        folder.last_checked = datetime.utcnow()

    def get_events(
        self,
        folder_id: Optional[str] = None,
        processed: Optional[bool] = None,
        limit: int = 100,
    ) -> list[WatchEvent]:
        """Get watch events."""
        query = self.db.query(WatchEvent).order_by(WatchEvent.created_at.desc())

        if folder_id:
            query = query.filter(WatchEvent.watch_folder_id == folder_id)
        if processed is not None:
            query = query.filter(WatchEvent.processed == processed)

        return query.limit(limit).all()

    def process_pending_events(self) -> dict:
        """Process any pending (unprocessed) events."""
        events = (
            self.db.query(WatchEvent)
            .filter(WatchEvent.processed == False)
            .all()
        )

        processed = 0
        errors = []

        for event in events:
            folder = (
                self.db.query(WatchFolder)
                .filter(WatchFolder.id == event.watch_folder_id)
                .first()
            )
            if folder:
                try:
                    self._process_event(self.db, folder, event)
                    processed += 1
                except Exception as e:
                    errors.append({"event_id": event.id, "error": str(e)})

        self.db.commit()

        return {"processed": processed, "errors": errors}

    def rescan_folder(self, folder_id: str) -> dict:
        """Rescan a watch folder for changes."""
        folder = self.get_watch_folder(folder_id)
        if not folder:
            return {"error": "Folder not found"}

        folder_path = Path(folder.path)
        if not folder_path.exists():
            return {"error": "Folder path no longer exists"}

        scanner = MusicScanner(self.db)
        result = scanner.scan_directory(folder.path)

        folder.last_checked = datetime.utcnow()
        folder.file_count = result.get("total", 0)
        self.db.commit()

        return result

    def check_for_removed_tracks(self) -> dict:
        """Check for tracks whose files no longer exist."""
        tracks = self.db.query(Track).all()
        removed = []

        for track in tracks:
            if not Path(track.path).exists():
                removed.append({
                    "id": track.id,
                    "title": track.title,
                    "path": track.path,
                })

        return {
            "total_checked": len(tracks),
            "removed": removed,
            "count": len(removed),
        }

    def cleanup_missing_tracks(self, delete: bool = False) -> dict:
        """Remove or mark tracks whose files are missing."""
        result = self.check_for_removed_tracks()
        removed_tracks = result["removed"]

        if delete and removed_tracks:
            track_ids = [t["id"] for t in removed_tracks]
            self.db.query(Track).filter(Track.id.in_(track_ids)).delete(
                synchronize_session=False
            )
            self.db.commit()

        return {
            "found": len(removed_tracks),
            "deleted": len(removed_tracks) if delete else 0,
            "tracks": removed_tracks,
        }

    def get_stats(self) -> dict:
        """Get folder watching statistics."""
        from sqlalchemy import func

        total_folders = self.db.query(WatchFolder).count()
        enabled_folders = (
            self.db.query(WatchFolder)
            .filter(WatchFolder.enabled == True)
            .count()
        )
        total_events = self.db.query(WatchEvent).count()
        pending_events = (
            self.db.query(WatchEvent)
            .filter(WatchEvent.processed == False)
            .count()
        )
        total_files = (
            self.db.query(func.sum(WatchFolder.file_count))
            .scalar() or 0
        )

        return {
            "total_folders": total_folders,
            "enabled_folders": enabled_folders,
            "watching": self._running,
            "total_events": total_events,
            "pending_events": pending_events,
            "total_files": total_files,
        }


# Global watcher instance
_watcher_instance: Optional[FolderWatcherService] = None


def get_watcher(db: Session) -> FolderWatcherService:
    """Get or create the global folder watcher."""
    global _watcher_instance
    if _watcher_instance is None:
        _watcher_instance = FolderWatcherService(db)
    return _watcher_instance
