"""API route modules."""

from .queue import router as queue_router
from .smart_playlists import router as smart_playlists_router
from .scrobble import router as scrobble_router
from .lyrics import router as lyrics_router
from .analysis import router as analysis_router
from .duplicates import router as duplicates_router
from .tags import router as tags_router
from .watch import router as watch_router
from .export import router as export_router

__all__ = [
    "queue_router",
    "smart_playlists_router",
    "scrobble_router",
    "lyrics_router",
    "analysis_router",
    "duplicates_router",
    "tags_router",
    "watch_router",
    "export_router",
]
