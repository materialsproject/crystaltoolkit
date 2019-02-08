from __future__ import print_function as _

import os as _os
import sys as _sys
import json

import dash as _dash

# noinspection PyUnresolvedReferences
from ._imports_ import *
from ._imports_ import __all__

if not hasattr(_dash, 'development'):
    print('Dash was not successfully imported. '
          'Make sure you don\'t have a file '
          'named \n"dash.py" in your current directory.', file=_sys.stderr)
    _sys.exit(1)

_basepath = _os.path.dirname(__file__)
_filepath = _os.path.abspath(_os.path.join(_basepath, 'package.json'))
with open(_filepath) as f:
    package = json.load(f)

package_name = package['name'].replace(' ', '_').replace('-', '_')
__version__ = package['version']

_current_path = _os.path.dirname(_os.path.abspath(__file__))

_this_module = _sys.modules[__name__]


_js_dist = [
    {
        'relative_package_path': 'crystal_toolkit.min.js',
        'dev_package_path': 'crystal_toolkit.dev.js',
        
        'namespace': package_name
    }
]

_css_dist = []


for _component in __all__:
    setattr(locals()[_component], '_js_dist', _js_dist)
    setattr(locals()[_component], '_css_dist', _css_dist)

# convenience imports
from crystal_toolkit.components.core import MPComponent, PanelComponent
register_app = MPComponent.register_app
register_cache = MPComponent.register_cache

from crystal_toolkit.components.json import JSONEditor
from crystal_toolkit.components.search import SearchComponent
from crystal_toolkit.components.structure import StructureMoleculeComponent
from crystal_toolkit.components.favorites import FavoritesComponent
from crystal_toolkit.components.literature import LiteratureComponent
from crystal_toolkit.components.robocrys import RobocrysComponent
from crystal_toolkit.components.magnetism import MagnetismComponent
from crystal_toolkit.components.bonding_graph import BondingGraphComponent
from crystal_toolkit.components.magnetism import MagnetismComponent
from crystal_toolkit.components.xrd import XRayDiffractionComponent, XRayDiffractionPanelComponent

from crystal_toolkit.components.transformations.core import AllTransformationsComponent
from crystal_toolkit.components.transformations.supercell import SupercellTransformationComponent
from crystal_toolkit.components.transformations.grainboundary import GrainBoundaryTransformationComponent
from crystal_toolkit.components.transformations.autooxistatedecoration import AutoOxiStateDecorationTransformationComponent

from crystal_toolkit.components.upload import StructureMoleculeUploadComponent
#from crystal_toolkit.components.summary import SummaryComponent
from crystal_toolkit.helpers.layouts import *
from crystal_toolkit.helpers.scene import *
from crystal_toolkit.helpers.view import view
