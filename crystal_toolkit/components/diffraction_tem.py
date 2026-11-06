from __future__ import annotations

from typing import TYPE_CHECKING
from warnings import warn

from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import Column, Columns

if TYPE_CHECKING:
    from dash import html
    from pymatgen.core import Structure

try:
    import quantem.diffsim as diffsim
    import quantem.diffsim.dash as diffsim_dash
except ImportError:
    no_diffsim_msg = (
        "requires the quantem.diffsim package. Please pip install quantem.diffsim."
    )
    diffsim = None

# Author: Colin Ophus


class TEMDiffractionComponent(MPComponent):
    """Electron diffraction simulator from quantEM (the quantem.diffsim package).

    The server converts the structure to CIF text of its conventional standard
    cell, and the simulator computes the reflections, structure factors and
    Bloch wave intensities in the browser.
    """

    def __init__(
        self, *args, initial_structure: Structure | None = None, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.create_store("structure", initial_data=initial_structure)

    def layout(self) -> html.Div | Columns:
        """The simulator's settings store and the element it draws into."""
        if not diffsim:
            warn(f"{type(self).__name__} {no_diffsim_msg}")
            col = Column(
                "This feature will not work unless quantem.diffsim is installed on the server."
            )
            return Columns([col])

        return diffsim_dash.layout(self.id("quantem-diffsim"))

    def generate_callbacks(self, app, cache) -> None:
        """Send the simulator settings for each new structure."""
        if not diffsim:
            return

        # serves the simulator bundle and adds the clientside callback that draws it
        diffsim_dash.register(app)

        @app.callback(
            Output(diffsim_dash.settings_id(self.id("quantem-diffsim")), "data"),
            Input(self.id("structure"), "data"),
        )
        def update_settings(structure):
            if not structure:
                raise PreventUpdate
            return diffsim.settings(
                self.from_data(structure),
                zone_axis=[0, 0, 1],
                mode="nanobeam",
                energy_keV=200,
                title="Electron diffraction",
            )
