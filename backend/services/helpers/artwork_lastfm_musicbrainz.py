"""Last.fm and MusicBrainz artwork fetching helpers."""

import aiohttp
from typing import Optional


class LastfmMusicbrainzArtworkFetcher:
    """Helper class for fetching artwork from Last.fm and MusicBrainz."""

    LASTFM_API_BASE = "https://ws.audioscrobbler.com/2.0/"
    COVER_ART_BASE = "https://coverartarchive.org"

    @staticmethod
    async def search_lastfm_artist(artist_name: str, api_key: str) -> Optional[str]:
        """Search Last.fm for artist image."""
        if not api_key:
            return None

        try:
            params = {
                "method": "artist.getinfo",
                "artist": artist_name,
                "api_key": api_key,
                "format": "json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    LastfmMusicbrainzArtworkFetcher.LASTFM_API_BASE, params=params
                ) as response:
                    if response.status != 200:
                        return None
                    data = await response.json()

            artist_info = data.get("artist", {})
            images = artist_info.get("image", [])

            # Get largest image
            for img in reversed(images):
                if img.get("#text"):
                    return img["#text"]

            return None
        except Exception:
            return None

    @staticmethod
    async def get_caa_cover(musicbrainz_id: str) -> Optional[str]:
        """Get cover from Cover Art Archive using MusicBrainz ID."""
        try:
            url = f"{LastfmMusicbrainzArtworkFetcher.COVER_ART_BASE}/release/{musicbrainz_id}/front-500"
            async with aiohttp.ClientSession() as session:
                async with session.head(url) as response:
                    if response.status == 200:
                        return url
            return None
        except Exception:
            return None
