"""Data-based playlist export service for JSON, CSV, and XSPF formats."""

from pathlib import Path
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session, joinedload

from models import Playlist, Track
from .export_helpers import (
    ensure_export_dir,
    get_playlist_tracks,
    sanitize_filename,
    get_exports as list_exports,
    delete_export as remove_export,
    serialize_tracks_to_json,
    serialize_tracks_to_csv,
)


class DataPlaylistExporter:
    """Service for exporting playlists to data formats (JSON, CSV, XSPF)."""

    def __init__(self, db: Session):
        self.db = db
        self.EXPORT_DIR = ensure_export_dir()

    def export_playlist(
        self,
        playlist_id: str,
        format: str = "json",
        output_path: Optional[str] = None,
        relative_paths: bool = False,
        base_path: Optional[str] = None,
    ) -> dict:
        """
        Export a playlist to a data file format.

        Args:
            playlist_id: Playlist to export
            format: 'json', 'xspf'
            output_path: Custom output path (default: exports folder)
            relative_paths: Use relative paths instead of absolute (not used for data formats)
            base_path: Base path for relative path calculation (not used for data formats)

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

        if format == "json":
            content = self._generate_json(playlist, tracks)
            ext = ".json"
        elif format == "xspf":
            content = self._generate_xspf(playlist, tracks)
            ext = ".xspf"
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

    def export_library(
        self,
        format: str = "json",
        output_path: Optional[str] = None,
    ) -> dict:
        """Export entire library metadata."""
        tracks = (
            self.db.query(Track)
            .options(joinedload(Track.artist), joinedload(Track.album))
            .all()
        )

        if format == "json":
            content = serialize_tracks_to_json(tracks)
            ext = ".json"
        elif format == "csv":
            content = serialize_tracks_to_csv(tracks)
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

    def get_exports(self) -> list[dict]:
        """List exported files."""
        return list_exports(self.EXPORT_DIR)

    def delete_export(self, filename: str) -> bool:
        """Delete an exported file."""
        return remove_export(filename, self.EXPORT_DIR)
