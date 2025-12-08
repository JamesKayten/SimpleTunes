"""Lyrics fetching and management service."""

import re
import aiohttp
from datetime import datetime
from typing import Optional
from urllib.parse import quote
from sqlalchemy.orm import Session

from models import Lyrics, Track


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
                return self._lyrics_to_dict(cached)

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
                        return self._parse_lrclib_response(data)

                # Fall back to search
                async with session.get(
                    f"{self.LRCLIB_API}/search",
                    params={"q": f"{artist} {title}" if artist else title},
                ) as response:
                    if response.status == 200:
                        results = await response.json()
                        if results and len(results) > 0:
                            # Find best match
                            best = self._find_best_match(
                                results, title, artist, duration
                            )
                            if best:
                                return self._parse_lrclib_response(best)

            return None

        except Exception:
            return None

    def _parse_lrclib_response(self, data: dict) -> Optional[dict]:
        """Parse LRCLIB API response."""
        if not data:
            return None

        synced = data.get("syncedLyrics")
        plain = data.get("plainLyrics")
        is_instrumental = data.get("instrumental", False)

        if is_instrumental:
            return {
                "plain_lyrics": None,
                "synced_lyrics": None,
                "is_instrumental": True,
                "source": "lrclib",
            }

        synced_parsed = None
        if synced:
            synced_parsed = self._parse_lrc(synced)

        return {
            "plain_lyrics": plain,
            "synced_lyrics": synced_parsed,
            "is_instrumental": False,
            "source": "lrclib",
        }

    def _parse_lrc(self, lrc_text: str) -> list[dict]:
        """
        Parse LRC format lyrics into structured format.

        Returns list of {time: float, text: str}
        """
        lines = []
        # Match [mm:ss.xx] or [mm:ss] format
        pattern = r'\[(\d{2}):(\d{2})(?:\.(\d{2,3}))?\](.*)$'

        for line in lrc_text.split('\n'):
            match = re.match(pattern, line.strip())
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                centiseconds = int(match.group(3) or 0)

                # Normalize centiseconds (could be 2 or 3 digits)
                if match.group(3) and len(match.group(3)) == 3:
                    centiseconds = centiseconds // 10

                time_seconds = minutes * 60 + seconds + centiseconds / 100
                text = match.group(4).strip()

                lines.append({
                    "time": time_seconds,
                    "text": text,
                })

        return sorted(lines, key=lambda x: x["time"])

    def _find_best_match(
        self,
        results: list[dict],
        title: str,
        artist: Optional[str],
        duration: Optional[float],
    ) -> Optional[dict]:
        """Find the best matching result from search."""
        title_lower = title.lower()
        artist_lower = artist.lower() if artist else ""

        scored = []
        for result in results:
            score = 0
            result_title = result.get("trackName", "").lower()
            result_artist = result.get("artistName", "").lower()
            result_duration = result.get("duration", 0)

            # Title match
            if result_title == title_lower:
                score += 10
            elif title_lower in result_title or result_title in title_lower:
                score += 5

            # Artist match
            if artist_lower:
                if result_artist == artist_lower:
                    score += 10
                elif artist_lower in result_artist or result_artist in artist_lower:
                    score += 5

            # Duration match (within 5 seconds)
            if duration and result_duration:
                if abs(duration - result_duration) < 5:
                    score += 5

            # Prefer synced lyrics
            if result.get("syncedLyrics"):
                score += 3

            if score > 0:
                scored.append((score, result))

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[0][1]

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

        return self._lyrics_to_dict(lyrics)

    def _lyrics_to_dict(self, lyrics: Lyrics) -> dict:
        """Convert Lyrics model to dict."""
        return {
            "track_id": lyrics.track_id,
            "plain_lyrics": lyrics.plain_lyrics,
            "synced_lyrics": lyrics.synced_lyrics,
            "is_instrumental": lyrics.is_instrumental,
            "source": lyrics.source,
            "language": lyrics.language,
            "has_synced": lyrics.synced_lyrics is not None and len(lyrics.synced_lyrics) > 0,
            "fetched_at": lyrics.fetched_at.isoformat() if lyrics.fetched_at else None,
        }

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

        current_line = None
        next_line = None

        for i, line in enumerate(lyrics.synced_lyrics):
            if line["time"] <= time_seconds:
                current_line = line
                if i + 1 < len(lyrics.synced_lyrics):
                    next_line = lyrics.synced_lyrics[i + 1]
            else:
                break

        return {
            "current": current_line,
            "next": next_line,
            "progress": self._calculate_line_progress(
                current_line, next_line, time_seconds
            ) if current_line else 0,
        }

    def _calculate_line_progress(
        self,
        current: dict,
        next_line: Optional[dict],
        time_seconds: float,
    ) -> float:
        """Calculate progress through current line (0.0 to 1.0)."""
        if not next_line:
            return 1.0

        line_duration = next_line["time"] - current["time"]
        if line_duration <= 0:
            return 1.0

        elapsed = time_seconds - current["time"]
        return min(1.0, max(0.0, elapsed / line_duration))

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
                    "matching_lines": self._find_matching_lines(
                        lyric.plain_lyrics, query
                    ),
                })

        return results

    def _find_matching_lines(self, lyrics: str, query: str) -> list[str]:
        """Find lines in lyrics that match query."""
        if not lyrics:
            return []

        query_lower = query.lower()
        matching = []
        for line in lyrics.split('\n'):
            if query_lower in line.lower():
                matching.append(line.strip())

        return matching[:5]  # Return up to 5 matching lines
