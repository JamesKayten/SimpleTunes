"""Smart playlist rule building and query construction."""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import and_, or_

from models import Track, Artist, Album, TrackRating


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
