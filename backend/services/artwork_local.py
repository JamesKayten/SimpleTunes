"""Local artwork caching and embedded extraction service."""

import aiofiles
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from PIL import Image
import io

from models import Album
from database import ARTWORK_DIR


class ArtworkLocalService:
    """Service for managing local artwork cache and embedded artwork."""

    def __init__(self, db: Session):
        self.db = db
        self.artwork_dir = ARTWORK_DIR
        self.artwork_dir.mkdir(parents=True, exist_ok=True)

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
