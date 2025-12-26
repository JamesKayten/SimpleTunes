"""Remote artwork fetching service."""

import asyncio
import hashlib
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from PIL import Image
import io

from models import Album, Artist, ArtworkCache
from database import ARTWORK_DIR
from .helpers.artwork_itunes_deezer import ItunesDeezerArtworkFetcher
from .helpers.artwork_lastfm_musicbrainz import LastfmMusicbrainzArtworkFetcher


class ArtworkFetcherService:
    """Service for fetching artwork from remote sources."""

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
        cover_url = await ItunesDeezerArtworkFetcher.search_itunes_cover(artist_name, album_title, size)

        # 2. Try Deezer as fallback
        if not cover_url:
            cover_url = await ItunesDeezerArtworkFetcher.search_deezer_cover(artist_name, album_title, size)

        # 3. Try Cover Art Archive if we have MusicBrainz ID
        if not cover_url and album.musicbrainz_id:
            cover_url = await LastfmMusicbrainzArtworkFetcher.get_caa_cover(album.musicbrainz_id)

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
            image_url = await LastfmMusicbrainzArtworkFetcher.search_lastfm_artist(artist_name, self.lastfm_api_key)

        # 2. Try Deezer
        if not image_url:
            image_url = await ItunesDeezerArtworkFetcher.search_deezer_artist(artist_name)

        if image_url:
            local_path = await self._download_and_cache(
                image_url, "artist_image", artist_id
            )
            if local_path:
                artist.image_path = local_path
                self.db.commit()
                return local_path

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
