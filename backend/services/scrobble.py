"""Scrobbling service for Last.fm, Libre.fm, and ListenBrainz."""

import hashlib
import time
import aiohttp
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from models import ScrobbleConfig, ScrobbleHistory, Track


class ScrobbleService:
    """Service for scrobbling tracks to various services."""

    LASTFM_API_URL = "https://ws.audioscrobbler.com/2.0/"
    LIBREFM_API_URL = "https://libre.fm/2.0/"
    LISTENBRAINZ_API_URL = "https://api.listenbrainz.org/1/submit-listens"

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # Configuration Management
    # =========================================================================

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

    # =========================================================================
    # Last.fm Authentication
    # =========================================================================

    def get_lastfm_auth_url(self, api_key: str, callback_url: Optional[str] = None) -> str:
        """Get Last.fm authentication URL for user to authorize."""
        url = f"https://www.last.fm/api/auth/?api_key={api_key}"
        if callback_url:
            url += f"&cb={callback_url}"
        return url

    async def complete_lastfm_auth(
        self, api_key: str, api_secret: str, token: str
    ) -> dict:
        """Complete Last.fm authentication and get session key."""
        params = {
            "method": "auth.getSession",
            "api_key": api_key,
            "token": token,
        }

        # Generate signature
        sig = self._generate_lastfm_signature(params, api_secret)
        params["api_sig"] = sig
        params["format"] = "json"

        async with aiohttp.ClientSession() as session:
            async with session.get(self.LASTFM_API_URL, params=params) as response:
                data = await response.json()

        if "error" in data:
            raise ValueError(data.get("message", "Authentication failed"))

        session_info = data.get("session", {})
        return {
            "username": session_info.get("name"),
            "session_key": session_info.get("key"),
        }

    def _generate_lastfm_signature(self, params: dict, secret: str) -> str:
        """Generate Last.fm API signature."""
        # Sort params and concatenate
        sorted_params = sorted(params.items())
        sig_string = "".join(f"{k}{v}" for k, v in sorted_params)
        sig_string += secret
        return hashlib.md5(sig_string.encode()).hexdigest()

    # =========================================================================
    # Scrobbling
    # =========================================================================

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
                    success = await self._scrobble_lastfm(track, config, timestamp)
                elif config.service == "librefm":
                    success = await self._scrobble_librefm(track, config, timestamp)
                elif config.service == "listenbrainz":
                    success = await self._scrobble_listenbrainz(track, config, timestamp)
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
                    success = await self._now_playing_lastfm(track, config)
                elif config.service == "librefm":
                    success = await self._now_playing_librefm(track, config)
                elif config.service == "listenbrainz":
                    success = await self._now_playing_listenbrainz(track, config)
                else:
                    continue

                results[config.service] = {"success": success}

            except Exception as e:
                results[config.service] = {"success": False, "error": str(e)}

        return results

    async def _scrobble_lastfm(
        self, track: Track, config: ScrobbleConfig, timestamp: int
    ) -> bool:
        """Scrobble to Last.fm."""
        if not config.session_key:
            raise ValueError("Last.fm not authenticated")

        params = {
            "method": "track.scrobble",
            "api_key": config.api_key,
            "sk": config.session_key,
            "artist": track.artist.name if track.artist else "Unknown",
            "track": track.title,
            "timestamp": str(timestamp),
        }

        if track.album:
            params["album"] = track.album.title

        if track.duration:
            params["duration"] = str(int(track.duration))

        sig = self._generate_lastfm_signature(params, config.api_secret)
        params["api_sig"] = sig
        params["format"] = "json"

        async with aiohttp.ClientSession() as session:
            async with session.post(self.LASTFM_API_URL, data=params) as response:
                data = await response.json()

        return "scrobbles" in data and data["scrobbles"].get("@attr", {}).get("accepted", 0) > 0

    async def _now_playing_lastfm(self, track: Track, config: ScrobbleConfig) -> bool:
        """Update now playing on Last.fm."""
        if not config.session_key:
            return False

        params = {
            "method": "track.updateNowPlaying",
            "api_key": config.api_key,
            "sk": config.session_key,
            "artist": track.artist.name if track.artist else "Unknown",
            "track": track.title,
        }

        if track.album:
            params["album"] = track.album.title

        if track.duration:
            params["duration"] = str(int(track.duration))

        sig = self._generate_lastfm_signature(params, config.api_secret)
        params["api_sig"] = sig
        params["format"] = "json"

        async with aiohttp.ClientSession() as session:
            async with session.post(self.LASTFM_API_URL, data=params) as response:
                data = await response.json()

        return "nowplaying" in data

    async def _scrobble_librefm(
        self, track: Track, config: ScrobbleConfig, timestamp: int
    ) -> bool:
        """Scrobble to Libre.fm (same API as Last.fm)."""
        if not config.session_key:
            raise ValueError("Libre.fm not authenticated")

        params = {
            "method": "track.scrobble",
            "api_key": config.api_key,
            "sk": config.session_key,
            "artist": track.artist.name if track.artist else "Unknown",
            "track": track.title,
            "timestamp": str(timestamp),
        }

        if track.album:
            params["album"] = track.album.title

        sig = self._generate_lastfm_signature(params, config.api_secret)
        params["api_sig"] = sig
        params["format"] = "json"

        async with aiohttp.ClientSession() as session:
            async with session.post(self.LIBREFM_API_URL, data=params) as response:
                data = await response.json()

        return "scrobbles" in data

    async def _now_playing_librefm(self, track: Track, config: ScrobbleConfig) -> bool:
        """Update now playing on Libre.fm."""
        return await self._now_playing_lastfm(track, config)  # Same API

    async def _scrobble_listenbrainz(
        self, track: Track, config: ScrobbleConfig, timestamp: int
    ) -> bool:
        """Scrobble to ListenBrainz."""
        if not config.session_key:  # Using session_key to store user token
            raise ValueError("ListenBrainz not authenticated")

        payload = {
            "listen_type": "single",
            "payload": [
                {
                    "listened_at": timestamp,
                    "track_metadata": {
                        "artist_name": track.artist.name if track.artist else "Unknown",
                        "track_name": track.title,
                        "release_name": track.album.title if track.album else None,
                        "additional_info": {
                            "duration_ms": int(track.duration * 1000) if track.duration else None,
                            "tracknumber": track.track_number,
                        },
                    },
                }
            ],
        }

        headers = {
            "Authorization": f"Token {config.session_key}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.LISTENBRAINZ_API_URL, json=payload, headers=headers
            ) as response:
                return response.status == 200

    async def _now_playing_listenbrainz(
        self, track: Track, config: ScrobbleConfig
    ) -> bool:
        """Update now playing on ListenBrainz."""
        if not config.session_key:
            return False

        payload = {
            "listen_type": "playing_now",
            "payload": [
                {
                    "track_metadata": {
                        "artist_name": track.artist.name if track.artist else "Unknown",
                        "track_name": track.title,
                        "release_name": track.album.title if track.album else None,
                    },
                }
            ],
        }

        headers = {
            "Authorization": f"Token {config.session_key}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.LISTENBRAINZ_API_URL, json=payload, headers=headers
            ) as response:
                return response.status == 200

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

    # =========================================================================
    # History
    # =========================================================================

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
