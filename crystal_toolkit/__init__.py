import json
import os as _os
from collections import defaultdict
from pathlib import Path

__version__ = "2020.05.21"

MODULE_PATH = Path(__file__).parents[0]

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


from crystal_toolkit.settings import SETTINGS as _SETTINGS


def _repr_mimebundle_(self, include=None, exclude=None):
    """
    Render Scenes using crystaltoolkit-extension for Jupyter Lab.
    """
    # TODO: add Plotly, application/vnd.plotly.v1+json
    if hasattr(self, "get_scene"):
        return {
            "application/vnd.mp.ctk+json": self.get_scene().to_json(),
            # "application/json": self.as_dict(),
            "text/plain": self.__repr__(),
        }
    else:
        return {"application/json": self.as_dict(), "text/plain": self.__repr__()}


MSONable._repr_mimebundle_ = _repr_mimebundle_


def _ipython_display_(self):
    """
    Render Scenes using crystaltoolkit-extension for Jupyter Lab.

    This function ensures that objects are also printed in string format
    as previously.
    """
    from IPython.display import publish_display_data

    if _SETTINGS.JUPYTER_LAB_PRINT_REPR:
        print(self.__repr__())

    publish_display_data(self._repr_mimebundle_())


MSONable._ipython_display_ = _ipython_display_

# monkey-patching to add get_scene() methods to common objects
from crystal_toolkit.renderables import *
