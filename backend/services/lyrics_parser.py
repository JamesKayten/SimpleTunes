"""Lyrics parsing and formatting utilities."""

import re
from typing import Optional


class LyricsParser:
    """Utilities for parsing and formatting lyrics data."""

    @staticmethod
    def parse_lrclib_response(data: dict) -> Optional[dict]:
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
            synced_parsed = LyricsParser.parse_lrc(synced)

        return {
            "plain_lyrics": plain,
            "synced_lyrics": synced_parsed,
            "is_instrumental": False,
            "source": "lrclib",
        }

    @staticmethod
    def parse_lrc(lrc_text: str) -> list[dict]:
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

    @staticmethod
    def find_best_match(
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

    @staticmethod
    def lyrics_to_dict(lyrics) -> dict:
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

    @staticmethod
    def get_line_at_time(synced_lyrics: list[dict], time_seconds: float) -> dict:
        """
        Get the current lyrics line at a given playback time.

        Args:
            synced_lyrics: List of synced lyrics lines
            time_seconds: Current playback time in seconds

        Returns:
            Dict with current line, next line, and progress
        """
        if not synced_lyrics:
            return {"current": None, "next": None, "progress": 0}

        current_line = None
        next_line = None

        for i, line in enumerate(synced_lyrics):
            if line["time"] <= time_seconds:
                current_line = line
                if i + 1 < len(synced_lyrics):
                    next_line = synced_lyrics[i + 1]
            else:
                break

        return {
            "current": current_line,
            "next": next_line,
            "progress": LyricsParser._calculate_line_progress(
                current_line, next_line, time_seconds
            ) if current_line else 0,
        }

    @staticmethod
    def _calculate_line_progress(
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

    @staticmethod
    def find_matching_lines(lyrics: str, query: str) -> list[str]:
        """Find lines in lyrics that match query."""
        if not lyrics:
            return []

        query_lower = query.lower()
        matching = []
        for line in lyrics.split('\n'):
            if query_lower in line.lower():
                matching.append(line.strip())

        return matching[:5]  # Return up to 5 matching lines
