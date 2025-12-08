"""Database models for SimpleTunes."""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Table, Boolean, Text,
    JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, declarative_base
import uuid
import enum

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class RepeatMode(enum.Enum):
    OFF = "off"
    ONE = "one"
    ALL = "all"


class ScrobbleStatus(enum.Enum):
    PENDING = "pending"
    SCROBBLED = "scrobbled"
    FAILED = "failed"


# Association tables
playlist_tracks = Table(
    "playlist_tracks",
    Base.metadata,
    Column("playlist_id", String, ForeignKey("playlists.id"), primary_key=True),
    Column("track_id", String, ForeignKey("tracks.id"), primary_key=True),
    Column("position", Integer, default=0),
    Column("added_at", DateTime, default=datetime.utcnow),
)

collection_tracks = Table(
    "collection_tracks",
    Base.metadata,
    Column("collection_id", String, ForeignKey("collections.id"), primary_key=True),
    Column("track_id", String, ForeignKey("tracks.id"), primary_key=True),
)


class Artist(Base):
    __tablename__ = "artists"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, index=True)
    sort_name = Column(String, index=True)  # "Beatles, The" for sorting
    bio = Column(Text)
    image_path = Column(String)
    musicbrainz_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    albums = relationship("Album", back_populates="artist")
    tracks = relationship("Track", back_populates="artist")


class Album(Base):
    __tablename__ = "albums"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False, index=True)
    artist_id = Column(String, ForeignKey("artists.id"))
    year = Column(Integer, index=True)
    genre = Column(String, index=True)
    cover_path = Column(String)  # Local path to album cover
    cover_url = Column(String)   # Original URL for reference
    total_tracks = Column(Integer)
    total_discs = Column(Integer, default=1)
    musicbrainz_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    artist = relationship("Artist", back_populates="albums")
    tracks = relationship("Track", back_populates="album")


class Track(Base):
    __tablename__ = "tracks"

    id = Column(String, primary_key=True, default=generate_uuid)
    path = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False, index=True)
    artist_id = Column(String, ForeignKey("artists.id"))
    album_id = Column(String, ForeignKey("albums.id"))
    duration = Column(Float, default=0)
    track_number = Column(Integer)
    disc_number = Column(Integer, default=1)
    genre = Column(String, index=True)
    year = Column(Integer, index=True)
    bitrate = Column(Integer)
    sample_rate = Column(Integer)
    channels = Column(Integer)
    file_format = Column(String)
    file_size = Column(Integer)
    play_count = Column(Integer, default=0)
    last_played = Column(DateTime)
    date_added = Column(DateTime, default=datetime.utcnow)
    musicbrainz_id = Column(String)

    artist = relationship("Artist", back_populates="tracks")
    album = relationship("Album", back_populates="tracks")
    rating = relationship("TrackRating", back_populates="track", uselist=False)
    playlists = relationship(
        "Playlist", secondary=playlist_tracks, back_populates="tracks"
    )


class TrackRating(Base):
    __tablename__ = "track_ratings"

    id = Column(String, primary_key=True, default=generate_uuid)
    track_id = Column(String, ForeignKey("tracks.id"), nullable=False, unique=True)
    rating = Column(Integer)  # 1-5 stars, None = unrated
    excluded = Column(Boolean, default=False)  # Remove from auto-playlists
    favorite = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    track = relationship("Track", back_populates="rating")


class Collection(Base):
    """A collection represents a folder of music imported by the user."""
    __tablename__ = "collections"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False, unique=True)  # Source folder path
    track_count = Column(Integer, default=0)
    total_duration = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scanned = Column(DateTime)

    tracks = relationship("Track", secondary=collection_tracks)


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text)
    is_smart = Column(Boolean, default=False)  # Smart playlist with rules
    smart_rules = Column(Text)  # JSON rules for smart playlists
    cover_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tracks = relationship(
        "Track", secondary=playlist_tracks, back_populates="playlists"
    )


class ArtworkCache(Base):
    """Cache for downloaded artwork."""
    __tablename__ = "artwork_cache"

    id = Column(String, primary_key=True, default=generate_uuid)
    source_url = Column(String, nullable=False, unique=True)
    local_path = Column(String, nullable=False)
    artwork_type = Column(String)  # album_cover, artist_image, etc.
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)
    downloaded_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# Queue System
# ============================================================================


class QueueItem(Base):
    """Individual item in the play queue."""
    __tablename__ = "queue_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    track_id = Column(String, ForeignKey("tracks.id"), nullable=False)
    position = Column(Integer, nullable=False, index=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    source_type = Column(String)  # 'playlist', 'album', 'artist', 'search', 'manual'
    source_id = Column(String)    # ID of source playlist/album/etc.

    track = relationship("Track")


class QueueState(Base):
    """Global queue state (singleton-ish, one row)."""
    __tablename__ = "queue_state"

    id = Column(Integer, primary_key=True, default=1)
    current_index = Column(Integer, default=0)
    shuffle_enabled = Column(Boolean, default=False)
    repeat_mode = Column(String, default="off")  # off, one, all
    shuffle_order = Column(JSON)  # Shuffled indices
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Scrobbling
# ============================================================================


class ScrobbleConfig(Base):
    """Scrobbling service configuration."""
    __tablename__ = "scrobble_config"

    id = Column(String, primary_key=True, default=generate_uuid)
    service = Column(String, nullable=False)  # 'lastfm', 'librefm', 'listenbrainz'
    enabled = Column(Boolean, default=True)
    username = Column(String)
    session_key = Column(String)  # Encrypted session key
    api_key = Column(String)
    api_secret = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScrobbleHistory(Base):
    """History of scrobbled tracks."""
    __tablename__ = "scrobble_history"

    id = Column(String, primary_key=True, default=generate_uuid)
    track_id = Column(String, ForeignKey("tracks.id"), nullable=False)
    service = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, scrobbled, failed
    scrobbled_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text)

    track = relationship("Track")


# ============================================================================
# Lyrics
# ============================================================================


class Lyrics(Base):
    """Cached lyrics for tracks."""
    __tablename__ = "lyrics"

    id = Column(String, primary_key=True, default=generate_uuid)
    track_id = Column(String, ForeignKey("tracks.id"), nullable=False, unique=True)
    plain_lyrics = Column(Text)  # Plain text lyrics
    synced_lyrics = Column(JSON)  # LRC format: [{time: 0.0, text: "..."}, ...]
    source = Column(String)  # Where lyrics were fetched from
    language = Column(String)
    is_instrumental = Column(Boolean, default=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    track = relationship("Track")


# ============================================================================
# Audio Analysis (ReplayGain, Gapless)
# ============================================================================


class AudioAnalysis(Base):
    """Audio analysis data for tracks (ReplayGain, gapless info)."""
    __tablename__ = "audio_analysis"

    id = Column(String, primary_key=True, default=generate_uuid)
    track_id = Column(String, ForeignKey("tracks.id"), nullable=False, unique=True)

    # ReplayGain
    track_gain = Column(Float)  # dB adjustment for track
    track_peak = Column(Float)  # Peak amplitude 0.0-1.0
    album_gain = Column(Float)  # dB adjustment for album consistency
    album_peak = Column(Float)

    # Gapless playback
    encoder_delay = Column(Integer)   # Samples to skip at start
    encoder_padding = Column(Integer)  # Samples to skip at end
    total_samples = Column(Integer)

    # BPM detection (bonus)
    bpm = Column(Float)

    analyzed_at = Column(DateTime, default=datetime.utcnow)

    track = relationship("Track")


# ============================================================================
# Watch Folders
# ============================================================================


class WatchFolder(Base):
    """Folders to watch for new music."""
    __tablename__ = "watch_folders"

    id = Column(String, primary_key=True, default=generate_uuid)
    path = Column(String, nullable=False, unique=True)
    name = Column(String)
    enabled = Column(Boolean, default=True)
    auto_import = Column(Boolean, default=True)
    create_playlist = Column(Boolean, default=False)  # Auto-create playlist for new imports
    last_checked = Column(DateTime)
    file_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class WatchEvent(Base):
    """Log of watch folder events."""
    __tablename__ = "watch_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    watch_folder_id = Column(String, ForeignKey("watch_folders.id"), nullable=False)
    event_type = Column(String)  # 'added', 'modified', 'deleted'
    file_path = Column(String)
    track_id = Column(String, ForeignKey("tracks.id"))
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    watch_folder = relationship("WatchFolder")
    track = relationship("Track")


# ============================================================================
# Duplicate Detection
# ============================================================================


class DuplicateGroup(Base):
    """Group of tracks identified as duplicates."""
    __tablename__ = "duplicate_groups"

    id = Column(String, primary_key=True, default=generate_uuid)
    fingerprint = Column(String, index=True)  # Audio fingerprint or hash
    match_type = Column(String)  # 'exact', 'audio', 'metadata'
    track_count = Column(Integer, default=0)
    reviewed = Column(Boolean, default=False)
    keep_track_id = Column(String, ForeignKey("tracks.id"))  # User's preferred version
    created_at = Column(DateTime, default=datetime.utcnow)

    keep_track = relationship("Track", foreign_keys=[keep_track_id])


class DuplicateMember(Base):
    """Track that belongs to a duplicate group."""
    __tablename__ = "duplicate_members"

    id = Column(String, primary_key=True, default=generate_uuid)
    group_id = Column(String, ForeignKey("duplicate_groups.id"), nullable=False)
    track_id = Column(String, ForeignKey("tracks.id"), nullable=False)
    similarity_score = Column(Float)  # 0.0-1.0
    is_primary = Column(Boolean, default=False)  # Best quality version

    group = relationship("DuplicateGroup")
    track = relationship("Track")
