"""Audio transcription and sentence segmentation."""

from types import SimpleNamespace
from typing import List, Optional, Tuple

from shadowloop.config import Segment


def transcribe(audio_path: str, model_size: str = "base") -> list:
    """
    Transcribe audio using openai-whisper with word-level timestamps.

    Returns list of segment objects with .words attribute,
    where each word has .word, .start, .end attributes.
    """
    import whisper

    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path, word_timestamps=True)

    segments = []
    for seg in result.get("segments", []):
        words = []
        for w in seg.get("words", []):
            words.append(SimpleNamespace(
                word=w["word"].strip(),
                start=w["start"],
                end=w["end"],
            ))
        segments.append(SimpleNamespace(
            text=seg["text"].strip(),
            start=seg["start"],
            end=seg["end"],
            words=words,
        ))
    return segments


def _split_into_sentences(raw_segments: list, audio_duration_ms: int) -> List[Segment]:
    """
    Split raw transcription segments into sentences based on punctuation and silence.

    Args:
        raw_segments: List of raw segment dicts from transcribe()
        audio_duration_ms: Total audio duration in milliseconds

    Returns:
        List of Segment objects with sequential IDs
    """
    # Flatten all words from all segments
    all_words = []
    for segment in raw_segments:
        if hasattr(segment, 'words'):
            all_words.extend(segment.words)

    if not all_words:
        return []

    # Group words into sentences
    sentence_groups = []
    current_group = [all_words[0]]

    for i in range(1, len(all_words)):
        prev_word = all_words[i - 1]
        curr_word = all_words[i]

        # Check for sentence-ending punctuation
        ends_sentence = prev_word.word.rstrip().endswith(('.', '!', '?'))

        # Check for silence gap >= 600ms
        silence_gap = (curr_word.start - prev_word.end) * 1000  # Convert to ms
        has_silence = silence_gap >= 600

        if ends_sentence or has_silence:
            sentence_groups.append(current_group)
            current_group = [curr_word]
        else:
            current_group.append(curr_word)

    if current_group:
        sentence_groups.append(current_group)

    # Convert word groups to segments
    segments = []
    for group in sentence_groups:
        text = ' '.join(w.word for w in group)
        start_ms = int(group[0].start * 1000)
        end_ms = int(group[-1].end * 1000)
        segments.append((text, start_ms, end_ms))

    # Merge segments shorter than 2000ms with neighbors
    merged = []
    i = 0
    while i < len(segments):
        text, start_ms, end_ms = segments[i]
        duration = end_ms - start_ms

        if duration < 2000 and i > 0:
            # Merge with previous
            prev_text, prev_start, prev_end = merged[-1]
            merged[-1] = (f"{prev_text} {text}", prev_start, end_ms)
        elif duration < 2000 and i < len(segments) - 1:
            # Merge with next
            next_text, next_start, next_end = segments[i + 1]
            merged.append((f"{text} {next_text}", start_ms, next_end))
            i += 1
        else:
            merged.append((text, start_ms, end_ms))

        i += 1

    # Apply padding and clamp boundaries
    result = []
    for idx, (text, start_ms, end_ms) in enumerate(merged):
        start_ms = max(0, start_ms - 50)
        end_ms = min(audio_duration_ms, end_ms + 50)
        result.append(Segment(id=idx, text=text, start_ms=start_ms, end_ms=end_ms))

    return result


def segment_audio(audio_path: str, audio_duration_ms: int, model_size: str = "base") -> List[Segment]:
    """
    Main entry point: transcribe audio and split into sentences.

    Args:
        audio_path: Path to audio file
        audio_duration_ms: Total audio duration in milliseconds
        model_size: Whisper model size

    Returns:
        List of Segment objects
    """
    raw_segments = transcribe(audio_path, model_size)
    return _split_into_sentences(raw_segments, audio_duration_ms)


def merge_segments(segments: List[Segment], id_a: int, id_b: int) -> List[Segment]:
    """
    Merge two adjacent segments.

    Args:
        segments: List of segments
        id_a: ID of first segment
        id_b: ID of second segment (must be id_a + 1)

    Returns:
        New list with merged segment and re-sequenced IDs

    Raises:
        ValueError: If segments are not adjacent
    """
    if id_b != id_a + 1:
        raise ValueError(f"Segments {id_a} and {id_b} are not adjacent")

    seg_a = next((s for s in segments if s.id == id_a), None)
    seg_b = next((s for s in segments if s.id == id_b), None)

    if not seg_a or not seg_b:
        raise ValueError(f"Segment {id_a} or {id_b} not found")

    # Create merged segment text
    merged_text = f"{seg_a.text} {seg_b.text}"

    # Build result with re-sequenced IDs
    result = []
    new_id = 0
    for seg in segments:
        if seg.id == id_a:
            result.append(Segment(id=new_id, text=merged_text, start_ms=seg_a.start_ms, end_ms=seg_b.end_ms))
            new_id += 1
        elif seg.id == id_b:
            continue
        else:
            result.append(Segment(id=new_id, text=seg.text, start_ms=seg.start_ms, end_ms=seg.end_ms))
            new_id += 1

    return result


def split_segment(segments: List[Segment], segment_id: int, split_offset_ms: int) -> List[Segment]:
    """
    Split a segment at a given offset.

    Args:
        segments: List of segments
        segment_id: ID of segment to split
        split_offset_ms: Offset from segment start (in ms)

    Returns:
        New list with split segment and re-sequenced IDs
    """
    seg = next((s for s in segments if s.id == segment_id), None)
    if not seg:
        raise ValueError(f"Segment {segment_id} not found")

    # Calculate split position
    duration_ms = seg.duration_ms
    split_ratio = split_offset_ms / duration_ms if duration_ms > 0 else 0
    char_pos = int(len(seg.text) * split_ratio)

    # Find nearest space for clean word break
    left_space = seg.text.rfind(' ', 0, char_pos)
    right_space = seg.text.find(' ', char_pos)

    if left_space == -1 and right_space == -1:
        # No spaces, split at char_pos
        split_pos = char_pos
    elif left_space == -1:
        split_pos = right_space
    elif right_space == -1:
        split_pos = left_space
    else:
        # Choose closer space
        split_pos = left_space if (char_pos - left_space) <= (right_space - char_pos) else right_space

    split_pos = max(0, min(split_pos, len(seg.text)))

    # Split text and calculate time boundary
    text_a = seg.text[:split_pos].strip()
    text_b = seg.text[split_pos:].strip()

    split_ms = seg.start_ms + split_offset_ms

    # Build result with re-sequenced IDs
    result = []
    new_id = 0
    for s in segments:
        if s.id == segment_id:
            result.append(Segment(id=new_id, text=text_a, start_ms=s.start_ms, end_ms=split_ms))
            new_id += 1
            result.append(Segment(id=new_id, text=text_b, start_ms=split_ms, end_ms=s.end_ms))
            new_id += 1
        else:
            result.append(Segment(id=new_id, text=s.text, start_ms=s.start_ms, end_ms=s.end_ms))
            new_id += 1

    return result


def delete_segment(segments: List[Segment], segment_id: int) -> List[Segment]:
    """
    Delete a segment and re-sequence IDs.

    Args:
        segments: List of segments
        segment_id: ID of segment to delete

    Returns:
        New list without the segment and with re-sequenced IDs
    """
    result = []
    new_id = 0
    for seg in segments:
        if seg.id != segment_id:
            result.append(Segment(id=new_id, text=seg.text, start_ms=seg.start_ms, end_ms=seg.end_ms))
            new_id += 1

    return result


def segments_from_transcript(transcript_text: str, audio_duration_ms: int) -> List[Segment]:
    """
    Create segments from user-provided transcript text.

    Each line becomes a segment. Timestamps are distributed evenly across the audio duration.
    Empty lines are skipped.
    """
    lines = [line.strip() for line in transcript_text.strip().split('\n') if line.strip()]
    if not lines:
        return []

    segment_duration = audio_duration_ms // len(lines)
    segments = []
    for i, line in enumerate(lines):
        start_ms = i * segment_duration
        end_ms = start_ms + segment_duration if i < len(lines) - 1 else audio_duration_ms
        segments.append(Segment(id=i, text=line, start_ms=start_ms, end_ms=end_ms))
    return segments
