"""ListenBrainz scrobbling implementation."""

import aiohttp

from models import ScrobbleConfig, Track


class ListenBrainzScrobbler:
    """Handles scrobbling to ListenBrainz service."""

    LISTENBRAINZ_API_URL = "https://api.listenbrainz.org/1/submit-listens"

    def __init__(self):
        pass

    async def scrobble_listenbrainz(
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

    async def now_playing_listenbrainz(
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
