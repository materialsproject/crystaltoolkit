from __future__ import print_function as _

import os as _os
import sys as _sys
import json
from collections import defaultdict

import dash as _dash


_basepath = _os.path.dirname(__file__)
_filepath = _os.path.abspath(_os.path.join(_basepath, "package.json"))
with open(_filepath) as f:
    package = json.load(f)

package_name = package["name"].replace(" ", "_").replace("-", "_")
__version__ = package["version"]

# pleasant hack to support MSONable objects in Dash callbacks natively
from monty.json import MSONable


def to_plotly_json(self):
    return self.as_dict()


MSONable.to_plotly_json = to_plotly_json


# Populate the default values from the JSON file
_DEFAULTS = defaultdict(lambda: None)
default_js = _os.path.join(
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__))), "./", "defaults.json"
)

with open(default_js) as handle:
    _DEFAULTS.update(json.loads(handle.read()))

try:
    # convenience import for Jupyter users
    import pythreejs
    from crystal_toolkit.helpers.pythreejs_renderer import view
    from crystal_toolkit.renderables import *
except ImportError:
    pass
