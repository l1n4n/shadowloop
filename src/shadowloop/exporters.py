"""
Exports assembled audio to file formats.

Simple exporters for common output formats.
"""

from typing import TYPE_CHECKING

from pydub import AudioSegment

if TYPE_CHECKING:
    from shadowloop.config import Segment


def export_mp3(audio: AudioSegment, output_path: str, bitrate: str = "192k") -> str:
    """
    Export audio to MP3 format.

    Args:
        audio: AudioSegment to export
        output_path: Path where MP3 file will be saved
        bitrate: MP3 bitrate (default "192k")

    Returns:
        The output_path (for chaining or confirmation)
    """
    audio.export(output_path, format="mp3", bitrate=bitrate)
    return output_path


def export_transcript(segments: list["Segment"], output_path: str) -> str:
    """Export segments to a timestamped .txt transcript file."""
    with open(output_path, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(f"[{seg.start_ms / 1000:.1f}s - {seg.end_ms / 1000:.1f}s] {seg.text}\n")
    return output_path
