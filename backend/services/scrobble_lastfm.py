"""Last.fm and Libre.fm scrobbling implementation."""

import hashlib
import aiohttp
from typing import Optional

from models import ScrobbleConfig, Track


class LastfmScrobbler:
    """Handles scrobbling to Last.fm and Libre.fm services."""

    LASTFM_API_URL = "https://ws.audioscrobbler.com/2.0/"
    LIBREFM_API_URL = "https://libre.fm/2.0/"

    def __init__(self):
        pass

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
    # Last.fm Scrobbling
    # =========================================================================

    async def scrobble_lastfm(
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

    async def now_playing_lastfm(self, track: Track, config: ScrobbleConfig) -> bool:
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

    # =========================================================================
    # Libre.fm Scrobbling (uses same API as Last.fm)
    # =========================================================================

    async def scrobble_librefm(
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

    async def now_playing_librefm(self, track: Track, config: ScrobbleConfig) -> bool:
        """Update now playing on Libre.fm."""
        # Libre.fm uses same API as Last.fm
        return await self.now_playing_lastfm(track, config)
