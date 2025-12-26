"""Duplicate track detection and fingerprinting service."""

import hashlib
from collections import defaultdict
from sqlalchemy.orm import Session, joinedload

from models import Track, DuplicateGroup, DuplicateMember
from .helpers.duplicate_fingerprinting import DuplicateFingerprinter


class DuplicateDetector:
    """Service for detecting duplicate tracks using various methods."""

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
            file_hash = DuplicateFingerprinter.get_file_hash(track.path)
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
            key = DuplicateFingerprinter.normalize_metadata_key(track)
            potential_groups[key].append(track)

        # Create duplicate groups with similarity scoring
        groups_created = 0
        for key, track_list in potential_groups.items():
            if len(track_list) > 1:
                # Verify similarity and create group
                if DuplicateFingerprinter.verify_metadata_similarity(track_list, min_similarity):
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
            similarity = DuplicateFingerprinter.calculate_track_quality(track)
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
            score = DuplicateFingerprinter.calculate_track_quality(track)
            scored.append((score, track))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]

    def get_stats(self) -> dict:
        """Get duplicate detection statistics."""
        from sqlalchemy import func

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
