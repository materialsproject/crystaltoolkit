import json
import os as _os
from collections import defaultdict

__version__ = "2020.03.20"

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


# monkey-patching to add get_scene() methods to common objects
from crystal_toolkit.renderables import *
