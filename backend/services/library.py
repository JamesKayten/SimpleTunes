"""Library management service (unified interface)."""

from typing import Optional
from sqlalchemy.orm import Session

from models import Track, Album, Artist, TrackRating
from schemas import LibraryQuery
from .library_queries import LibraryQueryService
from .library_stats import LibraryStatsService


class LibraryService:
    """
    Unified library service combining queries and statistics.

    This maintains backward compatibility while delegating to specialized services.
    """

    def __init__(self, db: Session):
        self.db = db
        self._queries = LibraryQueryService(db)
        self._stats = LibraryStatsService(db)

    # Query methods (delegated to LibraryQueryService)
    def query_tracks(self, query: LibraryQuery) -> tuple[list[Track], int]:
        """Query tracks with filtering, sorting, and pagination."""
        return self._queries.query_tracks(query)

    def get_track(self, track_id: str) -> Optional[Track]:
        """Get a single track by ID."""
        return self._queries.get_track(track_id)

    def get_tracks_by_album(self, album_id: str) -> list[Track]:
        """Get all tracks for an album, sorted by disc/track number."""
        return self._queries.get_tracks_by_album(album_id)

    def get_tracks_by_artist(self, artist_id: str) -> list[Track]:
        """Get all tracks for an artist."""
        return self._queries.get_tracks_by_artist(artist_id)

    def get_albums(
        self,
        artist_id: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        sort_by: str = "title",
        sort_order: str = "asc",
    ) -> list[Album]:
        """Get albums with optional filtering."""
        return self._queries.get_albums(artist_id, genre, year, sort_by, sort_order)

    def get_artists(self, sort_by: str = "name") -> list[Artist]:
        """Get all artists."""
        return self._queries.get_artists(sort_by)

    def rate_track(
        self,
        track_id: str,
        rating: Optional[int] = None,
        excluded: Optional[bool] = None,
        favorite: Optional[bool] = None,
        notes: Optional[str] = None,
    ) -> TrackRating:
        """Update or create a track rating."""
        return self._queries.rate_track(track_id, rating, excluded, favorite, notes)

    def increment_play_count(self, track_id: str) -> Track:
        """Increment play count for a track."""
        return self._queries.increment_play_count(track_id)

    # Statistics methods (delegated to LibraryStatsService)
    def get_genres(self) -> list[dict]:
        """Get all genres with track counts."""
        return self._stats.get_genres()

    def get_years(self) -> list[dict]:
        """Get all years with track counts."""
        return self._stats.get_years()

    def get_decades(self) -> list[dict]:
        """Get decades with track counts."""
        return self._stats.get_decades()

    def get_favorites(self) -> list[Track]:
        """Get all favorited tracks."""
        return self._stats.get_favorites()

    def get_excluded(self) -> list[Track]:
        """Get all excluded tracks."""
        return self._stats.get_excluded()

    def get_top_rated(self, limit: int = 50) -> list[Track]:
        """Get highest rated tracks."""
        return self._stats.get_top_rated(limit)

    def get_recently_played(self, limit: int = 50) -> list[Track]:
        """Get recently played tracks."""
        return self._stats.get_recently_played(limit)

    def get_recently_added(self, limit: int = 50) -> list[Track]:
        """Get recently added tracks."""
        return self._stats.get_recently_added(limit)

    def get_most_played(self, limit: int = 50) -> list[Track]:
        """Get most played tracks."""
        return self._stats.get_most_played(limit)

    def get_stats(self) -> dict:
        """Get library statistics."""
        return self._stats.get_stats()
