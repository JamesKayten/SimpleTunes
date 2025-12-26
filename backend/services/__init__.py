"""SimpleTunes services."""

# Main unified services (for backward compatibility)
from .scanner import MusicScanner
from .artwork_fetcher import ArtworkFetcherService
from .artwork_local import ArtworkLocalService
from .library import LibraryService
from .playlist_basic import PlaylistService
from .playlist_collections import CollectionService
from .smart_playlist import SmartPlaylistService
from .queue_manager import QueueService
from .scrobble import ScrobbleService
from .lyrics import LyricsService
from .analysis_replaygain import ReplayGainService
from .analysis_gapless import GaplessService
from .duplicates_detector import DuplicateDetector
from .duplicates_resolver import DuplicateResolver
from .tag_reader import TagReaderService
from .tag_writer import TagWriterService
from .watcher import FolderWatcherService, get_watcher
from .export import PlaylistExportService
from .export_text import TextPlaylistExporter
from .export_data import DataPlaylistExporter
from . import export_helpers

# Split service modules (for advanced usage)
from .lyrics_fetcher import LyricsService as LyricsFetcherService
from .lyrics_parser import LyricsParser
from .smart_playlist_builder import SmartPlaylistRule
from .smart_playlist_evaluator import SmartPlaylistService as SmartPlaylistEvaluatorService
from .library_queries import LibraryQueryService
from .library_stats import LibraryStatsService
from .scanner_files import MusicScanner as FileScannerService
from .scanner_metadata import MetadataExtractor

# Backward compatibility aliases
ArtworkService = ArtworkFetcherService
AudioAnalysisService = ReplayGainService

__all__ = [
    # Main unified services
    "MusicScanner",
    "ArtworkFetcherService",
    "ArtworkLocalService",
    "ArtworkService",  # Backward compatibility
    "LibraryService",
    "PlaylistService",
    "CollectionService",
    "SmartPlaylistService",
    "QueueService",
    "ScrobbleService",
    "LyricsService",
    "ReplayGainService",
    "GaplessService",
    "AudioAnalysisService",  # Backward compatibility
    "DuplicateDetector",
    "DuplicateResolver",
    "TagReaderService",
    "TagWriterService",
    "FolderWatcherService",
    "PlaylistExportService",
    "TextPlaylistExporter",
    "DataPlaylistExporter",
    "export_helpers",
    "get_watcher",
    # Split service modules
    "LyricsFetcherService",
    "LyricsParser",
    "SmartPlaylistRule",
    "SmartPlaylistEvaluatorService",
    "LibraryQueryService",
    "LibraryStatsService",
    "FileScannerService",
    "MetadataExtractor",
]
