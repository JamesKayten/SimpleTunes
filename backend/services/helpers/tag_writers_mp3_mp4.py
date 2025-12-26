"""MP3 and MP4 tag writing helpers."""

from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TRCK, TDRC, TPOS
from mutagen.mp4 import MP4


class Mp3Mp4TagWriter:
    """Helper class for writing MP3 and MP4 tags."""

    @staticmethod
    def write_mp3_tags(filepath: str, **tags) -> dict:
        """Write tags to MP3 file."""
        try:
            try:
                audio = ID3(filepath)
            except Exception:
                audio = ID3()
                audio.save(filepath)
                audio = ID3(filepath)

            if tags.get("title"):
                audio["TIT2"] = TIT2(encoding=3, text=tags["title"])
            if tags.get("artist"):
                audio["TPE1"] = TPE1(encoding=3, text=tags["artist"])
            if tags.get("album"):
                audio["TALB"] = TALB(encoding=3, text=tags["album"])
            if tags.get("genre"):
                audio["TCON"] = TCON(encoding=3, text=tags["genre"])
            if tags.get("year"):
                audio["TDRC"] = TDRC(encoding=3, text=str(tags["year"]))
            if tags.get("track_number"):
                audio["TRCK"] = TRCK(encoding=3, text=str(tags["track_number"]))
            if tags.get("disc_number"):
                audio["TPOS"] = TPOS(encoding=3, text=str(tags["disc_number"]))

            audio.save(filepath)
            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def write_mp4_tags(filepath: str, **tags) -> dict:
        """Write tags to MP4/M4A file."""
        try:
            audio = MP4(filepath)

            if tags.get("title"):
                audio["\xa9nam"] = [tags["title"]]
            if tags.get("artist"):
                audio["\xa9ART"] = [tags["artist"]]
            if tags.get("album"):
                audio["\xa9alb"] = [tags["album"]]
            if tags.get("genre"):
                audio["\xa9gen"] = [tags["genre"]]
            if tags.get("year"):
                audio["\xa9day"] = [str(tags["year"])]
            if tags.get("track_number"):
                # MP4 track number is tuple (track, total)
                current = audio.get("trkn", [(0, 0)])[0]
                audio["trkn"] = [(tags["track_number"], current[1] if len(current) > 1 else 0)]
            if tags.get("disc_number"):
                current = audio.get("disk", [(0, 0)])[0]
                audio["disk"] = [(tags["disc_number"], current[1] if len(current) > 1 else 0)]
            if tags.get("album_artist"):
                audio["aART"] = [tags["album_artist"]]

            audio.save()
            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}
