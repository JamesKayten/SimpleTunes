"""Play queue management service."""

import random
from datetime import datetime
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models import QueueItem, QueueState, Track, Playlist, Album, playlist_tracks


class QueueService:
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

    def play_index(self, index: int) -> Optional[dict]:
        """Set the current playing index and return the track."""
        total = self.db.query(QueueItem).count()
        if index < 0 or index >= total:
            return None

        state = self._get_state()
        state.current_index = index
        self.db.commit()

        return self.get_current_track()

    def get_current_track(self) -> Optional[dict]:
        """Get the currently playing track."""
        state = self._get_state()
        items = self.db.query(QueueItem).order_by(QueueItem.position).all()

        if not items:
            return None

        effective_index = state.current_index
        if state.shuffle_enabled and state.shuffle_order:
            if 0 <= state.current_index < len(state.shuffle_order):
                effective_index = state.shuffle_order[state.current_index]

        if 0 <= effective_index < len(items):
            item = items[effective_index]
            track = (
                self.db.query(Track)
                .options(joinedload(Track.artist), joinedload(Track.album))
                .filter(Track.id == item.track_id)
                .first()
            )
            return self._track_to_dict(track) if track else None

        return None

    def next_track(self) -> Optional[dict]:
        """Move to and return the next track."""
        state = self._get_state()
        total = self.db.query(QueueItem).count()

        if total == 0:
            return None

        if state.repeat_mode == "one":
            # Stay on current track
            return self.get_current_track()

        next_index = state.current_index + 1

        if next_index >= total:
            if state.repeat_mode == "all":
                next_index = 0
            else:
                # End of queue
                return None

        state.current_index = next_index
        self.db.commit()

        return self.get_current_track()

    def previous_track(self) -> Optional[dict]:
        """Move to and return the previous track."""
        state = self._get_state()
        total = self.db.query(QueueItem).count()

        if total == 0:
            return None

        prev_index = state.current_index - 1

        if prev_index < 0:
            if state.repeat_mode == "all":
                prev_index = total - 1
            else:
                prev_index = 0

        state.current_index = prev_index
        self.db.commit()

        return self.get_current_track()

    def set_shuffle(self, enabled: bool) -> dict:
        """Enable or disable shuffle mode."""
        state = self._get_state()
        state.shuffle_enabled = enabled

        if enabled:
            self._regenerate_shuffle()
        else:
            state.shuffle_order = None

        self.db.commit()
        return {"shuffle_enabled": enabled}

    def set_repeat(self, mode: str) -> dict:
        """Set repeat mode: 'off', 'one', or 'all'."""
        if mode not in ["off", "one", "all"]:
            raise ValueError(f"Invalid repeat mode: {mode}")

        state = self._get_state()
        state.repeat_mode = mode
        self.db.commit()
        return {"repeat_mode": mode}

    def _regenerate_shuffle(self):
        """Regenerate the shuffle order."""
        total = self.db.query(QueueItem).count()
        if total == 0:
            return

        state = self._get_state()
        indices = list(range(total))

        # Keep current track at current position if playing
        current = state.current_index
        if 0 <= current < total:
            indices.remove(current)
            random.shuffle(indices)
            indices.insert(0, current)
            state.current_index = 0
        else:
            random.shuffle(indices)

        state.shuffle_order = indices

    def play_next(self, track_id: str) -> QueueItem:
        """Add a track to play next (after current track)."""
        state = self._get_state()
        next_position = state.current_index + 1

        # Shift items at and after next_position
        self.db.query(QueueItem).filter(QueueItem.position >= next_position).update(
            {QueueItem.position: QueueItem.position + 1}
        )

        return self.add_track(track_id, next_position, "manual")

    def add_to_queue(self, track_id: str) -> QueueItem:
        """Add a track to the end of the queue."""
        return self.add_track(track_id, source_type="manual")

    def get_upcoming(self, limit: int = 10) -> list[dict]:
        """Get upcoming tracks after current position."""
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

        if not items:
            return []

        upcoming = []
        for i in range(state.current_index + 1, min(state.current_index + 1 + limit, len(items))):
            effective_index = i
            if state.shuffle_enabled and state.shuffle_order:
                effective_index = state.shuffle_order[i]
            if 0 <= effective_index < len(items):
                upcoming.append(self._item_to_dict(items[effective_index]))

        return upcoming

    def get_history(self, limit: int = 10) -> list[dict]:
        """Get previously played tracks."""
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

        if not items:
            return []

        history = []
        start = max(0, state.current_index - limit)
        for i in range(start, state.current_index):
            effective_index = i
            if state.shuffle_enabled and state.shuffle_order:
                effective_index = state.shuffle_order[i]
            if 0 <= effective_index < len(items):
                history.append(self._item_to_dict(items[effective_index]))

        return history

    def _item_to_dict(self, item: QueueItem) -> dict:
        """Convert queue item to dictionary."""
        return {
            "id": item.id,
            "position": item.position,
            "source_type": item.source_type,
            "source_id": item.source_id,
            "added_at": item.added_at.isoformat() if item.added_at else None,
            "track": self._track_to_dict(item.track) if item.track else None,
        }

    def _track_to_dict(self, track: Track) -> dict:
        """Convert track to dictionary."""
        if not track:
            return None
        return {
            "id": track.id,
            "path": track.path,
            "title": track.title,
            "artist_id": track.artist_id,
            "artist_name": track.artist.name if track.artist else None,
            "album_id": track.album_id,
            "album_name": track.album.title if track.album else None,
            "cover_path": track.album.cover_path if track.album else None,
            "duration": track.duration,
            "track_number": track.track_number,
        }
