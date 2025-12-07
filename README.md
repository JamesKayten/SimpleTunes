# SimpleTunes

SwiftUI + Python music player.

## Run

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

**Frontend:** Open `frontend/SimpleTunes.xcodeproj` → Run

Click ↻ to scan ~/Music for tracks.

## API

| Endpoint | Description |
|----------|-------------|
| `POST /library/scan` | Scan directory |
| `GET /library` | All tracks |
| `GET /library/search/{q}` | Search |
| `GET /playlists` | All playlists |
| `POST /playlists` | Create playlist |
