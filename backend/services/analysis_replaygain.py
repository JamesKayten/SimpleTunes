"""ReplayGain audio analysis service."""

from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import AudioAnalysis, Track, Album
from .helpers.audio_analysis import AudioAnalyzer


class ReplayGainService:
    """Service for ReplayGain audio analysis (track/album gain)."""

    def __init__(self, db: Session):
        self.db = db

    def get_analysis(self, track_id: str) -> Optional[AudioAnalysis]:
        """Get audio analysis for a track."""
        return (
            self.db.query(AudioAnalysis)
            .filter(AudioAnalysis.track_id == track_id)
            .first()
        )

    def analyze_track(self, track_id: str, force: bool = False) -> Optional[dict]:
        """
        Analyze a single track for ReplayGain and gapless info.

        Requires ffmpeg to be installed.
        """
        # Check if already analyzed
        if not force:
            existing = self.get_analysis(track_id)
            if existing:
                return self._analysis_to_dict(existing)

        track = self.db.query(Track).filter(Track.id == track_id).first()
        if not track:
            return None

        filepath = Path(track.path)
        if not filepath.exists():
            return None

        try:
            # Analyze with ffmpeg
            analysis_data = AudioAnalyzer.analyze_with_ffmpeg(str(filepath))

            if analysis_data:
                return self._save_analysis(track_id, analysis_data)

        except Exception as e:
            return {"error": str(e)}

        return None

    def _save_analysis(self, track_id: str, data: dict) -> dict:
        """Save audio analysis to database."""
        # Delete existing
        self.db.query(AudioAnalysis).filter(
            AudioAnalysis.track_id == track_id
        ).delete()

        analysis = AudioAnalysis(
            track_id=track_id,
            track_gain=data.get("track_gain"),
            track_peak=data.get("track_peak"),
            encoder_delay=data.get("encoder_delay"),
            encoder_padding=data.get("encoder_padding"),
            total_samples=data.get("total_samples"),
            bpm=data.get("bpm"),
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        return self._analysis_to_dict(analysis)

    def _analysis_to_dict(self, analysis: AudioAnalysis) -> dict:
        """Convert AudioAnalysis to dict."""
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

    def analyze_album(self, album_id: str) -> dict:
        """
        Analyze all tracks in an album and calculate album gain.

        Album gain ensures consistent volume across an album while
        preserving relative dynamics between tracks.
        """
        tracks = (
            self.db.query(Track)
            .filter(Track.album_id == album_id)
            .order_by(Track.disc_number, Track.track_number)
            .all()
        )

        if not tracks:
            return {"error": "No tracks in album"}

        results = {"analyzed": 0, "failed": 0, "tracks": []}
        track_gains = []
        max_peak = 0.0

        for track in tracks:
            analysis = self.analyze_track(track.id)
            if analysis and "track_gain" in analysis:
                results["analyzed"] += 1
                results["tracks"].append(analysis)
                track_gains.append(analysis["track_gain"])
                if analysis.get("track_peak"):
                    max_peak = max(max_peak, analysis["track_peak"])
            else:
                results["failed"] += 1

        # Calculate album gain (average of track gains)
        if track_gains:
            album_gain = sum(track_gains) / len(track_gains)

            # Update all tracks with album gain
            for track in tracks:
                analysis = self.get_analysis(track.id)
                if analysis:
                    analysis.album_gain = album_gain
                    analysis.album_peak = max_peak

            self.db.commit()
            results["album_gain"] = album_gain
            results["album_peak"] = max_peak

        return results

    def get_playback_gain(
        self,
        track_id: str,
        use_album_gain: bool = False,
        prevent_clipping: bool = True,
    ) -> Optional[float]:
        """
        Get the gain adjustment to apply during playback.

        Args:
            track_id: Track to get gain for
            use_album_gain: Use album gain instead of track gain
            prevent_clipping: Reduce gain if it would cause clipping

        Returns:
            Gain adjustment in dB, or None if not analyzed
        """
        analysis = self.get_analysis(track_id)
        if not analysis:
            return None

        if use_album_gain and analysis.album_gain is not None:
            gain = analysis.album_gain
            peak = analysis.album_peak
        else:
            gain = analysis.track_gain
            peak = analysis.track_peak

        if gain is None:
            return None

        # Prevent clipping
        if prevent_clipping and peak:
            # Calculate max gain before clipping
            max_gain = -20 * (peak ** 0.5) if peak > 0 else 0
            if gain > max_gain:
                gain = max_gain

        return gain

    def analyze_missing(self, limit: int = 50) -> dict:
        """Analyze tracks that haven't been analyzed yet."""
        analyzed_ids = self.db.query(AudioAnalysis.track_id).subquery()
        tracks = (
            self.db.query(Track)
            .filter(~Track.id.in_(analyzed_ids))
            .limit(limit)
            .all()
        )

        results = {"analyzed": 0, "failed": 0, "total": len(tracks)}

        for track in tracks:
            try:
                result = self.analyze_track(track.id)
                if result and "error" not in result:
                    results["analyzed"] += 1
                else:
                    results["failed"] += 1
            except Exception:
                results["failed"] += 1

        return results

    def get_stats(self) -> dict:
        """Get audio analysis statistics."""
        total_tracks = self.db.query(Track).count()
        analyzed = self.db.query(AudioAnalysis).count()

        avg_gain = (
            self.db.query(func.avg(AudioAnalysis.track_gain))
            .scalar()
        )

        with_bpm = (
            self.db.query(AudioAnalysis)
            .filter(AudioAnalysis.bpm.isnot(None))
            .count()
        )

        return {
            "total_tracks": total_tracks,
            "analyzed_tracks": analyzed,
            "pending_tracks": total_tracks - analyzed,
            "average_gain": round(avg_gain, 2) if avg_gain else None,
            "tracks_with_bpm": with_bpm,
        }
