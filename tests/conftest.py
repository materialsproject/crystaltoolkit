# conftest file for pytest
from pathlib import Path
from crystal_toolkit.core.scene import Spheres, Lines, Cylinders, Surface
import pytest

@pytest.fixture(scope="session")
def test_files():
    return Path(__file__).parent / "test_files"


@pytest.fixture(scope="session")
def standard_scenes():
    return {
        "spheres": Spheres(
            positions=[[0, 0, 0], [1, 1, 1]],
            color=None,
            radius=0.3,
        ),
        "cylinders": Cylinders(
            positionPairs=[[[0, 0, 0], [1, 1, 1]]], 
            radius=0.3, 
            color=None),
        "lines": Lines(
            positions=[[0, 0, 0], [1, 1, 1]],
            color=None,
        ),
        "surface": Surface(
            positions=[[0, 0, 0], [1, 1, 1], [2, 2, 2]],
            color=None,
        )
    }