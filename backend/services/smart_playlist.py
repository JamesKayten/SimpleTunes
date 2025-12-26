"""Smart playlist service (unified interface)."""

from typing import Optional
from sqlalchemy.orm import Session

from models import Playlist, Track
from .smart_playlist_evaluator import SmartPlaylistService as Evaluator
from .smart_playlist_builder import SmartPlaylistRule


class SmartPlaylistService:
    """
    Smart playlist service (unified interface).

    This maintains backward compatibility by delegating to the specialized evaluator.
    """

    def __init__(self, db: Session):
        self.db = db
        self._evaluator = Evaluator(db)

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
        """Create a new smart playlist."""
        return self._evaluator.create_smart_playlist(
            name, rules, match_all, limit, sort_by, sort_order, description
        )

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
        return self._evaluator.update_smart_playlist(
            playlist_id, name, rules, match_all, limit, sort_by, sort_order, description
        )

    def refresh_smart_playlist(self, playlist_id: str) -> int:
        """Refresh a smart playlist's tracks based on its rules."""
        return self._evaluator.refresh_smart_playlist(playlist_id)

    def refresh_all_smart_playlists(self) -> dict:
        """Refresh all smart playlists."""
        return self._evaluator.refresh_all_smart_playlists()

    def get_smart_playlist_rules(self, playlist_id: str) -> dict:
        """Get the rules for a smart playlist."""
        return self._evaluator.get_smart_playlist_rules(playlist_id)

    def preview_smart_playlist(
        self,
        rules: list[dict],
        match_all: bool = True,
        limit: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> list[Track]:
        """Preview what tracks would match given rules without saving."""
        return self._evaluator.preview_smart_playlist(
            rules, match_all, limit, sort_by, sort_order
        )

    @staticmethod
    def get_available_fields() -> dict:
        """Get available fields and their operators for UI."""
        return Evaluator.get_available_fields()
