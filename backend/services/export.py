"""Playlist export service for M3U, PLS, and other formats."""

from pathlib import Path
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session, joinedload

from models import Playlist, Track, playlist_tracks
from database import APP_DATA_DIR


class PlaylistExportService:
    """Service for exporting playlists to various formats."""

    EXPORT_DIR = APP_DATA_DIR / "exports"

    def __init__(self, db: Session):
        self.db = db
        self.EXPORT_DIR.mkdir(exist_ok=True)

    def export_playlist(
        self,
        playlist_id: str,
        format: str = "m3u",
        output_path: Optional[str] = None,
        relative_paths: bool = False,
        base_path: Optional[str] = None,
    ) -> dict:
        """
        Export a playlist to a file.

        Args:
            playlist_id: Playlist to export
            format: 'm3u', 'm3u8', 'pls', 'xspf', 'json'
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
        tracks = self._get_playlist_tracks(playlist_id)

        if format == "m3u":
            content = self._generate_m3u(playlist, tracks, relative_paths, base_path)
            ext = ".m3u"
        elif format == "m3u8":
            content = self._generate_m3u(playlist, tracks, relative_paths, base_path, extended=True)
            ext = ".m3u8"
        elif format == "pls":
            content = self._generate_pls(playlist, tracks, relative_paths, base_path)
            ext = ".pls"
        elif format == "xspf":
            content = self._generate_xspf(playlist, tracks)
            ext = ".xspf"
        elif format == "json":
            content = self._generate_json(playlist, tracks)
            ext = ".json"
        else:
            return {"error": f"Unsupported format: {format}"}

        # Determine output path
        if output_path:
            file_path = Path(output_path)
        else:
            safe_name = self._sanitize_filename(playlist.name)
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

    def _get_playlist_tracks(self, playlist_id: str) -> list[Track]:
        """Get playlist tracks in order."""
        track_ids = (
            self.db.query(playlist_tracks.c.track_id)
            .filter(playlist_tracks.c.playlist_id == playlist_id)
            .order_by(playlist_tracks.c.position)
            .all()
        )
        track_ids = [t[0] for t in track_ids]

        # Maintain order
        tracks = []
        for tid in track_ids:
            track = (
                self.db.query(Track)
                .options(joinedload(Track.artist), joinedload(Track.album))
                .filter(Track.id == tid)
                .first()
            )
            if track:
                tracks.append(track)

        return tracks

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
            path = self._get_track_path(track.path, relative_paths, base_path)

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
            path = self._get_track_path(track.path, relative_paths, base_path)
            artist = track.artist.name if track.artist else "Unknown"
            duration = int(track.duration) if track.duration else -1

            lines.append(f"File{i}={path}")
            lines.append(f"Title{i}={artist} - {track.title}")
            lines.append(f"Length{i}={duration}")
            lines.append("")

        lines.append(f"NumberOfEntries={len(tracks)}")
        lines.append("Version=2")

        return "\n".join(lines)

    def _generate_xspf(self, playlist: Playlist, tracks: list[Track]) -> str:
        """Generate XSPF (XML Shareable Playlist Format) content."""
        import xml.etree.ElementTree as ET
        from xml.dom import minidom

        root = ET.Element("playlist")
        root.set("version", "1")
        root.set("xmlns", "http://xspf.org/ns/0/")

        # Playlist metadata
        title = ET.SubElement(root, "title")
        title.text = playlist.name

        if playlist.description:
            annotation = ET.SubElement(root, "annotation")
            annotation.text = playlist.description

        date = ET.SubElement(root, "date")
        date.text = datetime.utcnow().isoformat()

        # Track list
        tracklist = ET.SubElement(root, "trackList")

        for track in tracks:
            track_elem = ET.SubElement(tracklist, "track")

            location = ET.SubElement(track_elem, "location")
            location.text = f"file://{track.path}"

            title_elem = ET.SubElement(track_elem, "title")
            title_elem.text = track.title

            if track.artist:
                creator = ET.SubElement(track_elem, "creator")
                creator.text = track.artist.name

            if track.album:
                album_elem = ET.SubElement(track_elem, "album")
                album_elem.text = track.album.title

            if track.duration:
                duration = ET.SubElement(track_elem, "duration")
                duration.text = str(int(track.duration * 1000))  # milliseconds

            if track.track_number:
                tracknum = ET.SubElement(track_elem, "trackNum")
                tracknum.text = str(track.track_number)

        # Pretty print
        xml_str = ET.tostring(root, encoding="unicode")
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")

    def _generate_json(self, playlist: Playlist, tracks: list[Track]) -> str:
        """Generate JSON playlist content."""
        import json

        data = {
            "playlist": {
                "id": playlist.id,
                "name": playlist.name,
                "description": playlist.description,
                "track_count": len(tracks),
                "created_at": playlist.created_at.isoformat() if playlist.created_at else None,
                "exported_at": datetime.utcnow().isoformat(),
            },
            "tracks": [
                {
                    "id": track.id,
                    "path": track.path,
                    "title": track.title,
                    "artist": track.artist.name if track.artist else None,
                    "album": track.album.title if track.album else None,
                    "duration": track.duration,
                    "track_number": track.track_number,
                    "disc_number": track.disc_number,
                    "genre": track.genre,
                    "year": track.year,
                }
                for track in tracks
            ],
        }

        return json.dumps(data, indent=2)

    def _get_track_path(
        self,
        absolute_path: str,
        relative: bool,
        base_path: Optional[str],
    ) -> str:
        """Get track path, optionally relative."""
        if not relative:
            return absolute_path

        if not base_path:
            return absolute_path

        try:
            abs_track = Path(absolute_path)
            base = Path(base_path)
            return str(abs_track.relative_to(base))
        except ValueError:
            return absolute_path

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize name for use as filename."""
        # Remove/replace invalid characters
        invalid = '<>:"/\\|?*'
        for char in invalid:
            name = name.replace(char, "_")
        return name.strip()

    def import_playlist(
        self,
        file_path: str,
        name: Optional[str] = None,
    ) -> dict:
        """
        Import a playlist from file.

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

    def export_library(
        self,
        format: str = "json",
        output_path: Optional[str] = None,
    ) -> dict:
        """Export entire library metadata."""
        import json

        tracks = (
            self.db.query(Track)
            .options(joinedload(Track.artist), joinedload(Track.album))
            .all()
        )

        if format == "json":
            data = {
                "exported_at": datetime.utcnow().isoformat(),
                "track_count": len(tracks),
                "tracks": [
                    {
                        "path": t.path,
                        "title": t.title,
                        "artist": t.artist.name if t.artist else None,
                        "album": t.album.title if t.album else None,
                        "genre": t.genre,
                        "year": t.year,
                        "duration": t.duration,
                        "track_number": t.track_number,
                        "disc_number": t.disc_number,
                        "play_count": t.play_count,
                    }
                    for t in tracks
                ],
            }
            content = json.dumps(data, indent=2)
            ext = ".json"
        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "Path", "Title", "Artist", "Album", "Genre", "Year",
                "Duration", "Track", "Disc", "Play Count"
            ])
            for t in tracks:
                writer.writerow([
                    t.path, t.title,
                    t.artist.name if t.artist else "",
                    t.album.title if t.album else "",
                    t.genre or "", t.year or "",
                    t.duration or 0, t.track_number or "",
                    t.disc_number or "", t.play_count or 0,
                ])
            content = output.getvalue()
            ext = ".csv"
        else:
            return {"error": f"Unsupported format: {format}"}

        if output_path:
            file_path = Path(output_path)
        else:
            file_path = self.EXPORT_DIR / f"library_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return {
                "success": True,
                "path": str(file_path),
                "format": format,
                "track_count": len(tracks),
            }

        except Exception as e:
            return {"error": str(e)}

    def get_exports(self) -> list[dict]:
        """List exported files."""
        exports = []
        for f in self.EXPORT_DIR.iterdir():
            if f.is_file():
                exports.append({
                    "name": f.name,
                    "path": str(f),
                    "size": f.stat().st_size,
                    "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
                })
        return sorted(exports, key=lambda x: x["created"], reverse=True)

    def delete_export(self, filename: str) -> bool:
        """Delete an exported file."""
        file_path = self.EXPORT_DIR / filename
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        return False
