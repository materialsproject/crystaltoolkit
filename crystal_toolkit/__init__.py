from __future__ import annotations
from pkg_resources import DistributionNotFound, get_distribution
from pathlib import Path

MODULE_PATH = Path(__file__).parents[0]

try:
    __version__ = get_distribution("crystal_toolkit").version
except DistributionNotFound:  # pragma: no cover
    # package is not installed
    pass
