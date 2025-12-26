"""Gapless playback analysis service."""

from typing import Optional
from sqlalchemy.orm import Session

from models import AudioAnalysis, Track


class GaplessService:
    """Service for gapless playback analysis and transition info."""

    def __init__(self, db: Session):
        self.db = db

    def get_analysis(self, track_id: str) -> Optional[AudioAnalysis]:
        """Get audio analysis for a track."""
        return (
            self.db.query(AudioAnalysis)
            .filter(AudioAnalysis.track_id == track_id)
            .first()
        )

    def get_gapless_info(self, track_id: str, next_track_id: Optional[str] = None) -> dict:
        """
        Get gapless playback info for transitioning between tracks.

        Returns info needed for seamless playback.
        """
        current = self.get_analysis(track_id)

        result = {
            "current_track": {
                "encoder_delay": current.encoder_delay if current else None,
                "encoder_padding": current.encoder_padding if current else None,
                "total_samples": current.total_samples if current else None,
            },
            "next_track": None,
            "crossfade_recommended": False,
        }

        if next_track_id:
            next_analysis = self.get_analysis(next_track_id)
            if next_analysis:
                result["next_track"] = {
                    "encoder_delay": next_analysis.encoder_delay,
                    "encoder_padding": next_analysis.encoder_padding,
                    "total_samples": next_analysis.total_samples,
                }

        # Check if tracks are from same album (true gapless)
        if next_track_id:
            current_track = self.db.query(Track).filter(Track.id == track_id).first()
            next_track = self.db.query(Track).filter(Track.id == next_track_id).first()

            if current_track and next_track:
                same_album = current_track.album_id == next_track.album_id
                consecutive = (
                    current_track.disc_number == next_track.disc_number and
                    current_track.track_number and next_track.track_number and
                    next_track.track_number == current_track.track_number + 1
                )
                result["same_album"] = same_album
                result["consecutive_tracks"] = consecutive
                result["crossfade_recommended"] = not (same_album and consecutive)

        return result
