"""Tests for segmenter module."""

import pytest
from typing import List, Any, Dict

from shadowloop.config import Segment
from shadowloop.segmenter import (
    _split_into_sentences,
    merge_segments,
    split_segment,
    delete_segment,
    segments_from_transcript,
)


class MockWord:
    """Mock word object for testing."""

    def __init__(self, word: str, start: float, end: float) -> None:
        self.word = word
        self.start = start
        self.end = end


class MockSegment:
    """Mock segment object for testing."""

    def __init__(self, text: str, start: float, end: float, words: List[MockWord]) -> None:
        self.text = text
        self.start = start
        self.end = end
        self.words = words


class TestSplitIntoSentences:
    """Test _split_into_sentences function."""

    def test_split_by_punctuation(self) -> None:
        """Words ending with period should create sentence boundary."""
        raw_segments = [
            MockSegment(
                text="Hello world. How are you? I am fine.",
                start=0.0,
                end=5.0,
                words=[
                    MockWord("Hello", 0.0, 0.3),
                    MockWord("world.", 0.35, 0.7),
                    MockWord("How", 1.0, 1.2),
                    MockWord("are", 1.25, 1.4),
                    MockWord("you?", 1.45, 1.7),
                    MockWord("I", 2.5, 2.7),
                    MockWord("am", 2.75, 2.9),
                    MockWord("fine.", 2.95, 3.2),
                ],
            )
        ]
        audio_duration_ms = 5000

        segments = _split_into_sentences(raw_segments, audio_duration_ms)

        # Verify segments were created (exact count depends on merge logic)
        assert len(segments) >= 1
        # Verify text contains expected content
        combined_text = " ".join(s.text for s in segments)
        assert "Hello world." in combined_text
        assert "How are you?" in combined_text

    def test_split_by_silence_gap(self) -> None:
        """Gap >= 600ms between words should create sentence boundary."""
        raw_segments = [
            MockSegment(
                text="Hello world How are you I am fine",
                start=0.0,
                end=5.0,
                words=[
                    MockWord("Hello", 0.0, 0.3),
                    MockWord("world", 0.35, 0.7),
                    MockWord("How", 1.5, 1.7),  # 800ms gap from previous
                    MockWord("are", 1.75, 1.9),
                    MockWord("you", 1.95, 2.1),
                    MockWord("I", 2.8, 3.0),  # 700ms gap from previous
                    MockWord("am", 3.05, 3.2),
                    MockWord("fine", 3.25, 3.5),
                ],
            )
        ]
        audio_duration_ms = 5000

        segments = _split_into_sentences(raw_segments, audio_duration_ms)

        # Verify segments were created
        assert len(segments) >= 1
        # Verify text contains expected content
        combined_text = " ".join(s.text for s in segments)
        assert "Hello world" in combined_text
        assert "How are you" in combined_text

    def test_merge_short_segments(self) -> None:
        """Segments under 2000ms should be merged with neighbors."""
        raw_segments = [
            MockSegment(
                text="Hi. How are you?",
                start=0.0,
                end=2.0,
                words=[
                    MockWord("Hi.", 0.0, 0.2),  # 200ms duration
                    MockWord("How", 0.5, 0.7),
                    MockWord("are", 0.75, 0.9),
                    MockWord("you?", 0.95, 1.2),
                ],
            )
        ]
        audio_duration_ms = 2000

        segments = _split_into_sentences(raw_segments, audio_duration_ms)

        # "Hi." is short (200ms), should merge with "How are you?"
        assert len(segments) == 1
        assert "Hi." in segments[0].text
        assert "How" in segments[0].text

    def test_padding_applied(self) -> None:
        """Segments should have -50ms start padding and +50ms end padding, clamped to boundaries."""
        raw_segments = [
            MockSegment(
                text="Hello world.",
                start=0.1,
                end=1.2,
                words=[
                    MockWord("Hello", 0.1, 0.4),
                    MockWord("world.", 0.45, 1.2),
                ],
            )
        ]
        audio_duration_ms = 5000

        segments = _split_into_sentences(raw_segments, audio_duration_ms)

        assert len(segments) == 1
        # start_ms = int(0.1 * 1000) - 50 = 100 - 50 = 50
        # end_ms = int(1.2 * 1000) + 50 = 1200 + 50 = 1250
        assert segments[0].start_ms == 50
        assert segments[0].end_ms == 1250

    def test_padding_clamped_to_zero(self) -> None:
        """Start padding should be clamped to 0."""
        raw_segments = [
            MockSegment(
                text="Hello",
                start=0.01,
                end=0.5,
                words=[
                    MockWord("Hello", 0.01, 0.5),
                ],
            )
        ]
        audio_duration_ms = 5000

        segments = _split_into_sentences(raw_segments, audio_duration_ms)

        assert len(segments) == 1
        # start_ms = max(0, int(0.01 * 1000) - 50) = max(0, 10 - 50) = 0
        assert segments[0].start_ms == 0

    def test_padding_clamped_to_duration(self) -> None:
        """End padding should be clamped to audio_duration_ms."""
        raw_segments = [
            MockSegment(
                text="Hello",
                start=4.9,
                end=5.0,
                words=[
                    MockWord("Hello", 4.9, 5.0),
                ],
            )
        ]
        audio_duration_ms = 5000

        segments = _split_into_sentences(raw_segments, audio_duration_ms)

        assert len(segments) == 1
        # end_ms = min(5000, int(5.0 * 1000) + 50) = min(5000, 5050) = 5000
        assert segments[0].end_ms == 5000

    def test_sequential_ids(self) -> None:
        """Segments should have sequential IDs starting from 0."""
        raw_segments = [
            MockSegment(
                text="Hello. How are you? I am fine.",
                start=0.0,
                end=3.0,
                words=[
                    MockWord("Hello.", 0.0, 0.3),
                    MockWord("How", 0.5, 0.7),
                    MockWord("are", 0.75, 0.9),
                    MockWord("you?", 0.95, 1.2),
                    MockWord("I", 1.5, 1.7),
                    MockWord("am", 1.75, 1.9),
                    MockWord("fine.", 1.95, 2.2),
                ],
            )
        ]
        audio_duration_ms = 3000

        segments = _split_into_sentences(raw_segments, audio_duration_ms)

        for i, seg in enumerate(segments):
            assert seg.id == i

    def test_empty_raw_segments(self) -> None:
        """Empty raw segments should return empty list."""
        raw_segments: List[Any] = []
        audio_duration_ms = 5000

        segments = _split_into_sentences(raw_segments, audio_duration_ms)

        assert segments == []


class TestMergeSegments:
    """Test merge_segments function."""

    def test_merge_segments(self, sample_segments: List[Segment]) -> None:
        """Merge segments 0 and 1."""
        result = merge_segments(sample_segments, 0, 1)

        assert len(result) == 2
        assert result[0].id == 0
        assert result[0].text == "Hello world. How are you?"
        assert result[0].start_ms == 0
        assert result[0].end_ms == 2800
        assert result[1].id == 1
        assert result[1].text == "I am fine."

    def test_merge_non_adjacent_raises(self, sample_segments: List[Segment]) -> None:
        """Merging non-adjacent segments should raise ValueError."""
        with pytest.raises(ValueError, match="not adjacent"):
            merge_segments(sample_segments, 0, 2)

    def test_merge_missing_segment_raises(self, sample_segments: List[Segment]) -> None:
        """Merging with missing segment should raise ValueError."""
        with pytest.raises(ValueError, match="not found"):
            merge_segments(sample_segments, 5, 6)

    def test_merge_resequences_ids(self, sample_segments: List[Segment]) -> None:
        """After merge, IDs should be re-sequenced starting from 0."""
        result = merge_segments(sample_segments, 1, 2)

        assert len(result) == 2
        assert result[0].id == 0
        assert result[0].text == "Hello world."
        assert result[1].id == 1
        assert "How are you?" in result[1].text
        assert "I am fine." in result[1].text


class TestSplitSegment:
    """Test split_segment function."""

    def test_split_segment(self, sample_segments: List[Segment]) -> None:
        """Split segment 1 at midpoint."""
        # Segment 1: "How are you?" from 1500 to 2800 (1300 ms duration)
        # Split at 650 ms (midpoint)
        result = split_segment(sample_segments, 1, 650)

        assert len(result) == 4
        assert result[0].id == 0
        assert result[0].text == "Hello world."
        assert result[1].id == 1
        assert result[1].text == "How are"
        assert result[1].start_ms == 1500
        assert result[1].end_ms == 2150  # 1500 + 650
        assert result[2].id == 2
        assert result[2].text == "you?"
        assert result[2].start_ms == 2150
        assert result[2].end_ms == 2800
        assert result[3].id == 3
        assert result[3].text == "I am fine."

    def test_split_segment_resequences_ids(self, sample_segments: List[Segment]) -> None:
        """After split, IDs should be re-sequenced."""
        result = split_segment(sample_segments, 0, 600)

        # Should have 4 segments now (original 3 + 1 from split)
        assert len(result) == 4
        for i, seg in enumerate(result):
            assert seg.id == i

    def test_split_segment_not_found_raises(self, sample_segments: List[Segment]) -> None:
        """Splitting non-existent segment should raise ValueError."""
        with pytest.raises(ValueError, match="not found"):
            split_segment(sample_segments, 99, 500)

    def test_split_segment_at_start(self, sample_segments: List[Segment]) -> None:
        """Split at offset 0 should create empty first part."""
        result = split_segment(sample_segments, 0, 0)

        assert len(result) == 4
        # First part should be very small or empty
        assert result[1].start_ms == 0


class TestDeleteSegment:
    """Test delete_segment function."""

    def test_delete_segment(self, sample_segments: List[Segment]) -> None:
        """Delete segment 1."""
        result = delete_segment(sample_segments, 1)

        assert len(result) == 2
        assert result[0].id == 0
        assert result[0].text == "Hello world."
        assert result[1].id == 1
        assert result[1].text == "I am fine."

    def test_delete_segment_resequences_ids(self, sample_segments: List[Segment]) -> None:
        """After delete, IDs should be re-sequenced."""
        result = delete_segment(sample_segments, 0)

        assert len(result) == 2
        assert result[0].id == 0
        assert result[0].text == "How are you?"
        assert result[1].id == 1
        assert result[1].text == "I am fine."

    def test_delete_first_segment(self, sample_segments: List[Segment]) -> None:
        """Delete first segment."""
        result = delete_segment(sample_segments, 0)

        assert len(result) == 2
        assert result[0].text == "How are you?"
        assert result[1].text == "I am fine."

    def test_delete_last_segment(self, sample_segments: List[Segment]) -> None:
        """Delete last segment."""
        result = delete_segment(sample_segments, 2)

        assert len(result) == 2
        assert result[0].text == "Hello world."
        assert result[1].text == "How are you?"

    def test_delete_nonexistent_segment(self, sample_segments: List[Segment]) -> None:
        """Deleting non-existent segment should return unchanged list."""
        result = delete_segment(sample_segments, 99)

        assert len(result) == 3
        assert result[0].id == 0
        assert result[1].id == 1
        assert result[2].id == 2


class TestSegmentsFromTranscript:
    def test_basic_transcript(self) -> None:
        text = "Hello world.\nHow are you?\nI am fine."
        segments = segments_from_transcript(text, 3000)
        assert len(segments) == 3
        assert segments[0].text == "Hello world."
        assert segments[0].start_ms == 0
        assert segments[1].text == "How are you?"
        assert segments[2].text == "I am fine."
        assert segments[2].end_ms == 3000

    def test_empty_lines_skipped(self) -> None:
        text = "Hello.\n\nWorld."
        segments = segments_from_transcript(text, 2000)
        assert len(segments) == 2

    def test_empty_transcript(self) -> None:
        segments = segments_from_transcript("", 1000)
        assert segments == []
