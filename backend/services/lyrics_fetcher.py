"""Lyrics fetching and management service."""

import aiohttp
from typing import Optional
from sqlalchemy.orm import Session

from models import Lyrics, Track
from .lyrics_parser import LyricsParser


class LyricsService:
    """Service for fetching and managing song lyrics."""

    # LRCLIB - Free lyrics API with synced lyrics support
    LRCLIB_API = "https://lrclib.net/api"

    def __init__(self, db: Session):
        self.db = db

    async def get_lyrics(self, track_id: str, force_refresh: bool = False) -> Optional[dict]:
        """
        Get lyrics for a track, fetching if not cached.

        Returns dict with plain_lyrics, synced_lyrics, etc.
        """
        # Check cache first
        if not force_refresh:
            cached = (
                self.db.query(Lyrics)
                .filter(Lyrics.track_id == track_id)
                .first()
            )
            if cached:
                return LyricsParser.lyrics_to_dict(cached)

        # Fetch from track info
        track = self.db.query(Track).filter(Track.id == track_id).first()
        if not track:
            return None

        artist = track.artist.name if track.artist else None
        album = track.album.title if track.album else None

        # Try to fetch lyrics
        lyrics_data = await self._fetch_lyrics(
            track.title,
            artist,
            album,
            track.duration,
        )

        if lyrics_data:
            return self._save_lyrics(track_id, lyrics_data)

        return None

    async def _fetch_lyrics(
        self,
        title: str,
        artist: Optional[str],
        album: Optional[str],
        duration: Optional[float],
    ) -> Optional[dict]:
        """Fetch lyrics from available sources."""
        # Try LRCLIB first (best for synced lyrics)
        result = await self._fetch_lrclib(title, artist, album, duration)
        if result:
            return result

        return None

    async def _fetch_lrclib(
        self,
        title: str,
        artist: Optional[str],
        album: Optional[str],
        duration: Optional[float],
    ) -> Optional[dict]:
        """Fetch lyrics from LRCLIB API."""
        try:
            # Build search URL
            params = {
                "track_name": title,
            }
            if artist:
                params["artist_name"] = artist
            if album:
                params["album_name"] = album
            if duration:
                params["duration"] = int(duration)

            async with aiohttp.ClientSession() as session:
                # Try exact match first
                async with session.get(
                    f"{self.LRCLIB_API}/get",
                    params=params,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return LyricsParser.parse_lrclib_response(data)

                # Fall back to search
                async with session.get(
                    f"{self.LRCLIB_API}/search",
                    params={"q": f"{artist} {title}" if artist else title},
                ) as response:
                    if response.status == 200:
                        results = await response.json()
                        if results and len(results) > 0:
                            # Find best match
                            best = LyricsParser.find_best_match(
                                results, title, artist, duration
                            )
                            if best:
                                return LyricsParser.parse_lrclib_response(best)

            return None

        except Exception:
            return None

    def _save_lyrics(self, track_id: str, lyrics_data: dict) -> dict:
        """Save lyrics to database."""
        # Delete existing
        self.db.query(Lyrics).filter(Lyrics.track_id == track_id).delete()

        lyrics = Lyrics(
            track_id=track_id,
            plain_lyrics=lyrics_data.get("plain_lyrics"),
            synced_lyrics=lyrics_data.get("synced_lyrics"),
            is_instrumental=lyrics_data.get("is_instrumental", False),
            source=lyrics_data.get("source"),
        )
        self.db.add(lyrics)
        self.db.commit()
        self.db.refresh(lyrics)

        return LyricsParser.lyrics_to_dict(lyrics)

    def save_custom_lyrics(
        self,
        track_id: str,
        plain_lyrics: Optional[str] = None,
        synced_lyrics: Optional[list[dict]] = None,
    ) -> dict:
        """Save user-provided custom lyrics."""
        return self._save_lyrics(
            track_id,
            {
                "plain_lyrics": plain_lyrics,
                "synced_lyrics": synced_lyrics,
                "is_instrumental": False,
                "source": "user",
            },
        )

    def delete_lyrics(self, track_id: str) -> bool:
        """Delete cached lyrics for a track."""
        result = self.db.query(Lyrics).filter(Lyrics.track_id == track_id).delete()
        self.db.commit()
        return result > 0

    def get_line_at_time(self, track_id: str, time_seconds: float) -> Optional[dict]:
        """
        Get the current lyrics line at a given playback time.

        Useful for real-time synced lyrics display.
        """
        lyrics = (
            self.db.query(Lyrics)
            .filter(Lyrics.track_id == track_id)
            .first()
        )

        if not lyrics or not lyrics.synced_lyrics:
            return None

        return LyricsParser.get_line_at_time(lyrics.synced_lyrics, time_seconds)

    async def fetch_missing_lyrics(self, limit: int = 50) -> dict:
        """Fetch lyrics for tracks that don't have them."""
        # Get tracks without lyrics
        tracks_with_lyrics = self.db.query(Lyrics.track_id).subquery()
        tracks = (
            self.db.query(Track)
            .filter(~Track.id.in_(tracks_with_lyrics))
            .limit(limit)
            .all()
        )

        results = {"fetched": 0, "failed": 0, "instrumental": 0}

        for track in tracks:
            try:
                lyrics_data = await self._fetch_lyrics(
                    track.title,
                    track.artist.name if track.artist else None,
                    track.album.title if track.album else None,
                    track.duration,
                )

                if lyrics_data:
                    self._save_lyrics(track.id, lyrics_data)
                    if lyrics_data.get("is_instrumental"):
                        results["instrumental"] += 1
                    else:
                        results["fetched"] += 1
                else:
                    results["failed"] += 1

            except Exception:
                results["failed"] += 1

        return results

    def search_lyrics(self, query: str) -> list[dict]:
        """Search for tracks by lyrics content."""
        search_term = f"%{query}%"
        lyrics = (
            self.db.query(Lyrics)
            .filter(Lyrics.plain_lyrics.ilike(search_term))
            .all()
        )

        results = []
        for lyric in lyrics:
            track = self.db.query(Track).filter(Track.id == lyric.track_id).first()
            if track:
                results.append({
                    "track_id": track.id,
                    "title": track.title,
                    "artist": track.artist.name if track.artist else None,
                    "album": track.album.title if track.album else None,
                    "matching_lines": LyricsParser.find_matching_lines(
                        lyric.plain_lyrics, query
                    ),
                })

        return results
