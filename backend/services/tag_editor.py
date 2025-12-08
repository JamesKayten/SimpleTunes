"""Tag editing service for modifying audio file metadata."""

from pathlib import Path
from datetime import datetime
from typing import Optional
from mutagen import File as MutagenFile
from mutagen.easyid3 import EasyID3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TRCK, TDRC, TPOS
from sqlalchemy.orm import Session

from models import Track, Album, Artist


class TagEditorService:
    """Service for editing audio file metadata tags."""

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
        file_tags = self._read_file_tags(str(filepath))

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

    def _read_file_tags(self, filepath: str) -> Optional[dict]:
        """Read tags directly from audio file."""
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
            artist_obj = self._get_or_create_artist(artist)
            track.artist_id = artist_obj.id
            changes["artist"] = artist

        if album is not None:
            # Find or create album
            album_obj = self._get_or_create_album(
                album, track.artist_id, year, genre
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
                return self._write_mp3_tags(filepath, **tags)
            elif suffix in (".m4a", ".mp4", ".aac"):
                return self._write_mp4_tags(filepath, **tags)
            elif suffix == ".flac":
                return self._write_flac_tags(filepath, **tags)
            elif suffix == ".ogg":
                return self._write_ogg_tags(filepath, **tags)
            else:
                # Try generic EasyID3-compatible approach
                return self._write_easy_tags(filepath, **tags)

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _write_mp3_tags(self, filepath: str, **tags) -> dict:
        """Write tags to MP3 file."""
        try:
            try:
                audio = ID3(filepath)
            except Exception:
                audio = ID3()
                audio.save(filepath)
                audio = ID3(filepath)

            if tags.get("title"):
                audio["TIT2"] = TIT2(encoding=3, text=tags["title"])
            if tags.get("artist"):
                audio["TPE1"] = TPE1(encoding=3, text=tags["artist"])
            if tags.get("album"):
                audio["TALB"] = TALB(encoding=3, text=tags["album"])
            if tags.get("genre"):
                audio["TCON"] = TCON(encoding=3, text=tags["genre"])
            if tags.get("year"):
                audio["TDRC"] = TDRC(encoding=3, text=str(tags["year"]))
            if tags.get("track_number"):
                audio["TRCK"] = TRCK(encoding=3, text=str(tags["track_number"]))
            if tags.get("disc_number"):
                audio["TPOS"] = TPOS(encoding=3, text=str(tags["disc_number"]))

            audio.save(filepath)
            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _write_mp4_tags(self, filepath: str, **tags) -> dict:
        """Write tags to MP4/M4A file."""
        try:
            audio = MP4(filepath)

            if tags.get("title"):
                audio["\xa9nam"] = [tags["title"]]
            if tags.get("artist"):
                audio["\xa9ART"] = [tags["artist"]]
            if tags.get("album"):
                audio["\xa9alb"] = [tags["album"]]
            if tags.get("genre"):
                audio["\xa9gen"] = [tags["genre"]]
            if tags.get("year"):
                audio["\xa9day"] = [str(tags["year"])]
            if tags.get("track_number"):
                # MP4 track number is tuple (track, total)
                current = audio.get("trkn", [(0, 0)])[0]
                audio["trkn"] = [(tags["track_number"], current[1] if len(current) > 1 else 0)]
            if tags.get("disc_number"):
                current = audio.get("disk", [(0, 0)])[0]
                audio["disk"] = [(tags["disc_number"], current[1] if len(current) > 1 else 0)]
            if tags.get("album_artist"):
                audio["aART"] = [tags["album_artist"]]

            audio.save()
            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _write_flac_tags(self, filepath: str, **tags) -> dict:
        """Write tags to FLAC file."""
        try:
            audio = FLAC(filepath)

            if tags.get("title"):
                audio["title"] = tags["title"]
            if tags.get("artist"):
                audio["artist"] = tags["artist"]
            if tags.get("album"):
                audio["album"] = tags["album"]
            if tags.get("genre"):
                audio["genre"] = tags["genre"]
            if tags.get("year"):
                audio["date"] = str(tags["year"])
            if tags.get("track_number"):
                audio["tracknumber"] = str(tags["track_number"])
            if tags.get("disc_number"):
                audio["discnumber"] = str(tags["disc_number"])
            if tags.get("album_artist"):
                audio["albumartist"] = tags["album_artist"]
            if tags.get("composer"):
                audio["composer"] = tags["composer"]

            audio.save()
            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _write_ogg_tags(self, filepath: str, **tags) -> dict:
        """Write tags to OGG file."""
        try:
            audio = OggVorbis(filepath)

            if tags.get("title"):
                audio["title"] = [tags["title"]]
            if tags.get("artist"):
                audio["artist"] = [tags["artist"]]
            if tags.get("album"):
                audio["album"] = [tags["album"]]
            if tags.get("genre"):
                audio["genre"] = [tags["genre"]]
            if tags.get("year"):
                audio["date"] = [str(tags["year"])]
            if tags.get("track_number"):
                audio["tracknumber"] = [str(tags["track_number"])]
            if tags.get("disc_number"):
                audio["discnumber"] = [str(tags["disc_number"])]

            audio.save()
            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _write_easy_tags(self, filepath: str, **tags) -> dict:
        """Write tags using EasyID3 interface (generic)."""
        try:
            audio = MutagenFile(filepath, easy=True)
            if audio is None:
                return {"success": False, "error": "Unsupported format"}

            if tags.get("title"):
                audio["title"] = tags["title"]
            if tags.get("artist"):
                audio["artist"] = tags["artist"]
            if tags.get("album"):
                audio["album"] = tags["album"]
            if tags.get("genre"):
                audio["genre"] = tags["genre"]
            if tags.get("year"):
                audio["date"] = str(tags["year"])
            if tags.get("track_number"):
                audio["tracknumber"] = str(tags["track_number"])
            if tags.get("disc_number"):
                audio["discnumber"] = str(tags["disc_number"])

            audio.save()
            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_or_create_artist(self, name: str) -> Artist:
        """Get or create artist by name."""
        artist = (
            self.db.query(Artist)
            .filter(Artist.name.ilike(name))
            .first()
        )
        if not artist:
            artist = Artist(name=name)
            self.db.add(artist)
            self.db.flush()
        return artist

    def _get_or_create_album(
        self,
        title: str,
        artist_id: Optional[str],
        year: Optional[int],
        genre: Optional[str],
    ) -> Album:
        """Get or create album by title and artist."""
        query = self.db.query(Album).filter(Album.title.ilike(title))
        if artist_id:
            query = query.filter(Album.artist_id == artist_id)
        album = query.first()

        if not album:
            album = Album(
                title=title,
                artist_id=artist_id,
                year=year,
                genre=genre,
            )
            self.db.add(album)
            self.db.flush()
        return album

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

        file_tags = self._read_file_tags(track.path)
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
                artist = self._get_or_create_artist(file_tags["artist"])
                track.artist_id = artist.id
                changes["artist"] = file_tags["artist"]

        if file_tags.get("album"):
            current_album = track.album.title if track.album else None
            if file_tags["album"] != current_album:
                album = self._get_or_create_album(
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
