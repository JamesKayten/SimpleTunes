"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class SortField(str, Enum):
    TITLE = "title"
    ARTIST = "artist"
    ALBUM = "album"
    GENRE = "genre"
    YEAR = "year"
    DATE_ADDED = "date_added"
    DURATION = "duration"
    RATING = "rating"
    PLAY_COUNT = "play_count"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


# Artist schemas
class ArtistBase(BaseModel):
    name: str
    sort_name: Optional[str] = None
    bio: Optional[str] = None


class ArtistCreate(ArtistBase):
    pass


class ArtistResponse(ArtistBase):
    id: str
    image_path: Optional[str] = None
    album_count: int = 0
    track_count: int = 0

    class Config:
        from_attributes = True


# Album schemas
class AlbumBase(BaseModel):
    title: str
    year: Optional[int] = None
    genre: Optional[str] = None


class AlbumCreate(AlbumBase):
    artist_id: Optional[str] = None


class AlbumResponse(AlbumBase):
    id: str
    artist_id: Optional[str] = None
    artist_name: Optional[str] = None
    cover_path: Optional[str] = None
    total_tracks: Optional[int] = None
    track_count: int = 0

    class Config:
        from_attributes = True


# Track schemas
class TrackBase(BaseModel):
    title: str
    duration: float = 0
    track_number: Optional[int] = None
    disc_number: int = 1
    genre: Optional[str] = None
    year: Optional[int] = None


class TrackCreate(TrackBase):
    path: str
    artist_id: Optional[str] = None
    album_id: Optional[str] = None


class TrackResponse(TrackBase):
    id: str
    path: str
    artist_id: Optional[str] = None
    artist_name: Optional[str] = None
    album_id: Optional[str] = None
    album_name: Optional[str] = None
    cover_path: Optional[str] = None
    play_count: int = 0
    rating: Optional[int] = None
    excluded: bool = False
    favorite: bool = False
    date_added: datetime

    class Config:
        from_attributes = True


# Rating schemas
class RatingUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    excluded: Optional[bool] = None
    favorite: Optional[bool] = None
    notes: Optional[str] = None


class RatingResponse(BaseModel):
    track_id: str
    rating: Optional[int] = None
    excluded: bool = False
    favorite: bool = False
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# Collection schemas
class CollectionCreate(BaseModel):
    path: str
    name: Optional[str] = None


class CollectionResponse(BaseModel):
    id: str
    name: str
    path: str
    track_count: int = 0
    total_duration: float = 0
    created_at: datetime
    last_scanned: Optional[datetime] = None

    class Config:
        from_attributes = True


# Playlist schemas
class PlaylistCreate(BaseModel):
    name: str
    description: Optional[str] = None


class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PlaylistResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_smart: bool = False
    track_count: int = 0
    total_duration: float = 0
    cover_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlaylistDetailResponse(PlaylistResponse):
    tracks: list[TrackResponse] = []


class PlaylistFromFolderRequest(BaseModel):
    """Create playlist from dropped folder."""
    folder_path: str
    name: Optional[str] = None  # If None, use folder name


# Library query schemas
class LibraryQuery(BaseModel):
    """Query parameters for filtering library."""
    search: Optional[str] = None
    genre: Optional[str] = None
    artist_id: Optional[str] = None
    album_id: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    rating_min: Optional[int] = Field(None, ge=1, le=5)
    favorites_only: bool = False
    exclude_removed: bool = True
    sort_by: SortField = SortField.TITLE
    sort_order: SortOrder = SortOrder.ASC
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


# Scan/import responses
class ScanRequest(BaseModel):
    directory: str


class ScanResponse(BaseModel):
    added: int
    updated: int
    total: int
    errors: list[str] = []


class ImportFolderRequest(BaseModel):
    """Import folder and optionally create playlist."""
    folder_path: str
    create_playlist: bool = True
    playlist_name: Optional[str] = None


class ImportResponse(BaseModel):
    collection_id: str
    playlist_id: Optional[str] = None
    tracks_added: int
    total_tracks: int


# Artwork
class ArtworkSearchRequest(BaseModel):
    artist: Optional[str] = None
    album: Optional[str] = None


class ArtworkResponse(BaseModel):
    id: str
    local_path: str
    artwork_type: str
    width: Optional[int] = None
    height: Optional[int] = None


# Statistics
class LibraryStats(BaseModel):
    total_tracks: int
    total_albums: int
    total_artists: int
    total_playlists: int
    total_collections: int
    total_duration_hours: float
    genres: list[dict]  # [{name: str, count: int}]
    decades: list[dict]  # [{decade: str, count: int}]
