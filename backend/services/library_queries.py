"""Library query operations and filtering."""

from typing import Optional
from sqlalchemy import desc, asc, or_
from sqlalchemy.orm import Session, joinedload

from models import Track, Album, Artist, TrackRating
from schemas import LibraryQuery, SortField, SortOrder


class LibraryQueryService:
    """Service for querying and filtering the music library."""

    def __init__(self, db: Session):
        self.db = db

    def query_tracks(self, query: LibraryQuery) -> tuple[list[Track], int]:
        """
        Query tracks with filtering, sorting, and pagination.

        Returns:
            Tuple of (tracks, total_count)
        """
        q = (
            self.db.query(Track)
            .outerjoin(Track.artist)
            .outerjoin(Track.album)
            .outerjoin(Track.rating)
        )

        # Apply filters
        if query.search:
            search_term = f"%{query.search}%"
            q = q.filter(
                or_(
                    Track.title.ilike(search_term),
                    Artist.name.ilike(search_term),
                    Album.title.ilike(search_term),
                )
            )

        if query.genre:
            q = q.filter(Track.genre.ilike(f"%{query.genre}%"))

        if query.artist_id:
            q = q.filter(Track.artist_id == query.artist_id)

        if query.album_id:
            q = q.filter(Track.album_id == query.album_id)

        if query.year_from:
            q = q.filter(Track.year >= query.year_from)

        if query.year_to:
            q = q.filter(Track.year <= query.year_to)

        if query.rating_min:
            q = q.filter(TrackRating.rating >= query.rating_min)

        if query.favorites_only:
            q = q.filter(TrackRating.favorite == True)

        if query.exclude_removed:
            q = q.filter(
                or_(
                    TrackRating.excluded == False,
                    TrackRating.excluded.is_(None),
                )
            )

        # Get total count before pagination
        total = q.count()

        # Apply sorting
        sort_column = self._get_sort_column(query.sort_by)
        if query.sort_order == SortOrder.DESC:
            q = q.order_by(desc(sort_column))
        else:
            q = q.order_by(asc(sort_column))

        # Apply pagination
        q = q.offset(query.offset).limit(query.limit)

        # Load relationships
        q = q.options(
            joinedload(Track.artist),
            joinedload(Track.album),
            joinedload(Track.rating),
        )

        return q.all(), total

    def _get_sort_column(self, sort_field: SortField):
        """Map sort field to SQLAlchemy column."""
        mapping = {
            SortField.TITLE: Track.title,
            SortField.ARTIST: Artist.name,
            SortField.ALBUM: Album.title,
            SortField.GENRE: Track.genre,
            SortField.YEAR: Track.year,
            SortField.DATE_ADDED: Track.date_added,
            SortField.DURATION: Track.duration,
            SortField.RATING: TrackRating.rating,
            SortField.PLAY_COUNT: Track.play_count,
        }
        return mapping.get(sort_field, Track.title)

    def get_track(self, track_id: str) -> Optional[Track]:
        """Get a single track by ID."""
        return (
            self.db.query(Track)
            .options(
                joinedload(Track.artist),
                joinedload(Track.album),
                joinedload(Track.rating),
            )
            .filter(Track.id == track_id)
            .first()
        )

    def get_tracks_by_album(self, album_id: str) -> list[Track]:
        """Get all tracks for an album, sorted by disc/track number."""
        return (
            self.db.query(Track)
            .filter(Track.album_id == album_id)
            .order_by(Track.disc_number, Track.track_number)
            .all()
        )

    def get_tracks_by_artist(self, artist_id: str) -> list[Track]:
        """Get all tracks for an artist."""
        return (
            self.db.query(Track)
            .filter(Track.artist_id == artist_id)
            .order_by(Track.album_id, Track.disc_number, Track.track_number)
            .all()
        )

    def get_albums(
        self,
        artist_id: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        sort_by: str = "title",
        sort_order: str = "asc",
    ) -> list[Album]:
        """Get albums with optional filtering."""
        q = self.db.query(Album).options(joinedload(Album.artist))

        if artist_id:
            q = q.filter(Album.artist_id == artist_id)
        if genre:
            q = q.filter(Album.genre.ilike(f"%{genre}%"))
        if year:
            q = q.filter(Album.year == year)

        # Sorting
        sort_map = {
            "title": Album.title,
            "artist": Artist.name,
            "year": Album.year,
        }
        sort_col = sort_map.get(sort_by, Album.title)

        if sort_order == "desc":
            q = q.order_by(desc(sort_col))
        else:
            q = q.order_by(asc(sort_col))

        return q.all()

    def get_artists(self, sort_by: str = "name") -> list[Artist]:
        """Get all artists."""
        q = self.db.query(Artist)

        if sort_by == "sort_name":
            q = q.order_by(Artist.sort_name)
        else:
            q = q.order_by(Artist.name)

        return q.all()

    def rate_track(
        self,
        track_id: str,
        rating: Optional[int] = None,
        excluded: Optional[bool] = None,
        favorite: Optional[bool] = None,
        notes: Optional[str] = None,
    ) -> TrackRating:
        """Update or create a track rating."""
        track = self.db.query(Track).filter(Track.id == track_id).first()
        if not track:
            raise ValueError(f"Track not found: {track_id}")

        track_rating = (
            self.db.query(TrackRating)
            .filter(TrackRating.track_id == track_id)
            .first()
        )

        if not track_rating:
            track_rating = TrackRating(track_id=track_id)
            self.db.add(track_rating)

        if rating is not None:
            track_rating.rating = rating
        if excluded is not None:
            track_rating.excluded = excluded
        if favorite is not None:
            track_rating.favorite = favorite
        if notes is not None:
            track_rating.notes = notes

        self.db.commit()
        self.db.refresh(track_rating)
        return track_rating

    def increment_play_count(self, track_id: str) -> Track:
        """Increment play count for a track."""
        from datetime import datetime

        track = self.db.query(Track).filter(Track.id == track_id).first()
        if not track:
            raise ValueError(f"Track not found: {track_id}")

        track.play_count += 1
        track.last_played = datetime.utcnow()
        self.db.commit()
        self.db.refresh(track)
        return track
