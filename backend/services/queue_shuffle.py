"""Shuffle and playback navigation for play queue."""

import random
from typing import Optional
from sqlalchemy.orm import joinedload

from models import QueueItem, Track


class QueueShuffleMixin:
    """Mixin providing shuffle, repeat, and navigation functionality for queue."""

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

    def play_next(self, track_id: str):
        """Add a track to play next (after current track)."""
        state = self._get_state()
        next_position = state.current_index + 1

        # Shift items at and after next_position
        self.db.query(QueueItem).filter(QueueItem.position >= next_position).update(
            {QueueItem.position: QueueItem.position + 1}
        )

        return self.add_track(track_id, next_position, "manual")

    def add_to_queue(self, track_id: str):
        """Add a track to the end of the queue."""
        return self.add_track(track_id, source_type="manual")

    def _item_to_dict(self, item) -> dict:
        """Convert queue item to dictionary."""
        return {
            "id": item.id,
            "position": item.position,
            "source_type": item.source_type,
            "source_id": item.source_id,
            "added_at": item.added_at.isoformat() if item.added_at else None,
            "track": self._track_to_dict(item.track) if item.track else None,
        }

    def _track_to_dict(self, track) -> dict:
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
