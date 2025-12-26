"""API route modules."""

from .stats_routes import router as stats_router
from .library_routes import router as library_router
from .track_routes import router as track_router
from .album_routes import router as album_router
from .artist_routes import router as artist_router
from .genre_routes import router as genre_router
from .playlist_routes import router as playlist_router
from .collection_routes import router as collection_router
from .artwork_routes import router as artwork_router
from .stream_routes import router as stream_router
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
    "stats_router",
    "library_router",
    "track_router",
    "album_router",
    "artist_router",
    "genre_router",
    "playlist_router",
    "collection_router",
    "artwork_router",
    "stream_router",
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
