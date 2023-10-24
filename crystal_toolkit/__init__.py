from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from monty.json import MSONable

import crystal_toolkit.helpers.layouts as ctl
from crystal_toolkit.core.jupyter import patch_msonable
from crystal_toolkit.core.plugin import CrystalToolkitPlugin
from crystal_toolkit.renderables import (
    Lattice,
    Molecule,
    MoleculeGraph,
    PhaseDiagram,
    Site,
    Structure,
    StructureGraph,
    VolumetricData,
)

patch_msonable()

MODULE_PATH = Path(__file__).parents[0]

try:
    __version__ = version("crystal_toolkit")
except PackageNotFoundError:  # pragma: no cover
    # package is not installed
    pass
