import shutil
import tempfile
from typing import Optional

from pydub import AudioSegment


SUPPORTED_FORMATS = {"mp3", "wav", "m4a", "aac", "ogg", "flac"}


def check_ffmpeg() -> None:
    """Check if ffmpeg is installed and available.

    Raises:
        RuntimeError: If ffmpeg is not found.
    """
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg is required but not found. Install it: https://ffmpeg.org/download.html"
        )


def load_audio(file_path: str) -> AudioSegment:
    """Load audio file from disk.

    Args:
        file_path: Path to the audio file.

    Returns:
        AudioSegment object.

    Raises:
        ValueError: If file extension is not supported.
    """
    ext = file_path.rsplit(".", 1)[-1].lower()
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported audio format: {ext}. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    return AudioSegment.from_file(file_path)


def prepare_for_transcription(audio: AudioSegment) -> AudioSegment:
    """Convert audio to mono 16kHz WAV format suitable for Whisper.

    Args:
        audio: AudioSegment to prepare.

    Returns:
        Converted AudioSegment.
    """
    return audio.set_channels(1).set_frame_rate(16000)


def export_temp_wav(audio: AudioSegment) -> str:
    """Export audio to a temporary WAV file.

    Args:
        audio: AudioSegment to export.

    Returns:
        Path to the temporary WAV file. Caller is responsible for cleanup.
    """
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_path = temp_file.name
    temp_file.close()

    audio.export(temp_path, format="wav")
    return temp_path
