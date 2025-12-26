"""Shared response formatting functions for API routes."""

from sqlalchemy.orm import Session
from models import Track, Album, Artist, Playlist, Collection


def track_to_response(track: Track) -> dict:
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


def album_to_response(album: Album, db: Session) -> dict:
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


def artist_to_response(artist: Artist, db: Session) -> dict:
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


def playlist_to_response(playlist: Playlist) -> dict:
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


def collection_to_response(collection: Collection) -> dict:
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


def get_media_type(suffix: str) -> str:
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
