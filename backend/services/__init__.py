"""SimpleTunes services."""

from .scanner import MusicScanner
from .artwork import ArtworkService
from .library import LibraryService
from .playlist import PlaylistService
from .smart_playlist import SmartPlaylistService
from .queue import QueueService
from .scrobble import ScrobbleService
from .lyrics import LyricsService
from .audio_analysis import AudioAnalysisService
from .duplicates import DuplicateService
from .tag_editor import TagEditorService
from .folder_watcher import FolderWatcherService, get_watcher
from .export import PlaylistExportService

__all__ = [
    "MusicScanner",
    "ArtworkService",
    "LibraryService",
    "PlaylistService",
    "SmartPlaylistService",
    "QueueService",
    "ScrobbleService",
    "LyricsService",
    "AudioAnalysisService",
    "DuplicateService",
    "TagEditorService",
    "FolderWatcherService",
    "PlaylistExportService",
    "get_watcher",
]
