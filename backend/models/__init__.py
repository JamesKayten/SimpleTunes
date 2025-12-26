"""Database models for SimpleTunes."""

# Import Base and utilities from core
from .core import Base, generate_uuid, RepeatMode, ScrobbleStatus
from .core import playlist_tracks, collection_tracks

# Import all core models
from .core import (
    Artist,
    Album,
    Track,
    TrackRating,
    Collection,
    Playlist,
)

# Import all media models
from .media import (
    ArtworkCache,
    Lyrics,
    AudioAnalysis,
)

# Import all feature models
from .features import (
    QueueItem,
    QueueState,
    ScrobbleConfig,
    ScrobbleHistory,
    WatchFolder,
    WatchEvent,
    DuplicateGroup,
    DuplicateMember,
)

__all__ = [
    # Base and utilities
    "Base",
    "generate_uuid",
    "RepeatMode",
    "ScrobbleStatus",
    "playlist_tracks",
    "collection_tracks",
    # Core models
    "Artist",
    "Album",
    "Track",
    "TrackRating",
    "Collection",
    "Playlist",
    # Media models
    "ArtworkCache",
    "Lyrics",
    "AudioAnalysis",
    # Feature models
    "QueueItem",
    "QueueState",
    "ScrobbleConfig",
    "ScrobbleHistory",
    "WatchFolder",
    "WatchEvent",
    "DuplicateGroup",
    "DuplicateMember",
]
