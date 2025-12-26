"""Duplicate detection fingerprinting and hash calculation helpers."""

import hashlib
from pathlib import Path
from typing import Optional
import re

from models import Track


class DuplicateFingerprinter:
    """Helper class for duplicate detection fingerprinting."""

    @staticmethod
    def get_file_hash(filepath: str, chunk_size: int = 8192) -> Optional[str]:
        """Calculate MD5 hash of file."""
        try:
            path = Path(filepath)
            if not path.exists():
                return None

            hasher = hashlib.md5()
            with open(path, "rb") as f:
                # For large files, hash first and last chunks + size
                # This is faster while still being accurate
                file_size = path.stat().st_size

                if file_size <= chunk_size * 2:
                    # Small file - hash entire content
                    hasher.update(f.read())
                else:
                    # Large file - hash head, tail, and size
                    hasher.update(f.read(chunk_size))
                    f.seek(-chunk_size, 2)  # Seek from end
                    hasher.update(f.read(chunk_size))
                    hasher.update(str(file_size).encode())

            return hasher.hexdigest()

        except Exception:
            return None

    @staticmethod
    def normalize_metadata_key(track: Track) -> str:
        """Create normalized key from track metadata."""
        title = DuplicateFingerprinter.normalize_string(track.title)
        artist = DuplicateFingerprinter.normalize_string(
            track.artist.name if track.artist else ""
        )
        # Include duration bucket (within 3 seconds)
        duration_bucket = int(track.duration // 3) if track.duration else 0

        return f"{title}|{artist}|{duration_bucket}"

    @staticmethod
    def normalize_string(s: str) -> str:
        """Normalize string for comparison."""
        if not s:
            return ""
        # Lowercase, remove punctuation, normalize whitespace
        s = s.lower()
        s = re.sub(r'[^\w\s]', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    @staticmethod
    def verify_metadata_similarity(
        tracks: list[Track], min_similarity: float
    ) -> bool:
        """Verify tracks are actually similar enough."""
        if len(tracks) < 2:
            return False

        # Compare first track to all others
        base = tracks[0]
        base_title = DuplicateFingerprinter.normalize_string(base.title)
        base_artist = DuplicateFingerprinter.normalize_string(
            base.artist.name if base.artist else ""
        )
        base_duration = base.duration or 0

        for track in tracks[1:]:
            track_title = DuplicateFingerprinter.normalize_string(track.title)
            track_artist = DuplicateFingerprinter.normalize_string(
                track.artist.name if track.artist else ""
            )
            track_duration = track.duration or 0

            # Calculate similarity
            title_sim = DuplicateFingerprinter.string_similarity(base_title, track_title)
            artist_sim = DuplicateFingerprinter.string_similarity(base_artist, track_artist)

            # Duration should be within 5 seconds
            duration_sim = 1.0 if abs(base_duration - track_duration) < 5 else 0.5

            # Weighted average
            similarity = (title_sim * 0.5) + (artist_sim * 0.3) + (duration_sim * 0.2)

            if similarity < min_similarity:
                return False

        return True

    @staticmethod
    def string_similarity(s1: str, s2: str) -> float:
        """Calculate similarity between two strings."""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0

        # Simple Jaccard similarity on words
        words1 = set(s1.split())
        words2 = set(s2.split())

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    @staticmethod
    def calculate_track_quality(track: Track) -> float:
        """Calculate quality score for a track (higher is better)."""
        score = 0.0

        # Prefer higher bitrate
        if track.bitrate:
            score += min(track.bitrate / 320, 1.0) * 0.3

        # Prefer lossless formats
        if track.file_format in ("flac", "wav", "aiff"):
            score += 0.3
        elif track.file_format in ("m4a", "aac"):
            score += 0.2
        elif track.file_format == "mp3":
            score += 0.1

        # Prefer larger files (usually higher quality)
        if track.file_size:
            # Normalize file size (assume 10MB is "normal")
            score += min(track.file_size / (10 * 1024 * 1024), 1.0) * 0.2

        # Prefer files with more complete metadata
        metadata_score = 0
        if track.title:
            metadata_score += 0.2
        if track.artist_id:
            metadata_score += 0.2
        if track.album_id:
            metadata_score += 0.2
        if track.track_number:
            metadata_score += 0.2
        if track.genre:
            metadata_score += 0.1
        if track.year:
            metadata_score += 0.1
        score += metadata_score * 0.2

        return score
