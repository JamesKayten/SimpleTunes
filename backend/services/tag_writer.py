"""Tag writing and editing service for audio file metadata."""
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from models import Track, Album, Artist
from .tag_reader import TagReaderService
from .helpers.tag_writers_mp3_mp4 import Mp3Mp4TagWriter
from .helpers.tag_writers_flac_ogg import FlacOggTagWriter
from .helpers.tag_helpers import TagHelper

class TagWriterService:
    """Service for writing and editing audio file metadata tags."""

    def __init__(self, db: Session):
        self.db = db
        self.reader = TagReaderService(db)

    def update_tags(
        self,
        track_id: str,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        track_number: Optional[int] = None,
        disc_number: Optional[int] = None,
        album_artist: Optional[str] = None,
        composer: Optional[str] = None,
        write_to_file: bool = True,
    ) -> dict:
        """
        Update track tags in database and optionally in file.

        Args:
            track_id: Track to update
            write_to_file: If True, also write changes to the audio file

        Returns:
            Updated tag info
        """
        track = self.db.query(Track).filter(Track.id == track_id).first()
        if not track:
            return {"error": "Track not found"}

        changes = {}

        # Update database
        if title is not None:
            track.title = title
            changes["title"] = title

        if artist is not None:
            # Find or create artist
            artist_obj = TagHelper.get_or_create_artist(self.db, artist)
            track.artist_id = artist_obj.id
            changes["artist"] = artist

        if album is not None:
            # Find or create album
            album_obj = TagHelper.get_or_create_album(
                self.db, album, track.artist_id, year, genre
            )
            track.album_id = album_obj.id
            changes["album"] = album

        if genre is not None:
            track.genre = genre
            changes["genre"] = genre
            # Also update album genre if set
            if track.album:
                track.album.genre = genre

        if year is not None:
            track.year = year
            changes["year"] = year
            if track.album:
                track.album.year = year

        if track_number is not None:
            track.track_number = track_number
            changes["track_number"] = track_number

        if disc_number is not None:
            track.disc_number = disc_number
            changes["disc_number"] = disc_number

        self.db.commit()

        # Write to file if requested
        file_result = None
        if write_to_file and changes:
            file_result = self._write_tags_to_file(
                track.path,
                title=title,
                artist=artist,
                album=album,
                genre=genre,
                year=year,
                track_number=track_number,
                disc_number=disc_number,
                album_artist=album_artist,
                composer=composer,
            )

        return {
            "success": True,
            "track_id": track_id,
            "changes": changes,
            "file_updated": file_result.get("success", False) if file_result else False,
            "file_error": file_result.get("error") if file_result else None,
        }

    def _write_tags_to_file(
        self,
        filepath: str,
        **tags,
    ) -> dict:
        """Write tags to audio file."""
        try:
            path = Path(filepath)
            if not path.exists():
                return {"success": False, "error": "File not found"}

            suffix = path.suffix.lower()

            if suffix == ".mp3":
                return Mp3Mp4TagWriter.write_mp3_tags(filepath, **tags)
            elif suffix in (".m4a", ".mp4", ".aac"):
                return Mp3Mp4TagWriter.write_mp4_tags(filepath, **tags)
            elif suffix == ".flac":
                return FlacOggTagWriter.write_flac_tags(filepath, **tags)
            elif suffix == ".ogg":
                return FlacOggTagWriter.write_ogg_tags(filepath, **tags)
            else:
                # Try generic EasyID3-compatible approach
                return FlacOggTagWriter.write_easy_tags(filepath, **tags)

        except Exception as e:
            return {"success": False, "error": str(e)}

    def batch_update(
        self,
        track_ids: list[str],
        artist: Optional[str] = None,
        album: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        write_to_file: bool = True,
    ) -> dict:
        """
        Update tags for multiple tracks at once.

        Only non-None values are applied to all tracks.
        """
        results = {"success": 0, "failed": 0, "errors": []}

        for track_id in track_ids:
            try:
                result = self.update_tags(
                    track_id,
                    artist=artist,
                    album=album,
                    genre=genre,
                    year=year,
                    write_to_file=write_to_file,
                )
                if result.get("success"):
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "track_id": track_id,
                        "error": result.get("error"),
                    })
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "track_id": track_id,
                    "error": str(e),
                })

        return results

    def sync_from_file(self, track_id: str) -> dict:
        """
        Sync database tags from file tags.

        Useful when files were edited externally.
        """
        track = self.db.query(Track).filter(Track.id == track_id).first()
        if not track:
            return {"error": "Track not found"}

        file_tags = self.reader.read_file_tags(track.path)
        if not file_tags or "error" in file_tags:
            return {"error": file_tags.get("error", "Could not read tags")}

        # Update database from file
        changes = {}

        if file_tags.get("title") and file_tags["title"] != track.title:
            track.title = file_tags["title"]
            changes["title"] = file_tags["title"]

        if file_tags.get("genre") and file_tags["genre"] != track.genre:
            track.genre = file_tags["genre"]
            changes["genre"] = file_tags["genre"]

        if file_tags.get("year") and file_tags["year"] != track.year:
            track.year = file_tags["year"]
            changes["year"] = file_tags["year"]

        if file_tags.get("track_number") and file_tags["track_number"] != track.track_number:
            track.track_number = file_tags["track_number"]
            changes["track_number"] = file_tags["track_number"]

        if file_tags.get("disc_number") and file_tags["disc_number"] != track.disc_number:
            track.disc_number = file_tags["disc_number"]
            changes["disc_number"] = file_tags["disc_number"]

        if file_tags.get("artist"):
            current_artist = track.artist.name if track.artist else None
            if file_tags["artist"] != current_artist:
                artist = TagHelper.get_or_create_artist(self.db, file_tags["artist"])
                track.artist_id = artist.id
                changes["artist"] = file_tags["artist"]

        if file_tags.get("album"):
            current_album = track.album.title if track.album else None
            if file_tags["album"] != current_album:
                album = TagHelper.get_or_create_album(
                    self.db,
                    file_tags["album"],
                    track.artist_id,
                    file_tags.get("year"),
                    file_tags.get("genre"),
                )
                track.album_id = album.id
                changes["album"] = file_tags["album"]

        self.db.commit()

        return {
            "success": True,
            "track_id": track_id,
            "changes": changes,
        }
