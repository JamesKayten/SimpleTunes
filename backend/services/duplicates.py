"""Duplicate track detection service."""

import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional
from collections import defaultdict
from sqlalchemy import func, and_
from sqlalchemy.orm import Session, joinedload

from models import Track, Album, Artist, DuplicateGroup, DuplicateMember


class DuplicateService:
    """Service for detecting and managing duplicate tracks."""

    def __init__(self, db: Session):
        self.db = db

    def scan_for_duplicates(
        self,
        match_type: str = "metadata",
        min_similarity: float = 0.8,
    ) -> dict:
        """
        Scan library for duplicate tracks.

        Args:
            match_type: 'exact' (file hash), 'metadata' (title/artist/duration),
                       or 'audio' (audio fingerprint - requires acoustid)
            min_similarity: Minimum similarity score (0.0-1.0) for metadata matching

        Returns:
            Summary of duplicates found
        """
        if match_type == "exact":
            return self._scan_exact_duplicates()
        elif match_type == "metadata":
            return self._scan_metadata_duplicates(min_similarity)
        elif match_type == "audio":
            return self._scan_audio_duplicates()
        else:
            raise ValueError(f"Unknown match type: {match_type}")

    def _scan_exact_duplicates(self) -> dict:
        """Find exact duplicates by file hash."""
        tracks = self.db.query(Track).all()
        hash_groups = defaultdict(list)

        for track in tracks:
            file_hash = self._get_file_hash(track.path)
            if file_hash:
                hash_groups[file_hash].append(track)

        # Create duplicate groups
        groups_created = 0
        for file_hash, tracks in hash_groups.items():
            if len(tracks) > 1:
                self._create_duplicate_group(
                    tracks, file_hash, "exact"
                )
                groups_created += 1

        return {
            "match_type": "exact",
            "groups_found": groups_created,
            "total_duplicates": sum(
                len(t) for t in hash_groups.values() if len(t) > 1
            ),
        }

    def _scan_metadata_duplicates(self, min_similarity: float) -> dict:
        """Find duplicates by metadata matching."""
        tracks = self.db.query(Track).options(
            joinedload(Track.artist),
            joinedload(Track.album),
        ).all()

        # Group by normalized title + artist
        potential_groups = defaultdict(list)
        for track in tracks:
            key = self._normalize_metadata_key(track)
            potential_groups[key].append(track)

        # Create duplicate groups with similarity scoring
        groups_created = 0
        for key, track_list in potential_groups.items():
            if len(track_list) > 1:
                # Verify similarity and create group
                if self._verify_metadata_similarity(track_list, min_similarity):
                    fingerprint = hashlib.md5(key.encode()).hexdigest()
                    self._create_duplicate_group(
                        track_list, fingerprint, "metadata"
                    )
                    groups_created += 1

        return {
            "match_type": "metadata",
            "groups_found": groups_created,
            "min_similarity": min_similarity,
        }

    def _scan_audio_duplicates(self) -> dict:
        """
        Find duplicates by audio fingerprinting.

        Note: Requires chromaprint/fpcalc to be installed.
        This is more accurate but slower.
        """
        # Audio fingerprinting requires external tools
        # For now, return a placeholder
        return {
            "match_type": "audio",
            "error": "Audio fingerprinting requires chromaprint. Install with: brew install chromaprint",
            "groups_found": 0,
        }

    def _get_file_hash(self, filepath: str, chunk_size: int = 8192) -> Optional[str]:
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

    def _normalize_metadata_key(self, track: Track) -> str:
        """Create normalized key from track metadata."""
        title = self._normalize_string(track.title)
        artist = self._normalize_string(
            track.artist.name if track.artist else ""
        )
        # Include duration bucket (within 3 seconds)
        duration_bucket = int(track.duration // 3) if track.duration else 0

        return f"{title}|{artist}|{duration_bucket}"

    def _normalize_string(self, s: str) -> str:
        """Normalize string for comparison."""
        if not s:
            return ""
        # Lowercase, remove punctuation, normalize whitespace
        import re
        s = s.lower()
        s = re.sub(r'[^\w\s]', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def _verify_metadata_similarity(
        self, tracks: list[Track], min_similarity: float
    ) -> bool:
        """Verify tracks are actually similar enough."""
        if len(tracks) < 2:
            return False

        # Compare first track to all others
        base = tracks[0]
        base_title = self._normalize_string(base.title)
        base_artist = self._normalize_string(
            base.artist.name if base.artist else ""
        )
        base_duration = base.duration or 0

        for track in tracks[1:]:
            track_title = self._normalize_string(track.title)
            track_artist = self._normalize_string(
                track.artist.name if track.artist else ""
            )
            track_duration = track.duration or 0

            # Calculate similarity
            title_sim = self._string_similarity(base_title, track_title)
            artist_sim = self._string_similarity(base_artist, track_artist)

            # Duration should be within 5 seconds
            duration_sim = 1.0 if abs(base_duration - track_duration) < 5 else 0.5

            # Weighted average
            similarity = (title_sim * 0.5) + (artist_sim * 0.3) + (duration_sim * 0.2)

            if similarity < min_similarity:
                return False

        return True

    def _string_similarity(self, s1: str, s2: str) -> float:
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

    def _create_duplicate_group(
        self,
        tracks: list[Track],
        fingerprint: str,
        match_type: str,
    ) -> DuplicateGroup:
        """Create a duplicate group for the given tracks."""
        # Check if group already exists
        existing = (
            self.db.query(DuplicateGroup)
            .filter(DuplicateGroup.fingerprint == fingerprint)
            .first()
        )

        if existing:
            # Update existing group
            group = existing
            # Remove old members
            self.db.query(DuplicateMember).filter(
                DuplicateMember.group_id == group.id
            ).delete()
        else:
            # Create new group
            group = DuplicateGroup(
                fingerprint=fingerprint,
                match_type=match_type,
                track_count=len(tracks),
            )
            self.db.add(group)
            self.db.flush()

        # Determine primary (best quality) track
        primary = self._select_primary_track(tracks)

        # Add members
        for track in tracks:
            similarity = self._calculate_track_quality(track)
            member = DuplicateMember(
                group_id=group.id,
                track_id=track.id,
                similarity_score=similarity,
                is_primary=(track.id == primary.id),
            )
            self.db.add(member)

        group.track_count = len(tracks)
        self.db.commit()
        return group

    def _select_primary_track(self, tracks: list[Track]) -> Track:
        """Select the best quality track as primary."""
        scored = []
        for track in tracks:
            score = self._calculate_track_quality(track)
            scored.append((score, track))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]

    def _calculate_track_quality(self, track: Track) -> float:
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

    def get_duplicate_groups(
        self,
        reviewed: Optional[bool] = None,
        match_type: Optional[str] = None,
    ) -> list[dict]:
        """Get all duplicate groups."""
        query = self.db.query(DuplicateGroup)

        if reviewed is not None:
            query = query.filter(DuplicateGroup.reviewed == reviewed)
        if match_type:
            query = query.filter(DuplicateGroup.match_type == match_type)

        groups = query.order_by(DuplicateGroup.created_at.desc()).all()

        return [self._group_to_dict(g) for g in groups]

    def get_duplicate_group(self, group_id: str) -> Optional[dict]:
        """Get a specific duplicate group with members."""
        group = (
            self.db.query(DuplicateGroup)
            .filter(DuplicateGroup.id == group_id)
            .first()
        )

        if not group:
            return None

        members = (
            self.db.query(DuplicateMember)
            .filter(DuplicateMember.group_id == group_id)
            .all()
        )

        result = self._group_to_dict(group)
        result["tracks"] = []

        for member in members:
            track = (
                self.db.query(Track)
                .options(joinedload(Track.artist), joinedload(Track.album))
                .filter(Track.id == member.track_id)
                .first()
            )
            if track:
                result["tracks"].append({
                    "member_id": member.id,
                    "track_id": track.id,
                    "title": track.title,
                    "artist": track.artist.name if track.artist else None,
                    "album": track.album.title if track.album else None,
                    "path": track.path,
                    "duration": track.duration,
                    "bitrate": track.bitrate,
                    "file_format": track.file_format,
                    "file_size": track.file_size,
                    "similarity_score": member.similarity_score,
                    "is_primary": member.is_primary,
                })

        return result

    def _group_to_dict(self, group: DuplicateGroup) -> dict:
        """Convert DuplicateGroup to dict."""
        return {
            "id": group.id,
            "fingerprint": group.fingerprint,
            "match_type": group.match_type,
            "track_count": group.track_count,
            "reviewed": group.reviewed,
            "keep_track_id": group.keep_track_id,
            "created_at": group.created_at.isoformat() if group.created_at else None,
        }

    def mark_reviewed(self, group_id: str, keep_track_id: str) -> bool:
        """Mark a duplicate group as reviewed and select track to keep."""
        group = (
            self.db.query(DuplicateGroup)
            .filter(DuplicateGroup.id == group_id)
            .first()
        )

        if not group:
            return False

        group.reviewed = True
        group.keep_track_id = keep_track_id
        self.db.commit()
        return True

    def delete_duplicates(
        self,
        group_id: str,
        delete_files: bool = False,
    ) -> dict:
        """
        Delete duplicate tracks, keeping the primary one.

        Args:
            group_id: Duplicate group to process
            delete_files: If True, also delete the actual files

        Returns:
            Summary of deletions
        """
        group = (
            self.db.query(DuplicateGroup)
            .filter(DuplicateGroup.id == group_id)
            .first()
        )

        if not group:
            return {"error": "Group not found"}

        # Get tracks to delete (not primary)
        members = (
            self.db.query(DuplicateMember)
            .filter(
                DuplicateMember.group_id == group_id,
                DuplicateMember.is_primary == False,
            )
            .all()
        )

        deleted = 0
        errors = []

        for member in members:
            track = self.db.query(Track).filter(Track.id == member.track_id).first()
            if track:
                if delete_files:
                    try:
                        path = Path(track.path)
                        if path.exists():
                            path.unlink()
                    except Exception as e:
                        errors.append(f"{track.path}: {str(e)}")
                        continue

                # Delete from database
                self.db.delete(track)
                deleted += 1

        # Delete the group
        self.db.query(DuplicateMember).filter(
            DuplicateMember.group_id == group_id
        ).delete()
        self.db.delete(group)
        self.db.commit()

        return {
            "deleted": deleted,
            "errors": errors,
        }

    def auto_resolve_duplicates(
        self,
        delete_files: bool = False,
        match_types: Optional[list[str]] = None,
    ) -> dict:
        """
        Automatically resolve all unreviewed duplicate groups.

        Keeps the primary (highest quality) track and deletes others.
        """
        query = self.db.query(DuplicateGroup).filter(
            DuplicateGroup.reviewed == False
        )

        if match_types:
            query = query.filter(DuplicateGroup.match_type.in_(match_types))

        groups = query.all()

        results = {"processed": 0, "deleted": 0, "errors": []}

        for group in groups:
            result = self.delete_duplicates(group.id, delete_files)
            results["processed"] += 1
            results["deleted"] += result.get("deleted", 0)
            results["errors"].extend(result.get("errors", []))

        return results

    def get_stats(self) -> dict:
        """Get duplicate detection statistics."""
        total_groups = self.db.query(DuplicateGroup).count()
        reviewed = (
            self.db.query(DuplicateGroup)
            .filter(DuplicateGroup.reviewed == True)
            .count()
        )
        pending = total_groups - reviewed

        by_type = (
            self.db.query(
                DuplicateGroup.match_type,
                func.count(DuplicateGroup.id),
            )
            .group_by(DuplicateGroup.match_type)
            .all()
        )

        total_duplicate_tracks = (
            self.db.query(func.sum(DuplicateGroup.track_count))
            .scalar() or 0
        )

        return {
            "total_groups": total_groups,
            "reviewed": reviewed,
            "pending": pending,
            "by_type": {t: c for t, c in by_type},
            "total_duplicate_tracks": total_duplicate_tracks,
        }
