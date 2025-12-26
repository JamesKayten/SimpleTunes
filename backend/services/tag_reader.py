"""Tag reading service for audio file metadata."""

from pathlib import Path
from typing import Optional
from mutagen import File as MutagenFile
from sqlalchemy.orm import Session

from models import Track


class TagReaderService:
    """Service for reading audio file metadata tags."""

    def __init__(self, db: Session):
        self.db = db

    def get_tags(self, track_id: str) -> Optional[dict]:
        """
        Get all editable tags from a track's file.

        Returns comprehensive tag info including what's stored in file vs database.
        """
        track = self.db.query(Track).filter(Track.id == track_id).first()
        if not track:
            return None

        filepath = Path(track.path)
        if not filepath.exists():
            return {"error": "File not found"}

        # Get tags from file
        file_tags = self.read_file_tags(str(filepath))

        # Get database values
        db_tags = {
            "title": track.title,
            "artist": track.artist.name if track.artist else None,
            "album": track.album.title if track.album else None,
            "genre": track.genre,
            "year": track.year,
            "track_number": track.track_number,
            "disc_number": track.disc_number,
        }

        return {
            "track_id": track_id,
            "path": track.path,
            "file_format": track.file_format,
            "file_tags": file_tags,
            "database_tags": db_tags,
            "synced": file_tags == db_tags if file_tags else False,
        }

    def read_file_tags(self, filepath: str) -> Optional[dict]:
        """
        Read tags directly from audio file.

        Args:
            filepath: Path to the audio file

        Returns:
            Dictionary of tag values or error dict
        """
        try:
            audio = MutagenFile(filepath, easy=True)
            if audio is None:
                return None

            tags = {
                "title": self._get_tag_value(audio, "title"),
                "artist": self._get_tag_value(audio, "artist"),
                "album": self._get_tag_value(audio, "album"),
                "genre": self._get_tag_value(audio, "genre"),
                "year": self._parse_year(self._get_tag_value(audio, "date")),
                "track_number": self._parse_track_number(
                    self._get_tag_value(audio, "tracknumber")
                ),
                "disc_number": self._parse_track_number(
                    self._get_tag_value(audio, "discnumber")
                ),
                "album_artist": self._get_tag_value(audio, "albumartist"),
                "composer": self._get_tag_value(audio, "composer"),
                "comment": self._get_tag_value(audio, "comment"),
            }

            return tags

        except Exception as e:
            return {"error": str(e)}

    def _get_tag_value(self, audio, key: str) -> Optional[str]:
        """Safely get tag value from audio file."""
        try:
            if key in audio:
                value = audio[key]
                if isinstance(value, list) and len(value) > 0:
                    return str(value[0])
                return str(value)
        except Exception:
            pass
        return None

    def _parse_year(self, value: Optional[str]) -> Optional[int]:
        """Parse year from date string."""
        if not value:
            return None
        try:
            return int(value[:4])
        except (ValueError, TypeError):
            return None

    def _parse_track_number(self, value: Optional[str]) -> Optional[int]:
        """Parse track number from string (handles '5/12' format)."""
        if not value:
            return None
        try:
            return int(value.split("/")[0])
        except (ValueError, TypeError):
            return None
