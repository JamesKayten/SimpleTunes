"""Music file scanner service."""

import os
from pathlib import Path
from typing import Optional
from datetime import datetime
from mutagen import File as MutagenFile
from mutagen.easyid3 import EasyID3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
from sqlalchemy.orm import Session

from models import Track, Album, Artist, Collection, collection_tracks


SUPPORTED_EXTENSIONS = {".mp3", ".m4a", ".flac", ".wav", ".aac", ".ogg", ".wma", ".aiff"}


class MusicScanner:
    """Scans directories for music files and extracts metadata."""

    def __init__(self, db: Session):
        self.db = db
        self._artist_cache: dict[str, Artist] = {}
        self._album_cache: dict[str, Album] = {}

    def scan_directory(
        self, directory: str, collection_id: Optional[str] = None
    ) -> dict:
        """
        Scan a directory for music files.

        Returns dict with keys: added, updated, total, errors
        """
        path = Path(directory).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        added = 0
        updated = 0
        errors = []

        # Clear caches for this scan
        self._artist_cache.clear()
        self._album_cache.clear()

        # Pre-populate cache with existing artists/albums
        for artist in self.db.query(Artist).all():
            self._artist_cache[artist.name.lower()] = artist
        for album in self.db.query(Album).all():
            key = f"{album.title.lower()}|{album.artist_id or ''}"
            self._album_cache[key] = album

        # Scan all files
        for filepath in path.rglob("*"):
            if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            if filepath.name.startswith("."):
                continue

            try:
                result = self._process_file(str(filepath), collection_id)
                if result == "added":
                    added += 1
                elif result == "updated":
                    updated += 1
            except Exception as e:
                errors.append(f"{filepath.name}: {str(e)}")

        self.db.commit()

        total = self.db.query(Track).count()
        return {"added": added, "updated": updated, "total": total, "errors": errors}

    def _process_file(
        self, filepath: str, collection_id: Optional[str] = None
    ) -> Optional[str]:
        """Process a single music file. Returns 'added', 'updated', or None."""
        # Check if track already exists
        existing = self.db.query(Track).filter(Track.path == filepath).first()

        metadata = self._extract_metadata(filepath)
        if not metadata:
            return None

        # Get or create artist
        artist = None
        artist_name = metadata.get("artist")
        if artist_name:
            artist = self._get_or_create_artist(artist_name)

        # Get or create album
        album = None
        album_title = metadata.get("album")
        if album_title:
            album = self._get_or_create_album(
                album_title,
                artist.id if artist else None,
                metadata.get("year"),
                metadata.get("genre"),
            )

        if existing:
            # Update existing track
            existing.title = metadata["title"]
            existing.artist_id = artist.id if artist else None
            existing.album_id = album.id if album else None
            existing.duration = metadata.get("duration", 0)
            existing.track_number = metadata.get("track_number")
            existing.disc_number = metadata.get("disc_number", 1)
            existing.genre = metadata.get("genre")
            existing.year = metadata.get("year")
            existing.bitrate = metadata.get("bitrate")
            existing.sample_rate = metadata.get("sample_rate")
            existing.channels = metadata.get("channels")
            existing.file_format = metadata.get("file_format")
            existing.file_size = metadata.get("file_size")
            return "updated"
        else:
            # Create new track
            track = Track(
                path=filepath,
                title=metadata["title"],
                artist_id=artist.id if artist else None,
                album_id=album.id if album else None,
                duration=metadata.get("duration", 0),
                track_number=metadata.get("track_number"),
                disc_number=metadata.get("disc_number", 1),
                genre=metadata.get("genre"),
                year=metadata.get("year"),
                bitrate=metadata.get("bitrate"),
                sample_rate=metadata.get("sample_rate"),
                channels=metadata.get("channels"),
                file_format=metadata.get("file_format"),
                file_size=metadata.get("file_size"),
            )
            self.db.add(track)
            self.db.flush()  # Get the track ID

            # Link to collection if provided
            if collection_id:
                self.db.execute(
                    collection_tracks.insert().values(
                        collection_id=collection_id, track_id=track.id
                    )
                )

            return "added"

    def _extract_metadata(self, filepath: str) -> Optional[dict]:
        """Extract metadata from a music file."""
        try:
            audio = MutagenFile(filepath)
            if audio is None:
                return None

            path = Path(filepath)
            metadata = {
                "title": path.stem,  # Default to filename
                "file_format": path.suffix.lower().lstrip("."),
                "file_size": path.stat().st_size,
            }

            # Get audio info
            if hasattr(audio, "info") and audio.info:
                metadata["duration"] = getattr(audio.info, "length", 0)
                metadata["bitrate"] = getattr(audio.info, "bitrate", None)
                metadata["sample_rate"] = getattr(audio.info, "sample_rate", None)
                metadata["channels"] = getattr(audio.info, "channels", None)

            # Extract tags based on file type
            if isinstance(audio, MP4):
                metadata.update(self._extract_mp4_tags(audio))
            elif isinstance(audio, FLAC):
                metadata.update(self._extract_vorbis_tags(audio))
            else:
                # Try EasyID3 for MP3 and similar
                try:
                    easy = MutagenFile(filepath, easy=True)
                    if easy:
                        metadata.update(self._extract_easy_tags(easy))
                except Exception:
                    pass

            return metadata

        except Exception:
            return None

    def _extract_easy_tags(self, audio) -> dict:
        """Extract tags from EasyID3-compatible files."""
        tags = {}
        if "title" in audio:
            tags["title"] = audio["title"][0]
        if "artist" in audio:
            tags["artist"] = audio["artist"][0]
        if "album" in audio:
            tags["album"] = audio["album"][0]
        if "genre" in audio:
            tags["genre"] = audio["genre"][0]
        if "date" in audio:
            try:
                tags["year"] = int(audio["date"][0][:4])
            except (ValueError, IndexError):
                pass
        if "tracknumber" in audio:
            try:
                tn = audio["tracknumber"][0]
                tags["track_number"] = int(tn.split("/")[0])
            except (ValueError, IndexError):
                pass
        if "discnumber" in audio:
            try:
                dn = audio["discnumber"][0]
                tags["disc_number"] = int(dn.split("/")[0])
            except (ValueError, IndexError):
                pass
        return tags

    def _extract_mp4_tags(self, audio: MP4) -> dict:
        """Extract tags from MP4/M4A files."""
        tags = {}
        tag_map = {
            "\xa9nam": "title",
            "\xa9ART": "artist",
            "\xa9alb": "album",
            "\xa9gen": "genre",
            "\xa9day": "year",
        }
        for mp4_key, our_key in tag_map.items():
            if mp4_key in audio:
                value = audio[mp4_key][0]
                if our_key == "year":
                    try:
                        tags[our_key] = int(str(value)[:4])
                    except ValueError:
                        pass
                else:
                    tags[our_key] = str(value)

        if "trkn" in audio:
            try:
                tags["track_number"] = audio["trkn"][0][0]
            except (IndexError, TypeError):
                pass

        if "disk" in audio:
            try:
                tags["disc_number"] = audio["disk"][0][0]
            except (IndexError, TypeError):
                pass

        return tags

    def _extract_vorbis_tags(self, audio: FLAC) -> dict:
        """Extract tags from FLAC/Vorbis files."""
        tags = {}
        if "title" in audio:
            tags["title"] = audio["title"][0]
        if "artist" in audio:
            tags["artist"] = audio["artist"][0]
        if "album" in audio:
            tags["album"] = audio["album"][0]
        if "genre" in audio:
            tags["genre"] = audio["genre"][0]
        if "date" in audio:
            try:
                tags["year"] = int(audio["date"][0][:4])
            except (ValueError, IndexError):
                pass
        if "tracknumber" in audio:
            try:
                tags["track_number"] = int(audio["tracknumber"][0])
            except ValueError:
                pass
        if "discnumber" in audio:
            try:
                tags["disc_number"] = int(audio["discnumber"][0])
            except ValueError:
                pass
        return tags

    def _get_or_create_artist(self, name: str) -> Artist:
        """Get existing artist or create new one."""
        key = name.lower()
        if key in self._artist_cache:
            return self._artist_cache[key]

        artist = Artist(
            name=name,
            sort_name=self._make_sort_name(name),
        )
        self.db.add(artist)
        self.db.flush()
        self._artist_cache[key] = artist
        return artist

    def _get_or_create_album(
        self,
        title: str,
        artist_id: Optional[str],
        year: Optional[int],
        genre: Optional[str],
    ) -> Album:
        """Get existing album or create new one."""
        key = f"{title.lower()}|{artist_id or ''}"
        if key in self._album_cache:
            return self._album_cache[key]

        album = Album(
            title=title,
            artist_id=artist_id,
            year=year,
            genre=genre,
        )
        self.db.add(album)
        self.db.flush()
        self._album_cache[key] = album
        return album

    def _make_sort_name(self, name: str) -> str:
        """Create a sortable name (e.g., 'The Beatles' -> 'Beatles, The')."""
        prefixes = ["The ", "A ", "An "]
        for prefix in prefixes:
            if name.startswith(prefix):
                return f"{name[len(prefix):]}, {prefix.strip()}"
        return name
