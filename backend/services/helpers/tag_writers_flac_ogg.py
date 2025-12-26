"""FLAC and OGG tag writing helpers."""

from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen import File as MutagenFile


class FlacOggTagWriter:
    """Helper class for writing FLAC and OGG tags."""

    @staticmethod
    def write_flac_tags(filepath: str, **tags) -> dict:
        """Write tags to FLAC file."""
        try:
            audio = FLAC(filepath)

            if tags.get("title"):
                audio["title"] = tags["title"]
            if tags.get("artist"):
                audio["artist"] = tags["artist"]
            if tags.get("album"):
                audio["album"] = tags["album"]
            if tags.get("genre"):
                audio["genre"] = tags["genre"]
            if tags.get("year"):
                audio["date"] = str(tags["year"])
            if tags.get("track_number"):
                audio["tracknumber"] = str(tags["track_number"])
            if tags.get("disc_number"):
                audio["discnumber"] = str(tags["disc_number"])
            if tags.get("album_artist"):
                audio["albumartist"] = tags["album_artist"]
            if tags.get("composer"):
                audio["composer"] = tags["composer"]

            audio.save()
            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def write_ogg_tags(filepath: str, **tags) -> dict:
        """Write tags to OGG file."""
        try:
            audio = OggVorbis(filepath)

            if tags.get("title"):
                audio["title"] = [tags["title"]]
            if tags.get("artist"):
                audio["artist"] = [tags["artist"]]
            if tags.get("album"):
                audio["album"] = [tags["album"]]
            if tags.get("genre"):
                audio["genre"] = [tags["genre"]]
            if tags.get("year"):
                audio["date"] = [str(tags["year"])]
            if tags.get("track_number"):
                audio["tracknumber"] = [str(tags["track_number"])]
            if tags.get("disc_number"):
                audio["discnumber"] = [str(tags["disc_number"])]

            audio.save()
            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def write_easy_tags(filepath: str, **tags) -> dict:
        """Write tags using EasyID3 interface (generic)."""
        try:
            audio = MutagenFile(filepath, easy=True)
            if audio is None:
                return {"success": False, "error": "Unsupported format"}

            if tags.get("title"):
                audio["title"] = tags["title"]
            if tags.get("artist"):
                audio["artist"] = tags["artist"]
            if tags.get("album"):
                audio["album"] = tags["album"]
            if tags.get("genre"):
                audio["genre"] = tags["genre"]
            if tags.get("year"):
                audio["date"] = str(tags["year"])
            if tags.get("track_number"):
                audio["tracknumber"] = str(tags["track_number"])
            if tags.get("disc_number"):
                audio["discnumber"] = str(tags["disc_number"])

            audio.save()
            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}
