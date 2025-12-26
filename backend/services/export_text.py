"""Text-based playlist export service for M3U, M3U8, and PLS formats."""

from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from models import Playlist, Track, playlist_tracks
from .export_helpers import (
    ensure_export_dir,
    get_playlist_tracks,
    sanitize_filename,
    get_exports as list_exports,
    delete_export as remove_export,
    get_track_path,
    EXPORT_DIR,
)


class TextPlaylistExporter:
    """Service for exporting playlists to text-based formats (M3U, M3U8, PLS)."""

    def __init__(self, db: Session):
        self.db = db
        self.EXPORT_DIR = ensure_export_dir()

    def export_playlist(
        self,
        playlist_id: str,
        format: str = "m3u",
        output_path: Optional[str] = None,
        relative_paths: bool = False,
        base_path: Optional[str] = None,
    ) -> dict:
        """
        Export a playlist to a text-based file format.

        Args:
            playlist_id: Playlist to export
            format: 'm3u', 'm3u8', 'pls'
            output_path: Custom output path (default: exports folder)
            relative_paths: Use relative paths instead of absolute
            base_path: Base path for relative path calculation

        Returns:
            Dict with export info and path
        """
        playlist = (
            self.db.query(Playlist)
            .filter(Playlist.id == playlist_id)
            .first()
        )
        if not playlist:
            return {"error": "Playlist not found"}

        # Get tracks in order
        tracks = get_playlist_tracks(self.db, playlist_id)

        if format == "m3u":
            content = self._generate_m3u(playlist, tracks, relative_paths, base_path)
            ext = ".m3u"
        elif format == "m3u8":
            content = self._generate_m3u(playlist, tracks, relative_paths, base_path, extended=True)
            ext = ".m3u8"
        elif format == "pls":
            content = self._generate_pls(playlist, tracks, relative_paths, base_path)
            ext = ".pls"
        else:
            return {"error": f"Unsupported format: {format}"}

        # Determine output path
        if output_path:
            file_path = Path(output_path)
        else:
            safe_name = sanitize_filename(playlist.name)
            file_path = self.EXPORT_DIR / f"{safe_name}{ext}"

        # Write file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return {
                "success": True,
                "path": str(file_path),
                "format": format,
                "track_count": len(tracks),
                "playlist_name": playlist.name,
            }

        except Exception as e:
            return {"error": str(e)}

    def import_playlist(
        self,
        file_path: str,
        name: Optional[str] = None,
    ) -> dict:
        """
        Import a playlist from a text-based file.

        Supports M3U, M3U8, PLS formats.
        """
        path = Path(file_path)
        if not path.exists():
            return {"error": "File not found"}

        ext = path.suffix.lower()

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            if ext in (".m3u", ".m3u8"):
                tracks = self._parse_m3u(content)
            elif ext == ".pls":
                tracks = self._parse_pls(content)
            else:
                return {"error": f"Unsupported format: {ext}"}

            # Create playlist
            playlist_name = name or path.stem
            playlist = Playlist(name=playlist_name)
            self.db.add(playlist)
            self.db.flush()

            # Find and add tracks
            added = 0
            not_found = []

            for i, track_path in enumerate(tracks):
                # Try to find track in library
                track = (
                    self.db.query(Track)
                    .filter(Track.path == track_path)
                    .first()
                )

                if track:
                    self.db.execute(
                        playlist_tracks.insert().values(
                            playlist_id=playlist.id,
                            track_id=track.id,
                            position=i,
                        )
                    )
                    added += 1
                else:
                    not_found.append(track_path)

            self.db.commit()

            return {
                "success": True,
                "playlist_id": playlist.id,
                "playlist_name": playlist_name,
                "tracks_added": added,
                "tracks_not_found": len(not_found),
                "not_found_paths": not_found[:10],  # First 10
            }

        except Exception as e:
            return {"error": str(e)}

    def _generate_m3u(
        self,
        playlist: Playlist,
        tracks: list[Track],
        relative_paths: bool = False,
        base_path: Optional[str] = None,
        extended: bool = False,
    ) -> str:
        """Generate M3U/M3U8 playlist content."""
        lines = []

        if extended:
            lines.append("#EXTM3U")
            lines.append(f"#PLAYLIST:{playlist.name}")
            lines.append("")

        for track in tracks:
            path = get_track_path(track.path, relative_paths, base_path)

            if extended:
                duration = int(track.duration) if track.duration else -1
                artist = track.artist.name if track.artist else "Unknown"
                lines.append(f"#EXTINF:{duration},{artist} - {track.title}")

            lines.append(path)

            if extended:
                lines.append("")

        return "\n".join(lines)

    def _generate_pls(
        self,
        playlist: Playlist,
        tracks: list[Track],
        relative_paths: bool = False,
        base_path: Optional[str] = None,
    ) -> str:
        """Generate PLS playlist content."""
        lines = ["[playlist]", ""]

        for i, track in enumerate(tracks, 1):
            path = get_track_path(track.path, relative_paths, base_path)
            artist = track.artist.name if track.artist else "Unknown"
            duration = int(track.duration) if track.duration else -1

            lines.append(f"File{i}={path}")
            lines.append(f"Title{i}={artist} - {track.title}")
            lines.append(f"Length{i}={duration}")
            lines.append("")

        lines.append(f"NumberOfEntries={len(tracks)}")
        lines.append("Version=2")

        return "\n".join(lines)

    def _parse_m3u(self, content: str) -> list[str]:
        """Parse M3U/M3U8 content."""
        tracks = []
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                tracks.append(line)
        return tracks

    def _parse_pls(self, content: str) -> list[str]:
        """Parse PLS content."""
        tracks = []
        for line in content.split("\n"):
            line = line.strip()
            if line.lower().startswith("file"):
                # Format: File1=/path/to/file.mp3
                parts = line.split("=", 1)
                if len(parts) == 2:
                    tracks.append(parts[1])
        return tracks

    def get_exports(self) -> list[dict]:
        """List exported files."""
        return list_exports(self.EXPORT_DIR)

    def delete_export(self, filename: str) -> bool:
        """Delete an exported file."""
        return remove_export(filename, self.EXPORT_DIR)
