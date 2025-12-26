"""Duplicate track resolution and management service."""

from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session, joinedload

from models import Track, DuplicateGroup, DuplicateMember


class DuplicateResolver:
    """Service for managing and resolving duplicate tracks."""

    def __init__(self, db: Session):
        self.db = db

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
