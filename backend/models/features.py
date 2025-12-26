"""Feature models: Queue, Scrobbling, Watch Folders, Duplicates."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from .core import Base, generate_uuid


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
