"""iTunes and Deezer artwork fetching helpers."""

import aiohttp
from typing import Optional


class ItunesDeezerArtworkFetcher:
    """Helper class for fetching artwork from iTunes and Deezer."""

    ITUNES_API_BASE = "https://itunes.apple.com/search"
    DEEZER_API_BASE = "https://api.deezer.com"

    @staticmethod
    async def search_itunes_cover(
        artist: Optional[str], album: str, size: str = "large"
    ) -> Optional[str]:
        """Search iTunes for album artwork."""
        try:
            query = f"{artist} {album}" if artist else album
            params = {
                "term": query,
                "media": "music",
                "entity": "album",
                "limit": 5,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    ItunesDeezerArtworkFetcher.ITUNES_API_BASE, params=params
                ) as response:
                    if response.status != 200:
                        return None
                    data = await response.json()

            results = data.get("results", [])
            if not results:
                return None

            # Find best match
            for result in results:
                result_album = result.get("collectionName", "").lower()
                result_artist = result.get("artistName", "").lower()

                if album.lower() in result_album or result_album in album.lower():
                    artwork_url = result.get("artworkUrl100", "")
                    if artwork_url:
                        # iTunes provides 100x100 by default, we can request larger
                        size_map = {
                            "small": "200x200",
                            "medium": "400x400",
                            "large": "600x600",
                        }
                        return artwork_url.replace(
                            "100x100", size_map.get(size, "600x600")
                        )

            return None
        except Exception:
            return None

    @staticmethod
    async def search_deezer_cover(
        artist: Optional[str], album: str, size: str = "large"
    ) -> Optional[str]:
        """Search Deezer for album artwork."""
        try:
            query = f"{artist} {album}" if artist else album

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{ItunesDeezerArtworkFetcher.DEEZER_API_BASE}/search/album",
                    params={"q": query, "limit": 5},
                ) as response:
                    if response.status != 200:
                        return None
                    data = await response.json()

            results = data.get("data", [])
            if not results:
                return None

            for result in results:
                result_album = result.get("title", "").lower()
                if album.lower() in result_album or result_album in album.lower():
                    size_map = {
                        "small": "cover_medium",
                        "medium": "cover_big",
                        "large": "cover_xl",
                    }
                    return result.get(size_map.get(size, "cover_xl"))

            return None
        except Exception:
            return None

    @staticmethod
    async def search_deezer_artist(artist_name: str) -> Optional[str]:
        """Search Deezer for artist image."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{ItunesDeezerArtworkFetcher.DEEZER_API_BASE}/search/artist",
                    params={"q": artist_name, "limit": 5},
                ) as response:
                    if response.status != 200:
                        return None
                    data = await response.json()

            results = data.get("data", [])
            if not results:
                return None

            for result in results:
                result_name = result.get("name", "").lower()
                if (
                    artist_name.lower() in result_name
                    or result_name in artist_name.lower()
                ):
                    return result.get("picture_xl")

            return None
        except Exception:
            return None
