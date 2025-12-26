"""Media-related models: Artwork, Lyrics, Audio Analysis."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from .core import Base, generate_uuid


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
