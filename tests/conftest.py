"""Shared fixtures for ShadowLoop tests."""

import pytest
from typing import List

from shadowloop.config import Segment, ShadowingConfig


@pytest.fixture
def sample_segments() -> List[Segment]:
    """Three sample segments for testing."""
    return [
        Segment(id=0, text="Hello world.", start_ms=0, end_ms=1200),
        Segment(id=1, text="How are you?", start_ms=1500, end_ms=2800),
        Segment(id=2, text="I am fine.", start_ms=3100, end_ms=4500),
    ]


@pytest.fixture
def default_config() -> ShadowingConfig:
    """Default ShadowingConfig for testing."""
    return ShadowingConfig()
