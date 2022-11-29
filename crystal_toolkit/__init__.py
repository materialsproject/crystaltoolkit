from __future__ import annotations

from pathlib import Path

from monty.json import MSONable
from pkg_resources import DistributionNotFound, get_distribution

from crystal_toolkit.msonable import (
    _ipython_display_,
    _repr_mimebundle_,
    show_json,
    to_plotly_json,
)
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

MSONable.to_plotly_json = to_plotly_json
MSONable._repr_mimebundle_ = _repr_mimebundle_
MSONable.show_json = show_json
MSONable._ipython_display_ = _ipython_display_

MODULE_PATH = Path(__file__).parents[0]

try:
    __version__ = get_distribution("crystal_toolkit").version
except DistributionNotFound:  # pragma: no cover
    # package is not installed
    pass
