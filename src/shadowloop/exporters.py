"""
Exports assembled audio to file formats.

Simple exporters for common output formats.
"""

from pydub import AudioSegment


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
