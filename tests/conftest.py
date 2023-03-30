# conftest file for pytest
from __future__ import annotations

from pathlib import Path

import pytest

from crystal_toolkit.core.scene import Cylinders, Lines, Spheres, Surface


@pytest.fixture(scope="session")
def test_files():
    """The path to the test_files directory."""
    return Path(__file__).parent / "test_files"


@pytest.fixture(scope="session")
def standard_scenes():
    """Dictionary of standard scenes for testing purposes."""
    return {
        "spheres": Spheres(
            positions=[[0, 0, 0], [1, 1, 1]],
            color=None,
            radius=0.3,
        ),
        "cylinders": Cylinders(
            positionPairs=[[[0, 0, 0], [1, 1, 1]]], radius=0.3, color=None
        ),
        "lines": Lines(
            positions=[[0, 0, 0], [1, 1, 1]],
            color=None,
        ),
        "surface": Surface(
            positions=[[0, 0, 0], [1, 1, 1], [2, 2, 2]],
            color=None,
        ),
    }
