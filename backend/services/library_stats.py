"""Library statistics and aggregations."""

from sqlalchemy import func, desc
from sqlalchemy.orm import Session, joinedload

from models import Track, Album, Artist, TrackRating, Collection


class LibraryStatsService:
    """Service for library statistics and aggregations."""

    def __init__(self, db: Session):
        self.db = db

    def get_genres(self) -> list[dict]:
        """Get all genres with track counts."""
        results = (
            self.db.query(Track.genre, func.count(Track.id))
            .filter(Track.genre.isnot(None))
            .group_by(Track.genre)
            .order_by(desc(func.count(Track.id)))
            .all()
        )
        return [{"name": genre, "count": count} for genre, count in results]

    def get_years(self) -> list[dict]:
        """Get all years with track counts."""
        results = (
            self.db.query(Track.year, func.count(Track.id))
            .filter(Track.year.isnot(None))
            .group_by(Track.year)
            .order_by(desc(Track.year))
            .all()
        )
        return [{"year": year, "count": count} for year, count in results]

    def get_decades(self) -> list[dict]:
        """Get decades with track counts."""
        results = (
            self.db.query(Track.year, func.count(Track.id))
            .filter(Track.year.isnot(None))
            .group_by(Track.year)
            .all()
        )

        decades = {}
        for year, count in results:
            decade = (year // 10) * 10
            decade_label = f"{decade}s"
            decades[decade_label] = decades.get(decade_label, 0) + count

        return sorted(
            [{"decade": k, "count": v} for k, v in decades.items()],
            key=lambda x: x["decade"],
            reverse=True,
        )

    def get_favorites(self) -> list[Track]:
        """Get all favorited tracks."""
        return (
            self.db.query(Track)
            .join(TrackRating)
            .filter(TrackRating.favorite == True)
            .options(joinedload(Track.artist), joinedload(Track.album))
            .all()
        )

    def get_excluded(self) -> list[Track]:
        """Get all excluded tracks."""
        return (
            self.db.query(Track)
            .join(TrackRating)
            .filter(TrackRating.excluded == True)
            .options(joinedload(Track.artist), joinedload(Track.album))
            .all()
        )

    def get_top_rated(self, limit: int = 50) -> list[Track]:
        """Get highest rated tracks."""
        return (
            self.db.query(Track)
            .join(TrackRating)
            .filter(TrackRating.rating.isnot(None))
            .order_by(desc(TrackRating.rating), desc(Track.play_count))
            .limit(limit)
            .options(joinedload(Track.artist), joinedload(Track.album))
            .all()
        )

    def get_recently_played(self, limit: int = 50) -> list[Track]:
        """Get recently played tracks."""
        return (
            self.db.query(Track)
            .filter(Track.last_played.isnot(None))
            .order_by(desc(Track.last_played))
            .limit(limit)
            .options(joinedload(Track.artist), joinedload(Track.album))
            .all()
        )

    def get_recently_added(self, limit: int = 50) -> list[Track]:
        """Get recently added tracks."""
        return (
            self.db.query(Track)
            .order_by(desc(Track.date_added))
            .limit(limit)
            .options(joinedload(Track.artist), joinedload(Track.album))
            .all()
        )

    def get_most_played(self, limit: int = 50) -> list[Track]:
        """Get most played tracks."""
        return (
            self.db.query(Track)
            .filter(Track.play_count > 0)
            .order_by(desc(Track.play_count))
            .limit(limit)
            .options(joinedload(Track.artist), joinedload(Track.album))
            .all()
        )

    def get_stats(self) -> dict:
        """Get library statistics."""
        total_tracks = self.db.query(Track).count()
        total_albums = self.db.query(Album).count()
        total_artists = self.db.query(Artist).count()
        total_collections = self.db.query(Collection).count()

        # Total duration in hours
        total_duration = self.db.query(func.sum(Track.duration)).scalar() or 0
        total_hours = total_duration / 3600

        from models import Playlist

        total_playlists = self.db.query(Playlist).count()

        return {
            "total_tracks": total_tracks,
            "total_albums": total_albums,
            "total_artists": total_artists,
            "total_playlists": total_playlists,
            "total_collections": total_collections,
            "total_duration_hours": round(total_hours, 1),
            "genres": self.get_genres()[:20],
            "decades": self.get_decades(),
        }
