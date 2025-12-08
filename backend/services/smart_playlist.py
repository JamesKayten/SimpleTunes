"""Smart playlist service with rule-based auto-updating."""

import json
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session, joinedload

from models import Playlist, Track, Artist, Album, TrackRating, playlist_tracks


class SmartPlaylistRule:
    """Represents a single rule for smart playlist matching."""

    FIELDS = {
        "title": {"type": "text", "column": Track.title},
        "artist": {"type": "text", "column": Artist.name},
        "album": {"type": "text", "column": Album.title},
        "genre": {"type": "text", "column": Track.genre},
        "year": {"type": "number", "column": Track.year},
        "rating": {"type": "number", "column": TrackRating.rating},
        "play_count": {"type": "number", "column": Track.play_count},
        "duration": {"type": "number", "column": Track.duration},
        "date_added": {"type": "date", "column": Track.date_added},
        "last_played": {"type": "date", "column": Track.last_played},
        "favorite": {"type": "boolean", "column": TrackRating.favorite},
        "excluded": {"type": "boolean", "column": TrackRating.excluded},
    }

    TEXT_OPERATORS = ["contains", "not_contains", "is", "is_not", "starts_with", "ends_with"]
    NUMBER_OPERATORS = ["equals", "not_equals", "greater_than", "less_than", "between"]
    DATE_OPERATORS = ["in_last", "not_in_last", "before", "after"]
    BOOLEAN_OPERATORS = ["is_true", "is_false"]

    def __init__(self, field: str, operator: str, value, value2=None):
        self.field = field
        self.operator = operator
        self.value = value
        self.value2 = value2  # For 'between' operator

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
            "value2": self.value2,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SmartPlaylistRule":
        return cls(
            field=data["field"],
            operator=data["operator"],
            value=data["value"],
            value2=data.get("value2"),
        )

    def apply(self, query):
        """Apply this rule to a SQLAlchemy query."""
        field_info = self.FIELDS.get(self.field)
        if not field_info:
            return query

        column = field_info["column"]
        field_type = field_info["type"]

        if field_type == "text":
            return self._apply_text_rule(query, column)
        elif field_type == "number":
            return self._apply_number_rule(query, column)
        elif field_type == "date":
            return self._apply_date_rule(query, column)
        elif field_type == "boolean":
            return self._apply_boolean_rule(query, column)

        return query

    def _apply_text_rule(self, query, column):
        if self.operator == "contains":
            return query.filter(column.ilike(f"%{self.value}%"))
        elif self.operator == "not_contains":
            return query.filter(~column.ilike(f"%{self.value}%"))
        elif self.operator == "is":
            return query.filter(column.ilike(self.value))
        elif self.operator == "is_not":
            return query.filter(~column.ilike(self.value))
        elif self.operator == "starts_with":
            return query.filter(column.ilike(f"{self.value}%"))
        elif self.operator == "ends_with":
            return query.filter(column.ilike(f"%{self.value}"))
        return query

    def _apply_number_rule(self, query, column):
        if self.operator == "equals":
            return query.filter(column == self.value)
        elif self.operator == "not_equals":
            return query.filter(column != self.value)
        elif self.operator == "greater_than":
            return query.filter(column > self.value)
        elif self.operator == "less_than":
            return query.filter(column < self.value)
        elif self.operator == "between":
            return query.filter(and_(column >= self.value, column <= self.value2))
        return query

    def _apply_date_rule(self, query, column):
        now = datetime.utcnow()
        if self.operator == "in_last":
            # value is number of days
            cutoff = now - timedelta(days=int(self.value))
            return query.filter(column >= cutoff)
        elif self.operator == "not_in_last":
            cutoff = now - timedelta(days=int(self.value))
            return query.filter(or_(column < cutoff, column.is_(None)))
        elif self.operator == "before":
            date = datetime.fromisoformat(self.value)
            return query.filter(column < date)
        elif self.operator == "after":
            date = datetime.fromisoformat(self.value)
            return query.filter(column > date)
        return query

    def _apply_boolean_rule(self, query, column):
        if self.operator == "is_true":
            return query.filter(column == True)
        elif self.operator == "is_false":
            return query.filter(or_(column == False, column.is_(None)))
        return query


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

        # Build query
        query = (
            self.db.query(Track)
            .outerjoin(Track.artist)
            .outerjoin(Track.album)
            .outerjoin(Track.rating)
        )

        # Apply rules
        if rules:
            if match_all:
                for rule in rules:
                    query = rule.apply(query)
            else:
                # OR logic - more complex
                conditions = []
                for rule in rules:
                    # Create a subquery for each rule
                    sub = (
                        self.db.query(Track.id)
                        .outerjoin(Track.artist)
                        .outerjoin(Track.album)
                        .outerjoin(Track.rating)
                    )
                    sub = rule.apply(sub)
                    conditions.append(Track.id.in_(sub))
                query = query.filter(or_(*conditions))

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
            self.db.query(Track)
            .outerjoin(Track.artist)
            .outerjoin(Track.album)
            .outerjoin(Track.rating)
            .options(joinedload(Track.artist), joinedload(Track.album))
        )

        if parsed_rules:
            if match_all:
                for rule in parsed_rules:
                    query = rule.apply(query)
            else:
                conditions = []
                for rule in parsed_rules:
                    sub = (
                        self.db.query(Track.id)
                        .outerjoin(Track.artist)
                        .outerjoin(Track.album)
                        .outerjoin(Track.rating)
                    )
                    sub = rule.apply(sub)
                    conditions.append(Track.id.in_(sub))
                query = query.filter(or_(*conditions))

        if sort_by:
            sort_column = SmartPlaylistRule.FIELDS.get(sort_by, {}).get("column", Track.title)
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))

        if limit:
            query = query.limit(limit)

        return query.all()

    @staticmethod
    def get_available_fields() -> dict:
        """Get available fields and their operators for UI."""
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
