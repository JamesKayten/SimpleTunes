"""Audio analysis helper functions for ReplayGain and gapless detection."""

import subprocess
import json
from typing import Optional


class AudioAnalyzer:
    """Helper class for analyzing audio files using ffmpeg/ffprobe."""

    # Target loudness for ReplayGain (EBU R128 standard)
    TARGET_LOUDNESS = -18.0  # LUFS

    @staticmethod
    def analyze_with_ffmpeg(filepath: str) -> Optional[dict]:
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
                            analysis["track_gain"] = AudioAnalyzer.TARGET_LOUDNESS - integrated_loudness
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
            gapless_info = AudioAnalyzer.get_gapless_info(filepath)
            if gapless_info:
                analysis.update(gapless_info)

            # Try to detect BPM
            bpm = AudioAnalyzer.detect_bpm(filepath)
            if bpm:
                analysis["bpm"] = bpm

            return analysis if analysis else None

        except subprocess.TimeoutExpired:
            return None
        except FileNotFoundError:
            # ffmpeg not installed
            return None

    @staticmethod
    def get_gapless_info(filepath: str) -> Optional[dict]:
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
                        smpb = AudioAnalyzer.parse_itunes_smpb(tags["iTunSMPB"])
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

    @staticmethod
    def parse_itunes_smpb(smpb: str) -> dict:
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

    @staticmethod
    def detect_bpm(filepath: str) -> Optional[float]:
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
