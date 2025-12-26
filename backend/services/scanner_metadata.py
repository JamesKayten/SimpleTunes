"""Music file metadata extraction."""

from pathlib import Path
from typing import Optional
from mutagen import File as MutagenFile
from mutagen.mp4 import MP4
from mutagen.flac import FLAC


class MetadataExtractor:
    """Extracts metadata from music files."""

    @staticmethod
    def extract_metadata(filepath: str) -> Optional[dict]:
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
                metadata.update(MetadataExtractor._extract_mp4_tags(audio))
            elif isinstance(audio, FLAC):
                metadata.update(MetadataExtractor._extract_vorbis_tags(audio))
            else:
                # Try EasyID3 for MP3 and similar
                try:
                    easy = MutagenFile(filepath, easy=True)
                    if easy:
                        metadata.update(MetadataExtractor._extract_easy_tags(easy))
                except Exception:
                    pass

            return metadata

        except Exception:
            return None

    @staticmethod
    def _extract_easy_tags(audio) -> dict:
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

    @staticmethod
    def _extract_mp4_tags(audio: MP4) -> dict:
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

    @staticmethod
    def _extract_vorbis_tags(audio: FLAC) -> dict:
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
