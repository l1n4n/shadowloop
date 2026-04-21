"""
Converts segments and config into an ordered list of plan actions.

Defines the repetition and pause pattern for shadowing practice.
"""

from dataclasses import dataclass
from typing import List, Union

from shadowloop.config import Segment, ShadowingConfig


@dataclass
class PlayClip:
    """Instruction to play a segment of audio."""
    segment_id: int
    start_ms: int
    end_ms: int


@dataclass
class Silence:
    """Instruction to insert silence."""
    duration_ms: int


PlanAction = Union[PlayClip, Silence]


def build_plan(segments: List[Segment], config: ShadowingConfig) -> List[PlanAction]:
    """
    Convert segments and config into an ordered list of plan actions.

    For each segment:
    - Insert pause before segment (except first)
    - Repeat segment N times with pauses between repeats
    - No trailing silence after last repetition

    Args:
        segments: List of audio segments to practice
        config: Shadowing configuration with repeat count and pause durations

    Returns:
        Ordered list of PlayClip and Silence actions
    """
    plan: List[PlanAction] = []

    for i, segment in enumerate(segments):
        # Add pause before segment (except first)
        if i > 0:
            plan.append(Silence(config.pause_between_sentences_ms))

        # Add repetitions with pauses between them
        for rep in range(config.repeat_count):
            plan.append(PlayClip(segment.id, segment.start_ms, segment.end_ms))

            # Add pause between repeats (except after last repetition)
            if rep < config.repeat_count - 1:
                plan.append(Silence(config.pause_between_repeats_ms))

    return plan


def estimate_duration_ms(plan: List[PlanAction], speed: float = 1.0) -> int:
    """
    Estimate total duration of a plan in milliseconds.

    PlayClip duration is adjusted by playback speed.
    Silence duration is used as-is.

    Args:
        plan: List of plan actions
        speed: Playback speed multiplier (default 1.0)

    Returns:
        Total estimated duration in milliseconds
    """
    total_ms = 0

    for action in plan:
        if isinstance(action, PlayClip):
            clip_duration = action.end_ms - action.start_ms
            total_ms += int(clip_duration / speed)
        elif isinstance(action, Silence):
            total_ms += action.duration_ms

    return total_ms
