from dataclasses import dataclass
from typing import List


@dataclass
class Segment:
    """One practice unit (sentence/phrase) from the source audio."""
    id: int
    text: str
    start_ms: int
    end_ms: int

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms


def segments_from_dicts(data: list) -> List[Segment]:
    """Reconstitute Segment objects from dicts (as returned by Gradio gr.State JSON serialization)."""
    if not data:
        return []
    result = []
    for item in data:
        if isinstance(item, Segment):
            result.append(item)
        elif isinstance(item, dict):
            result.append(Segment(
                id=item["id"],
                text=item["text"],
                start_ms=item["start_ms"],
                end_ms=item["end_ms"],
            ))
        else:
            raise ValueError(f"Cannot convert {type(item)} to Segment")
    return result


@dataclass
class ShadowingConfig:
    """User-configurable practice settings."""
    repeat_count: int = 8
    pause_between_repeats_ms: int = 2500
    pause_between_sentences_ms: int = 4000
    playback_speed: float = 1.0

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not 1 <= self.repeat_count <= 20:
            errors.append("Repeat count must be between 1 and 20.")
        if not 0 <= self.pause_between_repeats_ms <= 10000:
            errors.append("Pause between repeats must be 0-10000 ms.")
        if not 1000 <= self.pause_between_sentences_ms <= 15000:
            errors.append("Pause between sentences must be 1000-15000 ms.")
        if not 0.5 <= self.playback_speed <= 2.0:
            errors.append("Playback speed must be 0.5x-2.0x.")
        return errors
