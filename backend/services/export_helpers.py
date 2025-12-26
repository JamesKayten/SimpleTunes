"""Shared utilities for playlist export services."""

import json
import csv
import io
from pathlib import Path
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session, joinedload

from models import Track, playlist_tracks
from database import APP_DATA_DIR


# Shared export directory
EXPORT_DIR = APP_DATA_DIR / "exports"


def ensure_export_dir() -> Path:
    """Ensure export directory exists and return it."""
    EXPORT_DIR.mkdir(exist_ok=True)
    return EXPORT_DIR


def get_playlist_tracks(db: Session, playlist_id: str) -> list[Track]:
    """
    Get playlist tracks in order with artist and album info loaded.

    Args:
        db: Database session
        playlist_id: ID of the playlist

    Returns:
        List of Track objects in playlist order
    """
    track_ids = (
        db.query(playlist_tracks.c.track_id)
        .filter(playlist_tracks.c.playlist_id == playlist_id)
        .order_by(playlist_tracks.c.position)
        .all()
    )
    track_ids = [t[0] for t in track_ids]

    # Maintain order
    tracks = []
    for tid in track_ids:
        track = (
            db.query(Track)
            .options(joinedload(Track.artist), joinedload(Track.album))
            .filter(Track.id == tid)
            .first()
        )
        if track:
            tracks.append(track)

    return tracks


def sanitize_filename(name: str) -> str:
    """
    Sanitize name for use as filename.

    Args:
        name: Original filename

    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove/replace invalid characters
    invalid = '<>:"/\\|?*'
    for char in invalid:
        name = name.replace(char, "_")
    return name.strip()


def get_exports(export_dir: Optional[Path] = None) -> list[dict]:
    """
    List exported files in the export directory.

    Args:
        export_dir: Directory to list (defaults to EXPORT_DIR)

    Returns:
        List of export file info dicts, sorted by creation time (newest first)
    """
    if export_dir is None:
        export_dir = EXPORT_DIR

    exports = []
    if export_dir.exists():
        for f in export_dir.iterdir():
            if f.is_file():
                exports.append({
                    "name": f.name,
                    "path": str(f),
                    "size": f.stat().st_size,
                    "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
                })
    return sorted(exports, key=lambda x: x["created"], reverse=True)


def delete_export(filename: str, export_dir: Optional[Path] = None) -> bool:
    """
    Delete an exported file.

    Args:
        filename: Name of file to delete
        export_dir: Directory containing the file (defaults to EXPORT_DIR)

    Returns:
        True if file was deleted, False otherwise
    """
    if export_dir is None:
        export_dir = EXPORT_DIR

    file_path = export_dir / filename
    if file_path.exists() and file_path.is_file():
        file_path.unlink()
        return True
    return False


def get_track_path(
    absolute_path: str,
    relative: bool,
    base_path: Optional[str],
) -> str:
    """
    Get track path, optionally converting to relative path.

    Args:
        absolute_path: Absolute path to track
        relative: Whether to return relative path
        base_path: Base path for relative calculation

    Returns:
        Track path (absolute or relative)
    """
    if not relative:
        return absolute_path

    if not base_path:
        return absolute_path

    try:
        abs_track = Path(absolute_path)
        base = Path(base_path)
        return str(abs_track.relative_to(base))
    except ValueError:
        return absolute_path


def serialize_tracks_to_json(tracks: list[Track]) -> str:
    """
    Serialize tracks to JSON format for library export.

    Args:
        tracks: List of Track objects

    Returns:
        JSON string with track metadata
    """
    data = {
        "exported_at": datetime.utcnow().isoformat(),
        "track_count": len(tracks),
        "tracks": [
            {
                "path": t.path,
                "title": t.title,
                "artist": t.artist.name if t.artist else None,
                "album": t.album.title if t.album else None,
                "genre": t.genre,
                "year": t.year,
                "duration": t.duration,
                "track_number": t.track_number,
                "disc_number": t.disc_number,
                "play_count": t.play_count,
            }
            for t in tracks
        ],
    }
    return json.dumps(data, indent=2)


def serialize_tracks_to_csv(tracks: list[Track]) -> str:
    """
    Serialize tracks to CSV format for library export.

    Args:
        tracks: List of Track objects

    Returns:
        CSV string with track metadata
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Path", "Title", "Artist", "Album", "Genre", "Year",
        "Duration", "Track", "Disc", "Play Count"
    ])
    for t in tracks:
        writer.writerow([
            t.path, t.title,
            t.artist.name if t.artist else "",
            t.album.title if t.album else "",
            t.genre or "", t.year or "",
            t.duration or 0, t.track_number or "",
            t.disc_number or "", t.play_count or 0,
        ])
    return output.getvalue()
