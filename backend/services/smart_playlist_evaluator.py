"""Smart playlist evaluation and track matching service."""

import json
from datetime import datetime
from typing import Optional
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session, joinedload

from models import Playlist, Track, playlist_tracks
from .smart_playlist_builder import SmartPlaylistRule


class SmartPlaylistService:
    """Service for managing smart playlists."""

    def __init__(self, db: Session):
        self.db = db

    def create_smart_playlist(
        self,
        name: str,
        rules: list[dict],
        match_all: bool = True,
        limit: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        description: Optional[str] = None,
    ) -> Playlist:
        """
        Create a new smart playlist.

        Args:
            name: Playlist name
            rules: List of rule dictionaries
            match_all: If True, all rules must match; if False, any rule matches
            limit: Maximum number of tracks
            sort_by: Field to sort by
            sort_order: 'asc' or 'desc'
            description: Playlist description
        """
        smart_rules = {
            "rules": rules,
            "match_all": match_all,
            "limit": limit,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }

        playlist = Playlist(
            name=name,
            description=description,
            is_smart=True,
            smart_rules=json.dumps(smart_rules),
        )
        self.db.add(playlist)
        self.db.commit()
        self.db.refresh(playlist)

        # Populate initial tracks
        self.refresh_smart_playlist(playlist.id)

        return playlist

    def update_smart_playlist(
        self,
        playlist_id: str,
        name: Optional[str] = None,
        rules: Optional[list[dict]] = None,
        match_all: Optional[bool] = None,
        limit: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Playlist:
        """Update a smart playlist's rules."""
        playlist = self.db.query(Playlist).filter(Playlist.id == playlist_id).first()
        if not playlist or not playlist.is_smart:
            raise ValueError("Smart playlist not found")

        current_rules = json.loads(playlist.smart_rules) if playlist.smart_rules else {}

        if name is not None:
            playlist.name = name
        if description is not None:
            playlist.description = description
        if rules is not None:
            current_rules["rules"] = rules
        if match_all is not None:
            current_rules["match_all"] = match_all
        if limit is not None:
            current_rules["limit"] = limit
        if sort_by is not None:
            current_rules["sort_by"] = sort_by
        if sort_order is not None:
            current_rules["sort_order"] = sort_order

        playlist.smart_rules = json.dumps(current_rules)
        playlist.updated_at = datetime.utcnow()
        self.db.commit()

        # Refresh tracks
        self.refresh_smart_playlist(playlist_id)

        self.db.refresh(playlist)
        return playlist

    def refresh_smart_playlist(self, playlist_id: str) -> int:
        """
        Refresh a smart playlist's tracks based on its rules.

        Returns number of tracks in playlist.
        """
        playlist = self.db.query(Playlist).filter(Playlist.id == playlist_id).first()
        if not playlist or not playlist.is_smart:
            raise ValueError("Smart playlist not found")

        rules_data = json.loads(playlist.smart_rules) if playlist.smart_rules else {}
        rules = [SmartPlaylistRule.from_dict(r) for r in rules_data.get("rules", [])]
        match_all = rules_data.get("match_all", True)
        limit = rules_data.get("limit")
        sort_by = rules_data.get("sort_by")
        sort_order = rules_data.get("sort_order", "asc")

        query = self._build_base_query()
        query = self._apply_rules(query, rules, match_all)

        # Apply sorting
        if sort_by:
            sort_column = SmartPlaylistRule.FIELDS.get(sort_by, {}).get("column", Track.title)
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))

        # Apply limit
        if limit:
            query = query.limit(limit)

        matching_tracks = query.all()

        # Clear existing tracks
        self.db.execute(
            playlist_tracks.delete().where(playlist_tracks.c.playlist_id == playlist_id)
        )

        # Add matching tracks
        for i, track in enumerate(matching_tracks):
            self.db.execute(
                playlist_tracks.insert().values(
                    playlist_id=playlist_id,
                    track_id=track.id,
                    position=i,
                )
            )

        playlist.updated_at = datetime.utcnow()
        self.db.commit()

        return len(matching_tracks)

    def refresh_all_smart_playlists(self) -> dict:
        """Refresh all smart playlists."""
        playlists = self.db.query(Playlist).filter(Playlist.is_smart == True).all()

        results = {"refreshed": 0, "errors": []}
        for playlist in playlists:
            try:
                self.refresh_smart_playlist(playlist.id)
                results["refreshed"] += 1
            except Exception as e:
                results["errors"].append({"playlist_id": playlist.id, "error": str(e)})

        return results

    def get_smart_playlist_rules(self, playlist_id: str) -> dict:
        """Get the rules for a smart playlist."""
        playlist = self.db.query(Playlist).filter(Playlist.id == playlist_id).first()
        if not playlist or not playlist.is_smart:
            raise ValueError("Smart playlist not found")

        return json.loads(playlist.smart_rules) if playlist.smart_rules else {}

    def preview_smart_playlist(
        self,
        rules: list[dict],
        match_all: bool = True,
        limit: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> list[Track]:
        """
        Preview what tracks would match given rules without saving.

        Useful for the UI to show results before creating playlist.
        """
        parsed_rules = [SmartPlaylistRule.from_dict(r) for r in rules]
        query = (
            self._build_base_query()
            .options(joinedload(Track.artist), joinedload(Track.album))
        )
        query = self._apply_rules(query, parsed_rules, match_all)

        if sort_by:
            sort_column = SmartPlaylistRule.FIELDS.get(sort_by, {}).get("column", Track.title)
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))

        if limit:
            query = query.limit(limit)

        return query.all()
    def _build_base_query(self):
        """Build base query with necessary joins."""
        return (
            self.db.query(Track)
            .outerjoin(Track.artist)
            .outerjoin(Track.album)
            .outerjoin(Track.rating)
        )
    def _apply_rules(self, query, rules, match_all):
        """Apply smart rules to query with AND or OR logic."""
        if not rules:
            return query
        if match_all:
            for rule in rules:
                query = rule.apply(query)
        else:
            conditions = []
            for rule in rules:
                sub = self._build_base_query()
                sub = rule.apply(sub)
                conditions.append(Track.id.in_(sub))
            query = query.filter(or_(*conditions))
        return query

    @staticmethod
    def get_available_fields() -> dict:
        """Get available fields and operators for UI."""
        return {
            "text_fields": ["title", "artist", "album", "genre"],
            "number_fields": ["year", "rating", "play_count", "duration"],
            "date_fields": ["date_added", "last_played"],
            "boolean_fields": ["favorite", "excluded"],
            "text_operators": SmartPlaylistRule.TEXT_OPERATORS,
            "number_operators": SmartPlaylistRule.NUMBER_OPERATORS,
            "date_operators": SmartPlaylistRule.DATE_OPERATORS,
            "boolean_operators": SmartPlaylistRule.BOOLEAN_OPERATORS,
        }
