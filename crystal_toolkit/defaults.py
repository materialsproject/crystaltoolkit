"""Populate the default values from the JSON file"""
import json
import os as _os

from typing import Any
from collections import defaultdict

_DEFAULTS: dict[str, Any] = defaultdict()
default_js = _os.path.join(
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__))), "./", "defaults.json"
)

with open(default_js) as handle:
    _DEFAULTS.update(json.loads(handle.read()))