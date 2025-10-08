"""Pleasant hack to support MSONable objects in Dash callbacks natively."""

from __future__ import annotations

import socketserver
from typing import TYPE_CHECKING, ClassVar
from warnings import warn

from dash import Dash
from IPython.display import JSON, publish_display_data
from monty.json import MSONable, jsanitize
from pymatgen.analysis.graphs import MoleculeGraph, StructureGraph
from pymatgen.core.structure import SiteCollection

import crystal_toolkit.helpers.layouts as ctl
from crystal_toolkit.components.structure import StructureMoleculeComponent
from crystal_toolkit.core.plugin import CrystalToolkitPlugin
from crystal_toolkit.settings import SETTINGS

if TYPE_CHECKING:
    from crystal_toolkit.core.mpcomponent import MPComponent


class _JupyterRenderer:
    # TODO: For now this is hard-coded but could be replaced with a Registry class later.
    registry: ClassVar[dict[MSONable, MPComponent]] = {
        SiteCollection: StructureMoleculeComponent,
        StructureGraph: StructureMoleculeComponent,
        MoleculeGraph: StructureMoleculeComponent,
    }

    @staticmethod
    def _find_available_port():
        """Find an available port.

        Thank you Mihai Capotă, https://stackoverflow.com/a/61685162
        """
        with socketserver.TCPServer(("localhost", 0), None) as s:
            return s.server_address[1]

    # check docs about callback exception output
    # check docs about proxy settings

    def run(self, layout):
        """Run Dash app."""
        app = Dash(plugins=[CrystalToolkitPlugin(layout=layout)])

        port = SETTINGS.JUPYTER_EMBED_PORT or self._find_available_port()

        # try preferred port first, if already in use try alternative
        try:
            app.run(port=port, jupyter_mode=SETTINGS.JUPYTER_EMBED_MODE)
        except OSError:
            free_port = self._find_available_port()
            warn("Port {port} not available, using {free_port} instead.")
            app.run(port=free_port, jupyter_mode=SETTINGS.JUPYTER_EMBED_MODE)

    def display(self, obj):
        """Display a provided object."""
        for kls, component in self.registry.items():
            if isinstance(obj, kls):
                layout = ctl.Block(
                    [component(obj).layout()],
                    style={"margin-top": "1rem", "margin-left": "1rem"},
                )
                return self.run(layout)

        raise ValueError(f"No component defined for object of type {type(obj)}.")


def _to_plotly_json(self):
    """Patch to ensure MSONable objects can be serialized into JSON by plotly tools."""
    return self.as_dict()


def _display_json(self, **kwargs):
    """Display JSON representation of an MSONable object inside Jupyter."""
    JSON(self.as_dict(), **kwargs)


def _repr_mimebundle_(self, include=None, exclude=None):
    """Method used by Jupyter. A default for MSONable objects to return JSON representation."""
    return {
        "application/json": self.as_dict(),
        "text/plain": repr(self),
    }


def _ipython_display_(self):
    """Display MSONable objects using a Crystal Toolkit component, if available."""
    if any(isinstance(self, x) for x in _JupyterRenderer.registry):
        return _JupyterRenderer().display(self)

    # To be strict here, we could use inspect.signature
    # and .return_annotation is either a Scene or a go.Figure respectively
    # and also check all .parameters .kind.name have no POSITIONAL_ONLY
    # in practice, fairly unlikely this will cause issues without strict checking.
    # TODO: This can be removed once a central registry of renderable objects is implemented.
    if hasattr(self, "get_scene"):
        display_data = {
            "application/vnd.mp.ctk+json": self.get_scene().to_json(),
            "text/plain": repr(self),
        }
    elif hasattr(self, "get_plot"):
        display_data = {
            "application/vnd.plotly.v1+json": self.get_plot().to_plotly_json(),
            "application/json": jsanitize(self.as_dict()),
            "text/plain": repr(self),
        }
    else:
        display_data = {
            "application/json": jsanitize(self.as_dict()),
            "text/plain": repr(self),
        }

    publish_display_data(display_data)
    return None


def patch_msonable():
    """Patch MSONable to allow MSONable objects to render in Jupyter
    environments using Crystal Toolkit components.
    """
    MSONable.to_plotly_json = _to_plotly_json
    MSONable._repr_mimebundle_ = _repr_mimebundle_
    MSONable.display_json = _display_json
    MSONable._ipython_display_ = _ipython_display_
