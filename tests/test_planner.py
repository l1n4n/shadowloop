"""Tests for planner module."""

import pytest
from typing import List

from shadowloop.config import Segment, ShadowingConfig
from shadowloop.planner import PlayClip, Silence, PlanAction, build_plan, estimate_duration_ms


class TestBuildPlan:
    """Test build_plan function."""

    def test_single_segment_single_repeat(self, sample_segments: List[Segment]) -> None:
        """Single segment with repeat_count=1 should produce only PlayClip."""
        config = ShadowingConfig(repeat_count=1)
        segments = [sample_segments[0]]
        plan = build_plan(segments, config)

        assert len(plan) == 1
        assert isinstance(plan[0], PlayClip)
        assert plan[0].segment_id == 0
        assert plan[0].start_ms == 0
        assert plan[0].end_ms == 1200

    def test_single_segment_three_repeats(self, sample_segments: List[Segment]) -> None:
        """Single segment with repeat_count=3 should produce PlayClip, Silence, PlayClip, Silence, PlayClip."""
        config = ShadowingConfig(repeat_count=3, pause_between_repeats_ms=500)
        segments = [sample_segments[0]]
        plan = build_plan(segments, config)

        assert len(plan) == 5
        assert isinstance(plan[0], PlayClip)
        assert isinstance(plan[1], Silence)
        assert isinstance(plan[2], PlayClip)
        assert isinstance(plan[3], Silence)
        assert isinstance(plan[4], PlayClip)
        assert plan[1].duration_ms == 500
        assert plan[3].duration_ms == 500

    def test_two_segments_two_repeats(self, sample_segments: List[Segment]) -> None:
        """Two segments with repeat_count=2 should have sentence pause between segments."""
        config = ShadowingConfig(
            repeat_count=2,
            pause_between_repeats_ms=500,
            pause_between_sentences_ms=1000,
        )
        segments = [sample_segments[0], sample_segments[1]]
        plan = build_plan(segments, config)

        # Expected: PlayClip(seg0), Silence(500), PlayClip(seg0), Silence(1000), PlayClip(seg1), Silence(500), PlayClip(seg1)
        assert len(plan) == 7
        assert isinstance(plan[0], PlayClip)
        assert plan[0].segment_id == 0
        assert isinstance(plan[1], Silence)
        assert plan[1].duration_ms == 500
        assert isinstance(plan[2], PlayClip)
        assert plan[2].segment_id == 0
        assert isinstance(plan[3], Silence)
        assert plan[3].duration_ms == 1000
        assert isinstance(plan[4], PlayClip)
        assert plan[4].segment_id == 1
        assert isinstance(plan[5], Silence)
        assert plan[5].duration_ms == 500
        assert isinstance(plan[6], PlayClip)
        assert plan[6].segment_id == 1

    def test_no_trailing_silence(self, sample_segments: List[Segment]) -> None:
        """Last action in plan should be PlayClip, not Silence."""
        config = ShadowingConfig(repeat_count=2, pause_between_repeats_ms=500)
        segments = sample_segments
        plan = build_plan(segments, config)

        assert len(plan) > 0
        assert isinstance(plan[-1], PlayClip)

    def test_no_leading_silence(self, sample_segments: List[Segment]) -> None:
        """First action in plan should be PlayClip, not Silence."""
        config = ShadowingConfig(repeat_count=2)
        segments = sample_segments
        plan = build_plan(segments, config)

        assert len(plan) > 0
        assert isinstance(plan[0], PlayClip)

    def test_three_segments_one_repeat(self, sample_segments: List[Segment]) -> None:
        """Three segments with repeat_count=1 should have pauses between segments only."""
        config = ShadowingConfig(repeat_count=1, pause_between_sentences_ms=2000)
        segments = sample_segments
        plan = build_plan(segments, config)

        # Expected: PlayClip(0), Silence(2000), PlayClip(1), Silence(2000), PlayClip(2)
        assert len(plan) == 5
        assert isinstance(plan[0], PlayClip)
        assert isinstance(plan[1], Silence)
        assert plan[1].duration_ms == 2000
        assert isinstance(plan[2], PlayClip)
        assert isinstance(plan[3], Silence)
        assert plan[3].duration_ms == 2000
        assert isinstance(plan[4], PlayClip)


class TestEstimateDuration:
    """Test estimate_duration_ms function."""

    def test_estimate_duration_speed_1(self, sample_segments: List[Segment]) -> None:
        """Duration at speed 1.0 should be sum of clip and silence durations."""
        config = ShadowingConfig(
            repeat_count=2,
            pause_between_repeats_ms=500,
            pause_between_sentences_ms=1000,
        )
        segments = [sample_segments[0], sample_segments[1]]
        plan = build_plan(segments, config)

        # Segment 0: 1200 ms, Segment 1: 1300 ms
        # Plan: PlayClip(1200) + Silence(500) + PlayClip(1200) + Silence(1000) + PlayClip(1300) + Silence(500) + PlayClip(1300)
        # Total: 1200 + 500 + 1200 + 1000 + 1300 + 500 + 1300 = 7000
        duration = estimate_duration_ms(plan, speed=1.0)
        assert duration == 7000

    def test_estimate_duration_speed_half(self, sample_segments: List[Segment]) -> None:
        """Duration at speed 0.5 should double clip portions, silence unchanged."""
        config = ShadowingConfig(
            repeat_count=1,
            pause_between_repeats_ms=0,
            pause_between_sentences_ms=1000,
        )
        segments = [sample_segments[0]]
        plan = build_plan(segments, config)

        # At speed 1.0: 1200 ms
        # At speed 0.5: 1200 / 0.5 = 2400 ms
        duration_1x = estimate_duration_ms(plan, speed=1.0)
        duration_half = estimate_duration_ms(plan, speed=0.5)

        assert duration_1x == 1200
        assert duration_half == 2400

    def test_estimate_duration_speed_double(self, sample_segments: List[Segment]) -> None:
        """Duration at speed 2.0 should halve clip portions."""
        config = ShadowingConfig(repeat_count=1)
        segments = [sample_segments[0]]
        plan = build_plan(segments, config)

        # At speed 1.0: 1200 ms
        # At speed 2.0: 1200 / 2.0 = 600 ms
        duration_1x = estimate_duration_ms(plan, speed=1.0)
        duration_2x = estimate_duration_ms(plan, speed=2.0)

        assert duration_1x == 1200
        assert duration_2x == 600

    def test_estimate_duration_with_silence_only(self) -> None:
        """Plan with only silence should return silence duration."""
        plan: List[PlanAction] = [Silence(1000), Silence(500)]
        duration = estimate_duration_ms(plan, speed=1.0)
        assert duration == 1500

    def test_estimate_duration_empty_plan(self) -> None:
        """Empty plan should return 0."""
        plan: List[PlanAction] = []
        duration = estimate_duration_ms(plan, speed=1.0)
        assert duration == 0

    def test_estimate_duration_complex_plan(self, sample_segments: List[Segment]) -> None:
        """Complex plan with multiple segments and repeats."""
        config = ShadowingConfig(
            repeat_count=3,
            pause_between_repeats_ms=800,
            pause_between_sentences_ms=2000,
        )
        segments = sample_segments
        plan = build_plan(segments, config)

        # Manually calculate expected duration at speed 1.0
        # Segment 0: 1200 ms, Segment 1: 1300 ms, Segment 2: 1400 ms
        # For each segment: 3 repeats with 2 pauses between = 3*duration + 2*800
        # Between segments: 2000 ms pause
        # Total: (1200*3 + 2*800) + 2000 + (1300*3 + 2*800) + 2000 + (1400*3 + 2*800)
        # = (3600 + 1600) + 2000 + (3900 + 1600) + 2000 + (4200 + 1600)
        # = 5200 + 2000 + 5500 + 2000 + 5800 = 20500
        duration = estimate_duration_ms(plan, speed=1.0)
        assert duration == 20500
