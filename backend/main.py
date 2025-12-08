"""SimpleTunes API - Comprehensive music library backend."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Optional

from database import get_db, init_db, ARTWORK_DIR
from models import Track, Album, Artist, Playlist, Collection, TrackRating
from schemas import (
    ScanRequest,
    ScanResponse,
    LibraryQuery,
    TrackResponse,
    AlbumResponse,
    ArtistResponse,
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistResponse,
    PlaylistDetailResponse,
    PlaylistFromFolderRequest,
    RatingUpdate,
    RatingResponse,
    CollectionCreate,
    CollectionResponse,
    ImportFolderRequest,
    ImportResponse,
    LibraryStats,
    SortField,
    SortOrder,
)
from services import MusicScanner, ArtworkService, LibraryService, PlaylistService

# Import new route modules
from routes import (
    queue_router,
    smart_playlists_router,
    scrobble_router,
    lyrics_router,
    analysis_router,
    duplicates_router,
    tags_router,
    watch_router,
    export_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title="SimpleTunes API",
    description="Comprehensive music library management backend",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include new feature routers
app.include_router(queue_router)
app.include_router(smart_playlists_router)
app.include_router(scrobble_router)
app.include_router(lyrics_router)
app.include_router(analysis_router)
app.include_router(duplicates_router)
app.include_router(tags_router)
app.include_router(watch_router)
app.include_router(export_router)


# ============================================================================
# Health & Status
# ============================================================================


@app.get("/")
def root():
    return {"status": "ok", "service": "simpletunes", "version": "2.0.0"}


@app.get("/stats", response_model=LibraryStats)
def get_stats(db: Session = Depends(get_db)):
    """Get library statistics."""
    service = LibraryService(db)
    return service.get_stats()


# ============================================================================
# Library Scanning
# ============================================================================


@app.post("/library/scan", response_model=ScanResponse)
def scan_directory(request: ScanRequest, db: Session = Depends(get_db)):
    """Scan a directory for music files."""
    try:
        scanner = MusicScanner(db)
        result = scanner.scan_directory(request.directory)
        return ScanResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/library/import", response_model=ImportResponse)
def import_folder(request: ImportFolderRequest, db: Session = Depends(get_db)):
    """Import a folder and optionally create a playlist."""
    try:
        playlist_service = PlaylistService(db)

        if request.create_playlist:
            playlist, tracks_added = playlist_service.create_playlist_from_folder(
                request.folder_path, request.playlist_name
            )
            return ImportResponse(
                collection_id=playlist.id,  # Using playlist as collection reference
                playlist_id=playlist.id,
                tracks_added=tracks_added,
                total_tracks=tracks_added,
            )
        else:
            scanner = MusicScanner(db)
            result = scanner.scan_directory(request.folder_path)
            return ImportResponse(
                collection_id="",
                playlist_id=None,
                tracks_added=result["added"],
                total_tracks=result["total"],
            )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Tracks
# ============================================================================


@app.get("/tracks")
def get_tracks(
    search: Optional[str] = None,
    genre: Optional[str] = None,
    artist_id: Optional[str] = None,
    album_id: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    rating_min: Optional[int] = None,
    favorites_only: bool = False,
    exclude_removed: bool = True,
    sort_by: SortField = SortField.TITLE,
    sort_order: SortOrder = SortOrder.ASC,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Query tracks with filtering and sorting."""
    query = LibraryQuery(
        search=search,
        genre=genre,
        artist_id=artist_id,
        album_id=album_id,
        year_from=year_from,
        year_to=year_to,
        rating_min=rating_min,
        favorites_only=favorites_only,
        exclude_removed=exclude_removed,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )

    service = LibraryService(db)
    tracks, total = service.query_tracks(query)

    return {
        "tracks": [_track_to_response(t) for t in tracks],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# IMPORTANT: Specific routes MUST come before /{track_id} to avoid being intercepted
@app.get("/tracks/recent/played")
def get_recently_played(limit: int = 50, db: Session = Depends(get_db)):
    """Get recently played tracks."""
    service = LibraryService(db)
    tracks = service.get_recently_played(limit)
    return {"tracks": [_track_to_response(t) for t in tracks]}


@app.get("/tracks/recent/added")
def get_recently_added(limit: int = 50, db: Session = Depends(get_db)):
    """Get recently added tracks."""
    service = LibraryService(db)
    tracks = service.get_recently_added(limit)
    return {"tracks": [_track_to_response(t) for t in tracks]}


@app.get("/tracks/top/played")
def get_most_played(limit: int = 50, db: Session = Depends(get_db)):
    """Get most played tracks."""
    service = LibraryService(db)
    tracks = service.get_most_played(limit)
    return {"tracks": [_track_to_response(t) for t in tracks]}


@app.get("/tracks/top/rated")
def get_top_rated(limit: int = 50, db: Session = Depends(get_db)):
    """Get highest rated tracks."""
    service = LibraryService(db)
    tracks = service.get_top_rated(limit)
    return {"tracks": [_track_to_response(t) for t in tracks]}


@app.get("/tracks/favorites")
def get_favorites(db: Session = Depends(get_db)):
    """Get all favorite tracks."""
    service = LibraryService(db)
    tracks = service.get_favorites()
    return {"tracks": [_track_to_response(t) for t in tracks]}


@app.get("/tracks/excluded")
def get_excluded(db: Session = Depends(get_db)):
    """Get all excluded tracks."""
    service = LibraryService(db)
    tracks = service.get_excluded()
    return {"tracks": [_track_to_response(t) for t in tracks]}


# Dynamic route - must come AFTER all specific /tracks/* routes
@app.get("/tracks/{track_id}")
def get_track(track_id: str, db: Session = Depends(get_db)):
    """Get a single track by ID."""
    service = LibraryService(db)
    track = service.get_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return _track_to_response(track)


@app.post("/tracks/{track_id}/play")
def play_track(track_id: str, db: Session = Depends(get_db)):
    """Record a track play and increment play count."""
    service = LibraryService(db)
    try:
        track = service.increment_play_count(track_id)
        return {"play_count": track.play_count}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Ratings
# ============================================================================


@app.put("/tracks/{track_id}/rating", response_model=RatingResponse)
def update_rating(
    track_id: str, rating: RatingUpdate, db: Session = Depends(get_db)
):
    """Update track rating, favorite status, or exclusion."""
    service = LibraryService(db)
    try:
        track_rating = service.rate_track(
            track_id,
            rating=rating.rating,
            excluded=rating.excluded,
            favorite=rating.favorite,
            notes=rating.notes,
        )
        return RatingResponse(
            track_id=track_rating.track_id,
            rating=track_rating.rating,
            excluded=track_rating.excluded,
            favorite=track_rating.favorite,
            notes=track_rating.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Albums
# ============================================================================


@app.get("/albums")
def get_albums(
    artist_id: Optional[str] = None,
    genre: Optional[str] = None,
    year: Optional[int] = None,
    sort_by: str = "title",
    sort_order: str = "asc",
    db: Session = Depends(get_db),
):
    """Get albums with optional filtering."""
    service = LibraryService(db)
    albums = service.get_albums(artist_id, genre, year, sort_by, sort_order)
    return {"albums": [_album_to_response(a, db) for a in albums]}


@app.get("/albums/{album_id}")
def get_album(album_id: str, db: Session = Depends(get_db)):
    """Get album details with tracks."""
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    service = LibraryService(db)
    tracks = service.get_tracks_by_album(album_id)

    return {
        **_album_to_response(album, db),
        "tracks": [_track_to_response(t) for t in tracks],
    }


# ============================================================================
# Artists
# ============================================================================


@app.get("/artists")
def get_artists(sort_by: str = "name", db: Session = Depends(get_db)):
    """Get all artists."""
    service = LibraryService(db)
    artists = service.get_artists(sort_by)
    return {"artists": [_artist_to_response(a, db) for a in artists]}


@app.get("/artists/{artist_id}")
def get_artist(artist_id: str, db: Session = Depends(get_db)):
    """Get artist details with albums."""
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    service = LibraryService(db)
    albums = service.get_albums(artist_id=artist_id)
    tracks = service.get_tracks_by_artist(artist_id)

    return {
        **_artist_to_response(artist, db),
        "albums": [_album_to_response(a, db) for a in albums],
        "tracks": [_track_to_response(t) for t in tracks],
    }


# ============================================================================
# Genres & Years
# ============================================================================


@app.get("/genres")
def get_genres(db: Session = Depends(get_db)):
    """Get all genres with track counts."""
    service = LibraryService(db)
    return {"genres": service.get_genres()}


@app.get("/years")
def get_years(db: Session = Depends(get_db)):
    """Get all years with track counts."""
    service = LibraryService(db)
    return {"years": service.get_years()}


@app.get("/decades")
def get_decades(db: Session = Depends(get_db)):
    """Get decades with track counts."""
    service = LibraryService(db)
    return {"decades": service.get_decades()}


# ============================================================================
# Playlists
# ============================================================================


@app.get("/playlists")
def get_playlists(db: Session = Depends(get_db)):
    """Get all playlists."""
    service = PlaylistService(db)
    playlists = service.get_all_playlists()
    return {"playlists": [_playlist_to_response(p) for p in playlists]}


@app.post("/playlists", response_model=PlaylistResponse)
def create_playlist(request: PlaylistCreate, db: Session = Depends(get_db)):
    """Create a new empty playlist."""
    service = PlaylistService(db)
    playlist = service.create_playlist(request.name, request.description)
    return _playlist_to_response(playlist)


@app.post("/playlists/from-folder")
def create_playlist_from_folder(
    request: PlaylistFromFolderRequest, db: Session = Depends(get_db)
):
    """Create a playlist from a dropped folder."""
    service = PlaylistService(db)
    try:
        playlist, tracks_added = service.create_playlist_from_folder(
            request.folder_path, request.name
        )
        return {
            "playlist": _playlist_to_response(playlist),
            "tracks_added": tracks_added,
        }
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/playlists/{playlist_id}")
def get_playlist(playlist_id: str, db: Session = Depends(get_db)):
    """Get playlist with tracks."""
    service = PlaylistService(db)
    playlist = service.get_playlist(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return {
        **_playlist_to_response(playlist),
        "tracks": [_track_to_response(t) for t in playlist.tracks],
    }


@app.put("/playlists/{playlist_id}", response_model=PlaylistResponse)
def update_playlist(
    playlist_id: str, request: PlaylistUpdate, db: Session = Depends(get_db)
):
    """Update playlist metadata."""
    service = PlaylistService(db)
    try:
        playlist = service.update_playlist(
            playlist_id, request.name, request.description
        )
        return _playlist_to_response(playlist)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/playlists/{playlist_id}")
def delete_playlist(playlist_id: str, db: Session = Depends(get_db)):
    """Delete a playlist."""
    service = PlaylistService(db)
    if service.delete_playlist(playlist_id):
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="Playlist not found")


@app.post("/playlists/{playlist_id}/tracks/{track_id}")
def add_track_to_playlist(
    playlist_id: str,
    track_id: str,
    position: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Add a track to a playlist."""
    service = PlaylistService(db)
    if service.add_track_to_playlist(playlist_id, track_id, position):
        return {"added": True}
    raise HTTPException(status_code=404, detail="Playlist or track not found")


@app.delete("/playlists/{playlist_id}/tracks/{track_id}")
def remove_track_from_playlist(
    playlist_id: str, track_id: str, db: Session = Depends(get_db)
):
    """Remove a track from a playlist."""
    service = PlaylistService(db)
    if service.remove_track_from_playlist(playlist_id, track_id):
        return {"removed": True}
    raise HTTPException(status_code=404, detail="Track not in playlist")


@app.put("/playlists/{playlist_id}/reorder")
def reorder_playlist(
    playlist_id: str, track_ids: list[str], db: Session = Depends(get_db)
):
    """Reorder tracks in a playlist."""
    service = PlaylistService(db)
    try:
        playlist = service.reorder_playlist(playlist_id, track_ids)
        return {"reordered": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/playlists/{playlist_id}/add-folder")
def add_folder_to_playlist(
    playlist_id: str, folder_path: str, db: Session = Depends(get_db)
):
    """Add all tracks from a folder to an existing playlist."""
    service = PlaylistService(db)
    try:
        added = service.add_folder_to_playlist(playlist_id, folder_path)
        return {"added": added}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Collections
# ============================================================================


@app.get("/collections")
def get_collections(db: Session = Depends(get_db)):
    """Get all imported collections."""
    service = PlaylistService(db)
    collections = service.get_collections()
    return {"collections": [_collection_to_response(c) for c in collections]}


@app.get("/collections/{collection_id}/tracks")
def get_collection_tracks(collection_id: str, db: Session = Depends(get_db)):
    """Get all tracks in a collection."""
    service = PlaylistService(db)
    tracks = service.get_collection_tracks(collection_id)
    return {"tracks": [_track_to_response(t) for t in tracks]}


@app.post("/collections/{collection_id}/rescan")
def rescan_collection(collection_id: str, db: Session = Depends(get_db)):
    """Rescan a collection for new/changed tracks."""
    service = PlaylistService(db)
    try:
        result = service.rescan_collection(collection_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/collections/{collection_id}")
def delete_collection(
    collection_id: str,
    delete_tracks: bool = False,
    db: Session = Depends(get_db),
):
    """Delete a collection."""
    service = PlaylistService(db)
    if service.delete_collection(collection_id, delete_tracks):
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="Collection not found")


# ============================================================================
# Artwork
# ============================================================================


@app.post("/artwork/album/{album_id}")
async def fetch_album_artwork(
    album_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Fetch album artwork from online sources."""
    service = ArtworkService(db)
    result = await service.fetch_album_cover(album_id)
    if result:
        return {"path": result}
    return {"path": None, "message": "No artwork found"}


@app.post("/artwork/artist/{artist_id}")
async def fetch_artist_artwork(
    artist_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Fetch artist image from online sources."""
    service = ArtworkService(db)
    result = await service.fetch_artist_image(artist_id)
    if result:
        return {"path": result}
    return {"path": None, "message": "No artwork found"}


@app.post("/artwork/fetch-missing")
async def fetch_missing_artwork(
    limit: int = 50, db: Session = Depends(get_db)
):
    """Fetch artwork for all albums missing covers."""
    service = ArtworkService(db)
    result = await service.fetch_all_missing_covers(limit)
    return result


@app.get("/artwork/{filename}")
def serve_artwork(filename: str):
    """Serve cached artwork files."""
    file_path = ARTWORK_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Artwork not found")
    return FileResponse(file_path)


# ============================================================================
# File Streaming
# ============================================================================


@app.get("/stream/{track_id}")
def stream_track(track_id: str, db: Session = Depends(get_db)):
    """Stream a music file."""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    file_path = Path(track.path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_path,
        media_type=_get_media_type(file_path.suffix),
        filename=file_path.name,
    )


# ============================================================================
# Helper Functions
# ============================================================================


def _track_to_response(track: Track) -> dict:
    """Convert Track model to response dict."""
    return {
        "id": track.id,
        "path": track.path,
        "title": track.title,
        "artist_id": track.artist_id,
        "artist_name": track.artist.name if track.artist else None,
        "album_id": track.album_id,
        "album_name": track.album.title if track.album else None,
        "cover_path": track.album.cover_path if track.album else None,
        "duration": track.duration,
        "track_number": track.track_number,
        "disc_number": track.disc_number,
        "genre": track.genre,
        "year": track.year,
        "play_count": track.play_count,
        "rating": track.rating.rating if track.rating else None,
        "excluded": track.rating.excluded if track.rating else False,
        "favorite": track.rating.favorite if track.rating else False,
        "date_added": track.date_added.isoformat() if track.date_added else None,
    }


def _album_to_response(album: Album, db: Session) -> dict:
    """Convert Album model to response dict."""
    track_count = db.query(Track).filter(Track.album_id == album.id).count()
    return {
        "id": album.id,
        "title": album.title,
        "artist_id": album.artist_id,
        "artist_name": album.artist.name if album.artist else None,
        "year": album.year,
        "genre": album.genre,
        "cover_path": album.cover_path,
        "total_tracks": album.total_tracks,
        "track_count": track_count,
    }


def _artist_to_response(artist: Artist, db: Session) -> dict:
    """Convert Artist model to response dict."""
    album_count = db.query(Album).filter(Album.artist_id == artist.id).count()
    track_count = db.query(Track).filter(Track.artist_id == artist.id).count()
    return {
        "id": artist.id,
        "name": artist.name,
        "sort_name": artist.sort_name,
        "bio": artist.bio,
        "image_path": artist.image_path,
        "album_count": album_count,
        "track_count": track_count,
    }


def _playlist_to_response(playlist: Playlist) -> dict:
    """Convert Playlist model to response dict."""
    return {
        "id": playlist.id,
        "name": playlist.name,
        "description": playlist.description,
        "is_smart": playlist.is_smart,
        "track_count": getattr(playlist, "track_count", 0),
        "total_duration": getattr(playlist, "total_duration", 0),
        "cover_path": playlist.cover_path,
        "created_at": playlist.created_at.isoformat() if playlist.created_at else None,
        "updated_at": playlist.updated_at.isoformat() if playlist.updated_at else None,
    }


def _collection_to_response(collection: Collection) -> dict:
    """Convert Collection model to response dict."""
    return {
        "id": collection.id,
        "name": collection.name,
        "path": collection.path,
        "track_count": collection.track_count,
        "total_duration": collection.total_duration,
        "created_at": (
            collection.created_at.isoformat() if collection.created_at else None
        ),
        "last_scanned": (
            collection.last_scanned.isoformat() if collection.last_scanned else None
        ),
    }


def _get_media_type(suffix: str) -> str:
    """Get MIME type for audio file extension."""
    types = {
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".flac": "audio/flac",
        ".wav": "audio/wav",
        ".aac": "audio/aac",
        ".ogg": "audio/ogg",
        ".wma": "audio/x-ms-wma",
        ".aiff": "audio/aiff",
    }
    return types.get(suffix.lower(), "audio/mpeg")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
