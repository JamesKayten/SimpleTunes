"""Audio analysis service for ReplayGain and gapless playback."""

import subprocess
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session, joinedload

from models import AudioAnalysis, Track, Album


class AudioAnalysisService:
    """Service for analyzing audio files (ReplayGain, gapless info, BPM)."""

    # Target loudness for ReplayGain (EBU R128 standard)
    TARGET_LOUDNESS = -18.0  # LUFS

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
            analysis_data = self._analyze_with_ffmpeg(str(filepath))

            if analysis_data:
                return self._save_analysis(track_id, analysis_data)

        except Exception as e:
            return {"error": str(e)}

        return None

    def _analyze_with_ffmpeg(self, filepath: str) -> Optional[dict]:
        """Use ffmpeg to analyze audio file."""
        try:
            # Get loudness using ebur128 filter
            cmd = [
                "ffmpeg",
                "-i", filepath,
                "-af", "ebur128=framelog=verbose",
                "-f", "null",
                "-"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Parse ffmpeg output for loudness info
            output = result.stderr
            analysis = {}

            # Extract integrated loudness
            for line in output.split('\n'):
                if "I:" in line and "LUFS" in line:
                    try:
                        # Extract the LUFS value
                        parts = line.split("I:")
                        if len(parts) > 1:
                            lufs_str = parts[1].split("LUFS")[0].strip()
                            integrated_loudness = float(lufs_str)
                            analysis["track_gain"] = self.TARGET_LOUDNESS - integrated_loudness
                    except (ValueError, IndexError):
                        pass

                if "Peak:" in line:
                    try:
                        parts = line.split("Peak:")
                        if len(parts) > 1:
                            peak_str = parts[1].split("dBFS")[0].strip()
                            peak_db = float(peak_str)
                            # Convert dBFS to linear (0.0-1.0)
                            analysis["track_peak"] = 10 ** (peak_db / 20)
                    except (ValueError, IndexError):
                        pass

            # Get gapless info using ffprobe
            gapless_info = self._get_gapless_info(filepath)
            if gapless_info:
                analysis.update(gapless_info)

            # Try to detect BPM
            bpm = self._detect_bpm(filepath)
            if bpm:
                analysis["bpm"] = bpm

            return analysis if analysis else None

        except subprocess.TimeoutExpired:
            return None
        except FileNotFoundError:
            # ffmpeg not installed
            return None

    def _get_gapless_info(self, filepath: str) -> Optional[dict]:
        """Extract gapless playback info using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                filepath,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            data = json.loads(result.stdout)
            info = {}

            # Get audio stream info
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "audio":
                    # Total samples
                    duration = float(stream.get("duration", 0))
                    sample_rate = int(stream.get("sample_rate", 44100))
                    info["total_samples"] = int(duration * sample_rate)

                    # Check for encoder delay in tags
                    tags = stream.get("tags", {})

                    # iTunes-style gapless info
                    if "iTunSMPB" in tags:
                        smpb = self._parse_itunes_smpb(tags["iTunSMPB"])
                        info.update(smpb)

                    # LAME encoder info
                    encoder = tags.get("encoder", "")
                    if "LAME" in encoder.upper():
                        # LAME typically has 576 sample delay
                        info["encoder_delay"] = info.get("encoder_delay", 576)

                    break

            return info if info else None

        except Exception:
            return None

    def _parse_itunes_smpb(self, smpb: str) -> dict:
        """Parse iTunes SMPB atom for gapless info."""
        try:
            # SMPB format: " 00000000 XXXXXXXX YYYYYYYY ..."
            # X = encoder delay, Y = encoder padding
            parts = smpb.strip().split()
            if len(parts) >= 3:
                encoder_delay = int(parts[1], 16)
                encoder_padding = int(parts[2], 16)
                return {
                    "encoder_delay": encoder_delay,
                    "encoder_padding": encoder_padding,
                }
        except Exception:
            pass
        return {}

    def _detect_bpm(self, filepath: str) -> Optional[float]:
        """
        Detect BPM using ffmpeg's beat detection.

        Note: This is a simple implementation. For more accurate BPM,
        consider using librosa or essentia libraries.
        """
        try:
            # Use ffmpeg's ebur128 for rough tempo estimation
            # This is basic - for production, use specialized BPM detection
            cmd = [
                "ffmpeg",
                "-i", filepath,
                "-af", "aresample=8000,ebur128=metadata=1",
                "-f", "null",
                "-t", "30",  # Analyze first 30 seconds
                "-"
            ]

            # BPM detection is complex - return None for now
            # A full implementation would use librosa or a dedicated library
            return None

        except Exception:
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

    def get_stats(self) -> dict:
        """Get audio analysis statistics."""
        from sqlalchemy import func

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
