"""Music file scanner service (unified interface)."""

from typing import Optional
from sqlalchemy.orm import Session

from .scanner_files import MusicScanner as FilesScanner


# Re-export for backward compatibility
SUPPORTED_EXTENSIONS = {".mp3", ".m4a", ".flac", ".wav", ".aac", ".ogg", ".wma", ".aiff"}


class MusicScanner:
    """
    Music scanner service (unified interface).

    This maintains backward compatibility by delegating to the specialized scanner.
    """

    def __init__(self, db: Session):
        self.db = db
        self._scanner = FilesScanner(db)

    def scan_directory(
        self, directory: str, collection_id: Optional[str] = None
    ) -> dict:
        """Scan a directory for music files."""
        return self._scanner.scan_directory(directory, collection_id)
