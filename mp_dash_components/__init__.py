import os as _os
import dash as _dash
import sys as _sys
from .version import __version__

_current_path = _os.path.dirname(_os.path.abspath(__file__))

_components = _dash.development.component_loader.load_components(
    _os.path.join(_current_path, 'metadata.json'),
    'mp_dash_components'
)

_this_module = _sys.modules[__name__]


_js_dist = [
    {
        "relative_package_path": "bundle.js",
        "external_url": (
            "https://unpkg.com/mp-dash-components@{}"
            "/mp_dash_components/bundle.js"
        ).format(__version__),
        "namespace": "mp_dash_components"
    }
]

_css_dist = []


for _component in _components:
    setattr(_this_module, _component.__name__, _component)
    setattr(_component, '_js_dist', _js_dist)
    setattr(_component, '_css_dist', _css_dist)


# convenience imports
from mp_dash_components.components.json import JSONEditor
from mp_dash_components.components.search import SearchComponent
from mp_dash_components.components.structure import StructureMoleculeComponent
from mp_dash_components.components.favorites import FavoritesComponent
from mp_dash_components.components.literature import LiteratureComponent
from mp_dash_components.components.robocrys import RobocrysComponent
from mp_dash_components.components.magnetism import MagnetismComponent
#from mp_dash_components.components.bonding_graph import BondingGraphComponent
from mp_dash_components.components.magnetism import MagnetismComponent
from mp_dash_components.components.transformations.core import TransformationsComponent
from mp_dash_components.helpers.layouts import *
from mp_dash_components.helpers.scene import *
from mp_dash_components.helpers.view import view
