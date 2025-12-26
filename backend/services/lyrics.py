"""Lyrics fetching and management service (unified interface)."""

from typing import Optional
from sqlalchemy.orm import Session

from .lyrics_fetcher import LyricsService as LyricsFetcher


class LyricsService:
    """
    Lyrics service (unified interface).

    This maintains backward compatibility by delegating to the specialized fetcher.
    """

    def __init__(self, db: Session):
        self.db = db
        self._fetcher = LyricsFetcher(db)

    async def get_lyrics(self, track_id: str, force_refresh: bool = False) -> Optional[dict]:
        """Get lyrics for a track, fetching if not cached."""
        return await self._fetcher.get_lyrics(track_id, force_refresh)

    def save_custom_lyrics(
        self,
        track_id: str,
        plain_lyrics: Optional[str] = None,
        synced_lyrics: Optional[list[dict]] = None,
    ) -> dict:
        """Save user-provided custom lyrics."""
        return self._fetcher.save_custom_lyrics(track_id, plain_lyrics, synced_lyrics)

    def delete_lyrics(self, track_id: str) -> bool:
        """Delete cached lyrics for a track."""
        return self._fetcher.delete_lyrics(track_id)

    def get_line_at_time(self, track_id: str, time_seconds: float) -> Optional[dict]:
        """Get the current lyrics line at a given playback time."""
        return self._fetcher.get_line_at_time(track_id, time_seconds)

    async def fetch_missing_lyrics(self, limit: int = 50) -> dict:
        """Fetch lyrics for tracks that don't have them."""
        return await self._fetcher.fetch_missing_lyrics(limit)

    def search_lyrics(self, query: str) -> list[dict]:
        """Search for tracks by lyrics content."""
        return self._fetcher.search_lyrics(query)
