# SimpleTunes

A modern music player with a SwiftUI frontend and Python FastAPI backend.

## Architecture

```
┌─────────────────┐      HTTP/REST      ┌─────────────────┐
│   SwiftUI App   │ ◄─────────────────► │  FastAPI Server │
│   (macOS 14+)   │   localhost:8000    │   (Python 3.11) │
└─────────────────┘                     └─────────────────┘
        │                                       │
        ▼                                       ▼
   AVFoundation                            SQLite DB
   (Playback)                          ~/Library/Application Support/
                                            SimpleTunes/
```

## Features

### Backend
- **Library Management**: Scan folders, extract metadata (MP3, M4A, FLAC, WAV, AAC, OGG)
- **Artists & Albums**: Automatic organization with artwork support
- **Playlists**: Create, edit, reorder, import from folders
- **Smart Playlists**: Rule-based dynamic playlists
- **Play Queue**: Full queue management with shuffle/repeat
- **Ratings & Favorites**: 1-5 star ratings, favorites, exclusions
- **Scrobbling**: Last.fm, Libre.fm, ListenBrainz integration
- **Lyrics**: Fetch and cache lyrics with sync support
- **Audio Analysis**: ReplayGain, BPM detection, gapless info
- **Tag Editing**: Read/write metadata tags
- **Watch Folders**: Auto-import new music
- **Duplicate Detection**: Find and manage duplicate tracks
- **Export**: M3U, M3U8, PLS, XSPF, JSON playlist export

### Frontend
- Browse by tracks, albums, artists, genres
- Smart lists (Recently Added, Most Played, Favorites)
- Full playback controls with queue
- Shuffle & repeat modes
- Context menus for quick actions
- Play count tracking
- Rating & favorite management
- Scrobble support

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python main.py
```

Server runs at `http://127.0.0.1:8000`

API docs available at `http://127.0.0.1:8000/docs`

### 2. Frontend

Open `frontend/SimpleTunes.xcodeproj` in Xcode and run (⌘R).

Click the refresh button (↻) to scan `~/Music` for tracks.

## API Endpoints

### Library
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stats` | Library statistics |
| POST | `/library/scan` | Scan directory for music |
| POST | `/library/import` | Import folder with playlist |

### Tracks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tracks` | Query tracks with filters |
| GET | `/tracks/{id}` | Get single track |
| POST | `/tracks/{id}/play` | Record play count |
| PUT | `/tracks/{id}/rating` | Update rating/favorite |
| GET | `/tracks/favorites` | Get favorites |
| GET | `/tracks/recent/added` | Recently added |
| GET | `/tracks/recent/played` | Recently played |
| GET | `/tracks/top/played` | Most played |

### Albums & Artists
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/albums` | List albums |
| GET | `/albums/{id}` | Album with tracks |
| GET | `/artists` | List artists |
| GET | `/artists/{id}` | Artist with albums |
| GET | `/genres` | List genres |

### Playlists
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/playlists` | List playlists |
| POST | `/playlists` | Create playlist |
| GET | `/playlists/{id}` | Playlist with tracks |
| POST | `/playlists/{id}/tracks/{trackId}` | Add track |
| DELETE | `/playlists/{id}/tracks/{trackId}` | Remove track |

### Queue
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/queue` | Get current queue |
| POST | `/queue/tracks` | Add tracks to queue |
| POST | `/queue/play-next/{id}` | Play next |
| POST | `/queue/next` | Skip to next |
| POST | `/queue/previous` | Go to previous |
| PUT | `/queue/shuffle` | Toggle shuffle |
| PUT | `/queue/repeat` | Set repeat mode |

### Other Features
- `/scrobble/*` - Scrobbling configuration and history
- `/lyrics/*` - Lyrics fetching and caching
- `/analysis/*` - Audio analysis (ReplayGain, BPM)
- `/tags/*` - Tag reading and editing
- `/watch/*` - Watch folder management
- `/duplicates/*` - Duplicate detection
- `/export/*` - Playlist export
- `/smart-playlists/*` - Smart playlist management

## Project Structure

```
SimpleTunes/
├── backend/
│   ├── main.py              # FastAPI app & routes
│   ├── database.py          # SQLite configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── requirements.txt
│   ├── routes/              # Feature route modules
│   │   ├── queue.py
│   │   ├── scrobble.py
│   │   ├── lyrics.py
│   │   └── ...
│   └── services/            # Business logic
│       ├── scanner.py
│       ├── library.py
│       ├── playlist.py
│       └── ...
└── frontend/
    ├── SimpleTunes.xcodeproj
    └── SimpleTunes/
        ├── SimpleTunesApp.swift
        ├── ContentView.swift
        ├── Models.swift
        ├── APIService.swift
        ├── PlayerViewModel.swift
        ├── TrackListView.swift
        ├── NowPlayingBar.swift
        └── Info.plist
```

## Requirements

### Backend
- Python 3.11+
- FastAPI, SQLAlchemy, Mutagen, Pillow, aiohttp

### Frontend
- macOS 14.0+
- Xcode 15+
- Swift 5.9+

## License

MIT
