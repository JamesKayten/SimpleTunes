"""SimpleTunes API - Music library backend."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from mutagen import File as MutagenFile
from typing import Optional
import uuid

app = FastAPI(title="SimpleTunes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

library: dict[str, dict] = {}
playlists: dict[str, dict] = {}


class ScanRequest(BaseModel):
    directory: str


class PlaylistRequest(BaseModel):
    name: str
    track_ids: list[str] = []


def extract_metadata(filepath: str) -> Optional[dict]:
    try:
        audio = MutagenFile(filepath, easy=True)
        if audio is None:
            return None
        return {
            "id": str(uuid.uuid4()),
            "path": filepath,
            "title": audio.get("title", [Path(filepath).stem])[0],
            "artist": audio.get("artist", ["Unknown"])[0],
            "album": audio.get("album", ["Unknown"])[0],
            "duration": audio.info.length if audio.info else 0,
        }
    except Exception:
        return None


@app.get("/")
def root():
    return {"status": "ok", "service": "simpletunes"}


@app.post("/library/scan")
def scan_directory(request: ScanRequest):
    directory = Path(request.directory).expanduser()
    if not directory.exists():
        raise HTTPException(status_code=404, detail="Directory not found")
    
    extensions = {".mp3", ".m4a", ".flac", ".wav", ".aac", ".ogg"}
    added = 0
    
    for filepath in directory.rglob("*"):
        if filepath.suffix.lower() in extensions:
            metadata = extract_metadata(str(filepath))
            if metadata:
                library[metadata["id"]] = metadata
                added += 1
    
    return {"added": added, "total": len(library)}


@app.get("/library")
def get_library():
    return {"tracks": list(library.values())}


@app.get("/library/{track_id}")
def get_track(track_id: str):
    if track_id not in library:
        raise HTTPException(status_code=404, detail="Track not found")
    return library[track_id]


@app.get("/library/search/{query}")
def search_library(query: str):
    q = query.lower()
    results = [
        t for t in library.values()
        if q in t["title"].lower() or q in t["artist"].lower() or q in t["album"].lower()
    ]
    return {"tracks": results}


@app.post("/playlists")
def create_playlist(request: PlaylistRequest):
    pid = str(uuid.uuid4())
    playlists[pid] = {"id": pid, "name": request.name, "track_ids": request.track_ids}
    return playlists[pid]


@app.get("/playlists")
def get_playlists():
    return {"playlists": list(playlists.values())}


@app.get("/playlists/{playlist_id}")
def get_playlist(playlist_id: str):
    if playlist_id not in playlists:
        raise HTTPException(status_code=404, detail="Playlist not found")
    pl = playlists[playlist_id]
    tracks = [library[tid] for tid in pl["track_ids"] if tid in library]
    return {**pl, "tracks": tracks}


@app.put("/playlists/{playlist_id}/tracks/{track_id}")
def add_to_playlist(playlist_id: str, track_id: str):
    if playlist_id not in playlists:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if track_id not in library:
        raise HTTPException(status_code=404, detail="Track not found")
    if track_id not in playlists[playlist_id]["track_ids"]:
        playlists[playlist_id]["track_ids"].append(track_id)
    return playlists[playlist_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
