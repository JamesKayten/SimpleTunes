"""Core database models: Track, Album, Artist, Playlist, Collection."""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Table, Boolean, Text
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
