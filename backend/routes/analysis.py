"""Audio analysis routes (ReplayGain, gapless)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services import ReplayGainService, GaplessService

router = APIRouter(prefix="/analysis", tags=["Audio Analysis"])


@router.get("/{track_id}")
def get_audio_analysis(track_id: str, db: Session = Depends(get_db)):
    """Get audio analysis for a track."""
    service = ReplayGainService(db)
    analysis = service.get_analysis(track_id)
    if analysis:
        return {
            "track_id": analysis.track_id,
            "track_gain": analysis.track_gain,
            "track_peak": analysis.track_peak,
            "album_gain": analysis.album_gain,
            "album_peak": analysis.album_peak,
            "encoder_delay": analysis.encoder_delay,
            "encoder_padding": analysis.encoder_padding,
            "total_samples": analysis.total_samples,
            "bpm": analysis.bpm,
            "analyzed_at": analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
        }
    return {"track_id": track_id, "analyzed": False}


@router.post("/{track_id}")
def analyze_track(track_id: str, force: bool = False, db: Session = Depends(get_db)):
    """Analyze a track for ReplayGain and gapless info."""
    service = ReplayGainService(db)
    result = service.analyze_track(track_id, force)
    if result:
        return result
    return {"error": "Analysis failed or file not found"}


@router.post("/album/{album_id}")
def analyze_album(album_id: str, db: Session = Depends(get_db)):
    """Analyze all tracks in an album and calculate album gain."""
    service = ReplayGainService(db)
    return service.analyze_album(album_id)


@router.get("/{track_id}/gain")
def get_playback_gain(
    track_id: str,
    use_album: bool = False,
    prevent_clipping: bool = True,
    db: Session = Depends(get_db)
):
    """Get gain adjustment for playback."""
    service = ReplayGainService(db)
    gain = service.get_playback_gain(track_id, use_album, prevent_clipping)
    return {"gain_db": gain}


@router.get("/{track_id}/gapless")
def get_gapless_info(
    track_id: str,
    next_track_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get gapless playback info for transitioning between tracks."""
    service = GaplessService(db)
    return service.get_gapless_info(track_id, next_track_id)


@router.post("/missing")
def analyze_missing(limit: int = 50, db: Session = Depends(get_db)):
    """Analyze tracks that haven't been analyzed yet."""
    service = ReplayGainService(db)
    return service.analyze_missing(limit)


@router.get("/stats")
def get_analysis_stats(db: Session = Depends(get_db)):
    """Get audio analysis statistics."""
    service = ReplayGainService(db)
    return service.get_stats()
