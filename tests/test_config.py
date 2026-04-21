"""Tests for ShadowingConfig validation."""

import pytest
from shadowloop.config import ShadowingConfig, Segment, segments_from_dicts


class TestConfigValidation:
    """Test ShadowingConfig.validate() method."""

    def test_default_config_is_valid(self) -> None:
        """Default config should return empty error list."""
        config = ShadowingConfig()
        errors = config.validate()
        assert errors == []

    def test_repeat_count_zero_invalid(self) -> None:
        """Repeat count of 0 should be invalid."""
        config = ShadowingConfig(repeat_count=0)
        errors = config.validate()
        assert len(errors) > 0
        assert any("Repeat count" in e for e in errors)

    def test_repeat_count_twenty_one_invalid(self) -> None:
        """Repeat count of 21 should be invalid."""
        config = ShadowingConfig(repeat_count=21)
        errors = config.validate()
        assert len(errors) > 0
        assert any("Repeat count" in e for e in errors)

    def test_repeat_count_one_valid(self) -> None:
        """Repeat count of 1 should be valid."""
        config = ShadowingConfig(repeat_count=1)
        errors = config.validate()
        assert not any("Repeat count" in e for e in errors)

    def test_repeat_count_twenty_valid(self) -> None:
        """Repeat count of 20 should be valid."""
        config = ShadowingConfig(repeat_count=20)
        errors = config.validate()
        assert not any("Repeat count" in e for e in errors)

    def test_pause_between_repeats_negative_invalid(self) -> None:
        """Negative pause between repeats should be invalid."""
        config = ShadowingConfig(pause_between_repeats_ms=-1)
        errors = config.validate()
        assert len(errors) > 0
        assert any("Pause between repeats" in e for e in errors)

    def test_pause_between_repeats_over_max_invalid(self) -> None:
        """Pause between repeats over 10000 ms should be invalid."""
        config = ShadowingConfig(pause_between_repeats_ms=10001)
        errors = config.validate()
        assert len(errors) > 0
        assert any("Pause between repeats" in e for e in errors)

    def test_pause_between_repeats_zero_valid(self) -> None:
        """Pause between repeats of 0 should be valid."""
        config = ShadowingConfig(pause_between_repeats_ms=0)
        errors = config.validate()
        assert not any("Pause between repeats" in e for e in errors)

    def test_pause_between_repeats_max_valid(self) -> None:
        """Pause between repeats of 10000 should be valid."""
        config = ShadowingConfig(pause_between_repeats_ms=10000)
        errors = config.validate()
        assert not any("Pause between repeats" in e for e in errors)

    def test_pause_between_sentences_under_min_invalid(self) -> None:
        """Pause between sentences under 1000 ms should be invalid."""
        config = ShadowingConfig(pause_between_sentences_ms=999)
        errors = config.validate()
        assert len(errors) > 0
        assert any("Pause between sentences" in e for e in errors)

    def test_pause_between_sentences_over_max_invalid(self) -> None:
        """Pause between sentences over 15000 ms should be invalid."""
        config = ShadowingConfig(pause_between_sentences_ms=15001)
        errors = config.validate()
        assert len(errors) > 0
        assert any("Pause between sentences" in e for e in errors)

    def test_pause_between_sentences_min_valid(self) -> None:
        """Pause between sentences of 1000 should be valid."""
        config = ShadowingConfig(pause_between_sentences_ms=1000)
        errors = config.validate()
        assert not any("Pause between sentences" in e for e in errors)

    def test_pause_between_sentences_max_valid(self) -> None:
        """Pause between sentences of 15000 should be valid."""
        config = ShadowingConfig(pause_between_sentences_ms=15000)
        errors = config.validate()
        assert not any("Pause between sentences" in e for e in errors)

    def test_playback_speed_under_min_invalid(self) -> None:
        """Playback speed under 0.5x should be invalid."""
        config = ShadowingConfig(playback_speed=0.4)
        errors = config.validate()
        assert len(errors) > 0
        assert any("Playback speed" in e for e in errors)

    def test_playback_speed_over_max_invalid(self) -> None:
        """Playback speed over 2.0x should be invalid."""
        config = ShadowingConfig(playback_speed=2.1)
        errors = config.validate()
        assert len(errors) > 0
        assert any("Playback speed" in e for e in errors)

    def test_playback_speed_min_valid(self) -> None:
        """Playback speed of 0.5x should be valid."""
        config = ShadowingConfig(playback_speed=0.5)
        errors = config.validate()
        assert not any("Playback speed" in e for e in errors)

    def test_playback_speed_max_valid(self) -> None:
        """Playback speed of 2.0x should be valid."""
        config = ShadowingConfig(playback_speed=2.0)
        errors = config.validate()
        assert not any("Playback speed" in e for e in errors)

    def test_multiple_errors_reported(self) -> None:
        """Multiple validation errors should all be reported."""
        config = ShadowingConfig(
            repeat_count=0,
            pause_between_repeats_ms=20000,
            pause_between_sentences_ms=500,
            playback_speed=2.5,
        )
        errors = config.validate()
        assert len(errors) >= 4


class TestSegmentsFromDicts:
    def test_from_dicts(self) -> None:
        data = [{"id": 0, "text": "Hello", "start_ms": 0, "end_ms": 1000}]
        result = segments_from_dicts(data)
        assert len(result) == 1
        assert isinstance(result[0], Segment)
        assert result[0].text == "Hello"

    def test_passthrough_segments(self) -> None:
        seg = Segment(id=0, text="Hi", start_ms=0, end_ms=500)
        result = segments_from_dicts([seg])
        assert result[0] is seg

    def test_empty_list(self) -> None:
        assert segments_from_dicts([]) == []
        assert segments_from_dicts(None) == []
