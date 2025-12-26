"""SimpleTunes API - Comprehensive music library backend."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db

# Import all route modules
from routes import (
    stats_router,
    library_router,
    track_router,
    album_router,
    artist_router,
    genre_router,
    playlist_router,
    collection_router,
    artwork_router,
    stream_router,
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

# Include all routers
app.include_router(stats_router)
app.include_router(library_router)
app.include_router(track_router)
app.include_router(album_router)
app.include_router(artist_router)
app.include_router(genre_router)
app.include_router(playlist_router)
app.include_router(collection_router)
app.include_router(artwork_router)
app.include_router(stream_router)
app.include_router(queue_router)
app.include_router(smart_playlists_router)
app.include_router(scrobble_router)
app.include_router(lyrics_router)
app.include_router(analysis_router)
app.include_router(duplicates_router)
app.include_router(tags_router)
app.include_router(watch_router)
app.include_router(export_router)


@app.get("/")
def root():
    return {"status": "ok", "service": "simpletunes", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
