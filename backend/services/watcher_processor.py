"""Event processing for folder watching."""

import threading
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional
from watchdog.events import FileSystemEventHandler
from sqlalchemy.orm import Session

from models import WatchFolder, WatchEvent, Track
from services.scanner import MusicScanner, SUPPORTED_EXTENSIONS


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


class WatchEventProcessor:
    """Processes file system events for watched folders."""

    @staticmethod
    def process_event(
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

    @staticmethod
    def rescan_folder(db: Session, folder_id: str) -> dict:
        """Rescan a watch folder for changes."""
        folder = db.query(WatchFolder).filter(WatchFolder.id == folder_id).first()
        if not folder:
            return {"error": "Folder not found"}

        folder_path = Path(folder.path)
        if not folder_path.exists():
            return {"error": "Folder path no longer exists"}

        scanner = MusicScanner(db)
        result = scanner.scan_directory(folder.path)

        folder.last_checked = datetime.utcnow()
        folder.file_count = result.get("total", 0)
        db.commit()

        return result

    @staticmethod
    def check_for_removed_tracks(db: Session) -> dict:
        """Check for tracks whose files no longer exist."""
        tracks = db.query(Track).all()
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

    @staticmethod
    def cleanup_missing_tracks(db: Session, delete: bool = False) -> dict:
        """Remove or mark tracks whose files are missing."""
        result = WatchEventProcessor.check_for_removed_tracks(db)
        removed_tracks = result["removed"]

        if delete and removed_tracks:
            track_ids = [t["id"] for t in removed_tracks]
            db.query(Track).filter(Track.id.in_(track_ids)).delete(
                synchronize_session=False
            )
            db.commit()

        return {
            "found": len(removed_tracks),
            "deleted": len(removed_tracks) if delete else 0,
            "tracks": removed_tracks,
        }

    @staticmethod
    def get_events(
        db: Session,
        folder_id: Optional[str] = None,
        processed: Optional[bool] = None,
        limit: int = 100,
    ) -> list[WatchEvent]:
        """Get watch events."""
        query = db.query(WatchEvent).order_by(WatchEvent.created_at.desc())

        if folder_id:
            query = query.filter(WatchEvent.watch_folder_id == folder_id)
        if processed is not None:
            query = query.filter(WatchEvent.processed == processed)

        return query.limit(limit).all()

    @staticmethod
    def process_pending_events(db: Session) -> dict:
        """Process any pending (unprocessed) events."""
        events = (
            db.query(WatchEvent)
            .filter(WatchEvent.processed == False)
            .all()
        )

        processed = 0
        errors = []

        for event in events:
            folder = (
                db.query(WatchFolder)
                .filter(WatchFolder.id == event.watch_folder_id)
                .first()
            )
            if folder:
                try:
                    WatchEventProcessor.process_event(db, folder, event)
                    processed += 1
                except Exception as e:
                    errors.append({"event_id": event.id, "error": str(e)})

        db.commit()
        return {"processed": processed, "errors": errors}

    @staticmethod
    def get_stats(db: Session, is_running: bool) -> dict:
        """Get folder watching statistics."""
        from sqlalchemy import func
        total_folders = db.query(WatchFolder).count()
        enabled_folders = (
            db.query(WatchFolder)
            .filter(WatchFolder.enabled == True)
            .count()
        )
        total_events = db.query(WatchEvent).count()
        pending_events = (
            db.query(WatchEvent)
            .filter(WatchEvent.processed == False)
            .count()
        )
        total_files = (
            db.query(func.sum(WatchFolder.file_count))
            .scalar() or 0
        )

        return {
            "total_folders": total_folders,
            "enabled_folders": enabled_folders,
            "watching": is_running,
            "total_events": total_events,
            "pending_events": pending_events,
            "total_files": total_files,
        }
