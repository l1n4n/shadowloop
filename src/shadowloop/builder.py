"""
Assembles the final practice audio from segments and a plan.

Handles speed adjustment and combines audio clips with silence gaps.
"""

import os
import subprocess
import tempfile
from typing import List

from pydub import AudioSegment

from shadowloop.config import ShadowingConfig
from shadowloop.planner import PlayClip, Silence, PlanAction


def apply_speed(clip: AudioSegment, speed: float) -> AudioSegment:
    """
    Apply pitch-preserving speed change to an audio clip.

    Uses ffmpeg atempo filter for speed adjustment without pitch change.
    atempo accepts 0.5-2.0 range.

    Args:
        clip: AudioSegment to speed up or slow down
        speed: Speed multiplier (0.5-1.5 typical range)

    Returns:
        AudioSegment with speed applied, or original if speed == 1.0
    """
    if speed == 1.0:
        return clip

    # Create temporary files for ffmpeg processing
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.wav")
        output_path = os.path.join(tmpdir, "output.wav")

        # Export clip to temporary wav file
        clip.export(input_path, format="wav")

        # Run ffmpeg with atempo filter
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-filter:a", f"atempo={speed}",
            "-y", output_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)

        # Re-import the result
        result = AudioSegment.from_wav(output_path)

    return result


def build_audio(
    source_audio: AudioSegment,
    plan: List[PlanAction],
    config: ShadowingConfig
) -> AudioSegment:
    """
    Assemble final practice audio from source and plan actions.

    Iterates through plan actions:
    - PlayClip: extract segment, apply speed if needed, append to output
    - Silence: append silent audio segment

    Args:
        source_audio: Full source AudioSegment to extract clips from
        plan: List of PlayClip and Silence actions from planner
        config: ShadowingConfig with playback_speed setting

    Returns:
        Assembled AudioSegment ready for export
    """
    output = AudioSegment.empty()

    for action in plan:
        if isinstance(action, PlayClip):
            # Extract the segment from source audio
            segment = source_audio[action.start_ms:action.end_ms]

            # Apply speed adjustment if needed
            if config.playback_speed != 1.0:
                segment = apply_speed(segment, config.playback_speed)

            output += segment

        elif isinstance(action, Silence):
            # Append silence
            silence = AudioSegment.silent(duration=action.duration_ms)
            output += silence

    return output
