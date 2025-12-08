"""Artwork download and management service."""

import asyncio
import hashlib
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from sqlalchemy.orm import Session
from PIL import Image
import io

from models import Album, Artist, ArtworkCache
from database import ARTWORK_DIR


class ArtworkService:
    """Service for downloading and managing album/artist artwork."""

    # MusicBrainz Cover Art Archive
    COVER_ART_BASE = "https://coverartarchive.org"
    # Last.fm API for artist images (requires API key)
    LASTFM_API_BASE = "https://ws.audioscrobbler.com/2.0/"
    # iTunes Search API (no key required)
    ITUNES_API_BASE = "https://itunes.apple.com/search"
    # Deezer API (no key required)
    DEEZER_API_BASE = "https://api.deezer.com"

    def __init__(self, db: Session, lastfm_api_key: Optional[str] = None):
        self.db = db
        self.lastfm_api_key = lastfm_api_key
        self.artwork_dir = ARTWORK_DIR
        self.artwork_dir.mkdir(parents=True, exist_ok=True)

    async def fetch_album_cover(
        self,
        album_id: str,
        artist_name: Optional[str] = None,
        album_title: Optional[str] = None,
        size: str = "large",
    ) -> Optional[str]:
        """
        Fetch album cover from various sources.

        Args:
            album_id: Database album ID
            artist_name: Artist name for search
            album_title: Album title for search
            size: 'small', 'medium', 'large'

        Returns:
            Local path to downloaded artwork or None
        """
        album = self.db.query(Album).filter(Album.id == album_id).first()
        if not album:
            return None

        # Use provided names or get from DB
        if not artist_name and album.artist:
            artist_name = album.artist.name
        if not album_title:
            album_title = album.title

        # Try multiple sources
        cover_url = None

        # 1. Try iTunes (best quality, no API key needed)
        cover_url = await self._search_itunes_cover(artist_name, album_title, size)

        # 2. Try Deezer as fallback
        if not cover_url:
            cover_url = await self._search_deezer_cover(artist_name, album_title, size)

        # 3. Try Cover Art Archive if we have MusicBrainz ID
        if not cover_url and album.musicbrainz_id:
            cover_url = await self._get_caa_cover(album.musicbrainz_id)

        if cover_url:
            local_path = await self._download_and_cache(
                cover_url, "album_cover", album_id
            )
            if local_path:
                album.cover_path = local_path
                album.cover_url = cover_url
                self.db.commit()
                return local_path

        return None

    async def fetch_artist_image(
        self, artist_id: str, artist_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Fetch artist image.

        Returns:
            Local path to downloaded artwork or None
        """
        artist = self.db.query(Artist).filter(Artist.id == artist_id).first()
        if not artist:
            return None

        if not artist_name:
            artist_name = artist.name

        image_url = None

        # 1. Try Last.fm if we have API key
        if self.lastfm_api_key:
            image_url = await self._search_lastfm_artist(artist_name)

        # 2. Try Deezer
        if not image_url:
            image_url = await self._search_deezer_artist(artist_name)

        if image_url:
            local_path = await self._download_and_cache(
                image_url, "artist_image", artist_id
            )
            if local_path:
                artist.image_path = local_path
                self.db.commit()
                return local_path

        return None

    async def _search_itunes_cover(
        self, artist: Optional[str], album: str, size: str = "large"
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
                    self.ITUNES_API_BASE, params=params
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

    async def _search_deezer_cover(
        self, artist: Optional[str], album: str, size: str = "large"
    ) -> Optional[str]:
        """Search Deezer for album artwork."""
        try:
            query = f"{artist} {album}" if artist else album

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.DEEZER_API_BASE}/search/album",
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

    async def _search_deezer_artist(self, artist_name: str) -> Optional[str]:
        """Search Deezer for artist image."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.DEEZER_API_BASE}/search/artist",
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

    async def _search_lastfm_artist(self, artist_name: str) -> Optional[str]:
        """Search Last.fm for artist image."""
        if not self.lastfm_api_key:
            return None

        try:
            params = {
                "method": "artist.getinfo",
                "artist": artist_name,
                "api_key": self.lastfm_api_key,
                "format": "json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.LASTFM_API_BASE, params=params
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

    async def _get_caa_cover(self, musicbrainz_id: str) -> Optional[str]:
        """Get cover from Cover Art Archive using MusicBrainz ID."""
        try:
            url = f"{self.COVER_ART_BASE}/release/{musicbrainz_id}/front-500"
            async with aiohttp.ClientSession() as session:
                async with session.head(url) as response:
                    if response.status == 200:
                        return url
            return None
        except Exception:
            return None

    async def _download_and_cache(
        self, url: str, artwork_type: str, entity_id: str
    ) -> Optional[str]:
        """Download artwork and save to local cache."""
        try:
            # Check if already cached
            existing = (
                self.db.query(ArtworkCache)
                .filter(ArtworkCache.source_url == url)
                .first()
            )
            if existing and Path(existing.local_path).exists():
                return existing.local_path

            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    image_data = await response.read()

            # Process and save image
            img = Image.open(io.BytesIO(image_data))
            width, height = img.size

            # Generate filename
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            filename = f"{artwork_type}_{entity_id}_{url_hash}.jpg"
            local_path = self.artwork_dir / filename

            # Convert to RGB if necessary and save as JPEG
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            async with aiofiles.open(local_path, "wb") as f:
                buffer = io.BytesIO()
                img.save(buffer, "JPEG", quality=90)
                await f.write(buffer.getvalue())

            # Cache in database
            cache_entry = ArtworkCache(
                source_url=url,
                local_path=str(local_path),
                artwork_type=artwork_type,
                width=width,
                height=height,
                file_size=len(image_data),
            )
            self.db.add(cache_entry)
            self.db.commit()

            return str(local_path)

        except Exception:
            return None

    async def fetch_all_missing_covers(
        self, limit: int = 50
    ) -> dict:
        """Fetch covers for all albums missing artwork."""
        albums = (
            self.db.query(Album)
            .filter(Album.cover_path.is_(None))
            .limit(limit)
            .all()
        )

        success = 0
        failed = 0

        for album in albums:
            artist_name = album.artist.name if album.artist else None
            result = await self.fetch_album_cover(
                album.id, artist_name, album.title
            )
            if result:
                success += 1
            else:
                failed += 1

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

        return {"success": success, "failed": failed, "total": len(albums)}

    def get_embedded_cover(self, filepath: str) -> Optional[bytes]:
        """Extract embedded cover art from music file."""
        try:
            from mutagen import File as MutagenFile
            from mutagen.mp4 import MP4
            from mutagen.id3 import ID3
            from mutagen.flac import FLAC

            audio = MutagenFile(filepath)
            if audio is None:
                return None

            # MP4/M4A
            if isinstance(audio, MP4):
                if "covr" in audio:
                    return bytes(audio["covr"][0])

            # FLAC
            if isinstance(audio, FLAC):
                if audio.pictures:
                    return audio.pictures[0].data

            # MP3 with ID3
            if hasattr(audio, "tags") and audio.tags:
                for key in audio.tags:
                    if key.startswith("APIC"):
                        return audio.tags[key].data

            return None
        except Exception:
            return None

    async def extract_and_save_embedded(
        self, track_path: str, album_id: str
    ) -> Optional[str]:
        """Extract embedded artwork and save it."""
        image_data = self.get_embedded_cover(track_path)
        if not image_data:
            return None

        try:
            img = Image.open(io.BytesIO(image_data))
            width, height = img.size

            filename = f"album_cover_{album_id}_embedded.jpg"
            local_path = self.artwork_dir / filename

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            async with aiofiles.open(local_path, "wb") as f:
                buffer = io.BytesIO()
                img.save(buffer, "JPEG", quality=90)
                await f.write(buffer.getvalue())

            # Update album
            album = self.db.query(Album).filter(Album.id == album_id).first()
            if album:
                album.cover_path = str(local_path)
                self.db.commit()

            return str(local_path)

        except Exception:
            return None
