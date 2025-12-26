"""Play queue management service."""

from datetime import datetime
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models import QueueItem, QueueState, Track, Playlist, Album, playlist_tracks
from .queue_shuffle import QueueShuffleMixin


class QueueService(QueueShuffleMixin):
    """Service for managing the play queue with shuffle and repeat."""

    def __init__(self, db: Session):
        self.db = db
        self._ensure_state_exists()

    def _ensure_state_exists(self):
        """Ensure queue state row exists."""
        state = self.db.query(QueueState).filter(QueueState.id == 1).first()
        if not state:
            state = QueueState(id=1)
            self.db.add(state)
            self.db.commit()

    def _get_state(self) -> QueueState:
        """Get the queue state."""
        return self.db.query(QueueState).filter(QueueState.id == 1).first()

    def get_queue(self) -> dict:
        """Get the current queue with all tracks and state."""
        state = self._get_state()
        items = (
            self.db.query(QueueItem)
            .options(
                joinedload(QueueItem.track).joinedload(Track.artist),
                joinedload(QueueItem.track).joinedload(Track.album),
            )
            .order_by(QueueItem.position)
            .all()
        )

        # Get current track
        current_track = None
        if items and 0 <= state.current_index < len(items):
            effective_index = state.current_index
            if state.shuffle_enabled and state.shuffle_order:
                effective_index = state.shuffle_order[state.current_index]
            if 0 <= effective_index < len(items):
                current_track = items[effective_index].track

        return {
            "items": [self._item_to_dict(item) for item in items],
            "current_index": state.current_index,
            "current_track": self._track_to_dict(current_track) if current_track else None,
            "shuffle_enabled": state.shuffle_enabled,
            "repeat_mode": state.repeat_mode,
            "total_tracks": len(items),
            "total_duration": sum(item.track.duration for item in items if item.track),
        }

    def clear_queue(self) -> bool:
        """Clear all items from the queue."""
        self.db.query(QueueItem).delete()
        state = self._get_state()
        state.current_index = 0
        state.shuffle_order = None
        self.db.commit()
        return True

    def add_track(
        self,
        track_id: str,
        position: Optional[int] = None,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> QueueItem:
        """Add a single track to the queue."""
        track = self.db.query(Track).filter(Track.id == track_id).first()
        if not track:
            raise ValueError(f"Track not found: {track_id}")

        # Get max position if not specified
        if position is None:
            max_pos = self.db.query(func.max(QueueItem.position)).scalar()
            position = (max_pos or -1) + 1

        item = QueueItem(
            track_id=track_id,
            position=position,
            source_type=source_type,
            source_id=source_id,
        )
        self.db.add(item)

        # Regenerate shuffle if enabled
        state = self._get_state()
        if state.shuffle_enabled:
            self._regenerate_shuffle()

        self.db.commit()
        self.db.refresh(item)
        return item

    def add_tracks(
        self,
        track_ids: list[str],
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        clear_existing: bool = False,
    ) -> int:
        """Add multiple tracks to the queue."""
        if clear_existing:
            self.clear_queue()

        max_pos = self.db.query(func.max(QueueItem.position)).scalar()
        start_pos = (max_pos or -1) + 1

        added = 0
        for i, track_id in enumerate(track_ids):
            track = self.db.query(Track).filter(Track.id == track_id).first()
            if track:
                item = QueueItem(
                    track_id=track_id,
                    position=start_pos + i,
                    source_type=source_type,
                    source_id=source_id,
                )
                self.db.add(item)
                added += 1

        if added > 0:
            state = self._get_state()
            if state.shuffle_enabled:
                self._regenerate_shuffle()

        self.db.commit()
        return added

    def add_album(self, album_id: str, clear_existing: bool = False) -> int:
        """Add all tracks from an album to the queue."""
        tracks = (
            self.db.query(Track)
            .filter(Track.album_id == album_id)
            .order_by(Track.disc_number, Track.track_number)
            .all()
        )
        track_ids = [t.id for t in tracks]
        return self.add_tracks(track_ids, "album", album_id, clear_existing)

    def add_playlist(self, playlist_id: str, clear_existing: bool = False) -> int:
        """Add all tracks from a playlist to the queue."""
        playlist = self.db.query(Playlist).filter(Playlist.id == playlist_id).first()
        if not playlist:
            raise ValueError(f"Playlist not found: {playlist_id}")

        # Get tracks in playlist order
        track_ids = (
            self.db.query(playlist_tracks.c.track_id)
            .filter(playlist_tracks.c.playlist_id == playlist_id)
            .order_by(playlist_tracks.c.position)
            .all()
        )
        track_ids = [t[0] for t in track_ids]
        return self.add_tracks(track_ids, "playlist", playlist_id, clear_existing)

    def add_artist(self, artist_id: str, clear_existing: bool = False) -> int:
        """Add all tracks from an artist to the queue."""
        tracks = (
            self.db.query(Track)
            .filter(Track.artist_id == artist_id)
            .order_by(Track.album_id, Track.disc_number, Track.track_number)
            .all()
        )
        track_ids = [t.id for t in tracks]
        return self.add_tracks(track_ids, "artist", artist_id, clear_existing)

    def remove_track(self, queue_item_id: str) -> bool:
        """Remove a track from the queue by queue item ID."""
        item = self.db.query(QueueItem).filter(QueueItem.id == queue_item_id).first()
        if not item:
            return False

        removed_position = item.position
        self.db.delete(item)

        # Adjust positions of items after removed one
        self.db.query(QueueItem).filter(QueueItem.position > removed_position).update(
            {QueueItem.position: QueueItem.position - 1}
        )

        # Adjust current index if needed
        state = self._get_state()
        if removed_position < state.current_index:
            state.current_index -= 1
        elif removed_position == state.current_index:
            # Current track was removed, stay at same index (next track)
            total = self.db.query(QueueItem).count()
            if state.current_index >= total:
                state.current_index = max(0, total - 1)

        if state.shuffle_enabled:
            self._regenerate_shuffle()

        self.db.commit()
        return True

    def move_track(self, queue_item_id: str, new_position: int) -> bool:
        """Move a track to a new position in the queue."""
        item = self.db.query(QueueItem).filter(QueueItem.id == queue_item_id).first()
        if not item:
            return False

        old_position = item.position
        if old_position == new_position:
            return True

        # Adjust positions of affected items
        if new_position < old_position:
            # Moving up
            self.db.query(QueueItem).filter(
                QueueItem.position >= new_position,
                QueueItem.position < old_position,
            ).update({QueueItem.position: QueueItem.position + 1})
        else:
            # Moving down
            self.db.query(QueueItem).filter(
                QueueItem.position > old_position,
                QueueItem.position <= new_position,
            ).update({QueueItem.position: QueueItem.position - 1})

        item.position = new_position

        # Update current index if it was affected
        state = self._get_state()
        if old_position == state.current_index:
            state.current_index = new_position
        elif old_position < state.current_index <= new_position:
            state.current_index -= 1
        elif new_position <= state.current_index < old_position:
            state.current_index += 1

        self.db.commit()
        return True
