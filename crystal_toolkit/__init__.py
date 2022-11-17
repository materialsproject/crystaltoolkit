from __future__ import annotations

from pathlib import Path

from pkg_resources import DistributionNotFound, get_distribution

MODULE_PATH = Path(__file__).parents[0]

try:
    __version__ = get_distribution("crystal_toolkit").version
except DistributionNotFound:  # pragma: no cover
    # package is not installed
    pass
