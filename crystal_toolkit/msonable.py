"""pleasant hack to support MSONable objects in Dash callbacks natively"""
from __future__ import annotations

from monty.json import MSONable


def to_plotly_json(self):
    return self.as_dict()


MSONable.to_plotly_json = to_plotly_json


def _repr_mimebundle_(self, include=None, exclude=None):
    """Render Scenes using crystaltoolkit-extension for Jupyter Lab."""
    # TODO: add Plotly, application/vnd.plotly.v1+json

    help_text_ct = """If you see this text, the Crystal Toolkit Jupyter Lab \n
extension is not installed. You can install it by running \n
\"pip install crystaltoolkit-extension\" \n
from the same environment you run \"jupyter lab\". \n
This only works in Jupyter Lab 3.x or above.\n\n
"""

    help_text_plotly = """If you see this text, the Plotly Jupyter Lab extension
is not installed, please consult Plotly documentation for information on how to
install.
"""

    # TODO: to be strict here, we could use inspect.signature
    # and .return_annotation is either a Scene or a go.Figure respectively
    # and also check all .parameters .kind.name have no POSITIONAL_ONLY
    # in practice, fairly unlikely this will cause issues without strict checking
    if hasattr(self, "get_scene"):
        return {
            "application/vnd.mp.ctk+json": self.get_scene().to_json(),
            "text/plain": help_text_ct + repr(self),
        }
    elif hasattr(self, "get_plot"):
        return {
            "application/vnd.plotly.v1+json": self.get_plot().to_plotly_json(),
            "text/plain": help_text_plotly + repr(self),
        }
    else:
        return {"application/json": self.as_dict(), "text/plain": repr(self)}


MSONable._repr_mimebundle_ = _repr_mimebundle_


def show_json(self):
    from IPython.display import display_json

    return display_json(self.as_dict(), raw=True)


MSONable.show_json = show_json


def _ipython_display_(self):
    """Render Scenes using crystaltoolkit-extension for Jupyter Lab.

    This function ensures that objects are also printed in string format as previously.
    """
    from IPython.display import publish_display_data

    publish_display_data(self._repr_mimebundle_())


MSONable._ipython_display_ = _ipython_display_
