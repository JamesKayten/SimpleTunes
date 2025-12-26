"""Scrobbling service for Last.fm, Libre.fm, and ListenBrainz."""

import time
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from models import ScrobbleConfig, ScrobbleHistory, Track
from .scrobble_lastfm import LastfmScrobbler
from .scrobble_listenbrainz import ListenBrainzScrobbler


class ScrobbleService:
    """Service for scrobbling tracks to various services."""

    def __init__(self, db: Session):
        self.db = db
        self.lastfm = LastfmScrobbler()
        self.listenbrainz = ListenBrainzScrobbler()

    def get_config(self, service: str) -> Optional[ScrobbleConfig]:
        """Get configuration for a scrobbling service."""
        return (
            self.db.query(ScrobbleConfig)
            .filter(ScrobbleConfig.service == service)
            .first()
        )

    def get_all_configs(self) -> list[ScrobbleConfig]:
        """Get all scrobbling configurations."""
        return self.db.query(ScrobbleConfig).all()

    def save_config(
        self,
        service: str,
        api_key: str,
        api_secret: str,
        session_key: Optional[str] = None,
        username: Optional[str] = None,
        enabled: bool = True,
    ) -> ScrobbleConfig:
        """Save or update scrobbling configuration."""
        config = self.get_config(service)
        if not config:
            config = ScrobbleConfig(service=service)
            self.db.add(config)

        config.api_key = api_key
        config.api_secret = api_secret
        config.session_key = session_key
        config.username = username
        config.enabled = enabled
        config.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(config)
        return config

    def set_enabled(self, service: str, enabled: bool) -> bool:
        """Enable or disable a scrobbling service."""
        config = self.get_config(service)
        if not config:
            return False
        config.enabled = enabled
        self.db.commit()
        return True

    def delete_config(self, service: str) -> bool:
        """Delete scrobbling configuration."""
        config = self.get_config(service)
        if not config:
            return False
        self.db.delete(config)
        self.db.commit()
        return True

    def get_lastfm_auth_url(self, api_key: str, callback_url: Optional[str] = None) -> str:
        """Get Last.fm authentication URL for user to authorize."""
        return self.lastfm.get_lastfm_auth_url(api_key, callback_url)

    async def complete_lastfm_auth(
        self, api_key: str, api_secret: str, token: str
    ) -> dict:
        """Complete Last.fm authentication and get session key."""
        return await self.lastfm.complete_lastfm_auth(api_key, api_secret, token)

    async def scrobble(
        self,
        track_id: str,
        timestamp: Optional[int] = None,
    ) -> dict:
        """Scrobble a track to all enabled services."""
        track = self.db.query(Track).filter(Track.id == track_id).first()
        if not track:
            raise ValueError(f"Track not found: {track_id}")

        if not timestamp:
            timestamp = int(time.time())

        results = {}
        configs = self.db.query(ScrobbleConfig).filter(ScrobbleConfig.enabled == True).all()

        for config in configs:
            try:
                if config.service == "lastfm":
                    success = await self.lastfm.scrobble_lastfm(track, config, timestamp)
                elif config.service == "librefm":
                    success = await self.lastfm.scrobble_librefm(track, config, timestamp)
                elif config.service == "listenbrainz":
                    success = await self.listenbrainz.scrobble_listenbrainz(track, config, timestamp)
                else:
                    continue

                # Record in history
                status = "scrobbled" if success else "failed"
                self._record_scrobble(track_id, config.service, status)
                results[config.service] = {"success": success}

            except Exception as e:
                self._record_scrobble(track_id, config.service, "failed", str(e))
                results[config.service] = {"success": False, "error": str(e)}

        return results

    async def update_now_playing(self, track_id: str) -> dict:
        """Update 'now playing' status on all enabled services."""
        track = self.db.query(Track).filter(Track.id == track_id).first()
        if not track:
            raise ValueError(f"Track not found: {track_id}")

        results = {}
        configs = self.db.query(ScrobbleConfig).filter(ScrobbleConfig.enabled == True).all()

        for config in configs:
            try:
                if config.service == "lastfm":
                    success = await self.lastfm.now_playing_lastfm(track, config)
                elif config.service == "librefm":
                    success = await self.lastfm.now_playing_librefm(track, config)
                elif config.service == "listenbrainz":
                    success = await self.listenbrainz.now_playing_listenbrainz(track, config)
                else:
                    continue

                results[config.service] = {"success": success}

            except Exception as e:
                results[config.service] = {"success": False, "error": str(e)}

        return results

    def _record_scrobble(
        self,
        track_id: str,
        service: str,
        status: str,
        error: Optional[str] = None,
    ):
        """Record a scrobble attempt in history."""
        history = ScrobbleHistory(
            track_id=track_id,
            service=service,
            status=status,
            error_message=error,
        )
        self.db.add(history)
        self.db.commit()

    def get_scrobble_history(
        self,
        service: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ScrobbleHistory]:
        """Get scrobble history."""
        query = self.db.query(ScrobbleHistory).order_by(ScrobbleHistory.scrobbled_at.desc())

        if service:
            query = query.filter(ScrobbleHistory.service == service)

        return query.offset(offset).limit(limit).all()

    def get_pending_scrobbles(self) -> list[ScrobbleHistory]:
        """Get scrobbles that failed and need retry."""
        return (
            self.db.query(ScrobbleHistory)
            .filter(ScrobbleHistory.status == "failed")
            .order_by(ScrobbleHistory.scrobbled_at)
            .all()
        )

    async def retry_failed_scrobbles(self) -> dict:
        """Retry all failed scrobbles."""
        failed = self.get_pending_scrobbles()
        results = {"retried": 0, "success": 0, "failed": 0}

        for entry in failed:
            results["retried"] += 1
            try:
                result = await self.scrobble(
                    entry.track_id,
                    int(entry.scrobbled_at.timestamp()),
                )
                if result.get(entry.service, {}).get("success"):
                    results["success"] += 1
                    # Update original entry
                    entry.status = "scrobbled"
                    entry.error_message = None
                else:
                    results["failed"] += 1
            except Exception as e:
                results["failed"] += 1
                entry.error_message = str(e)

        self.db.commit()
        return results

    def get_stats(self) -> dict:
        """Get scrobbling statistics."""
        from sqlalchemy import func

        total = self.db.query(ScrobbleHistory).count()
        by_service = (
            self.db.query(ScrobbleHistory.service, func.count(ScrobbleHistory.id))
            .group_by(ScrobbleHistory.service)
            .all()
        )
        by_status = (
            self.db.query(ScrobbleHistory.status, func.count(ScrobbleHistory.id))
            .group_by(ScrobbleHistory.status)
            .all()
        )

        return {
            "total_scrobbles": total,
            "by_service": {s: c for s, c in by_service},
            "by_status": {s: c for s, c in by_status},
        }
