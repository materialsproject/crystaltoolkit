from __future__ import annotations

from fractions import Fraction

import numpy as np
from dash import callback_context, html
from dash.dependencies import Input, Output
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.util.string import unicodeify_spacegroup, unicodeify_species

from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import (
    H5,
    Column,
    Columns,
    Loading,
    get_data_list,
    get_table,
)


class SymmetryPanel(PanelComponent):
    @staticmethod
    def pretty_frac_format(x):
        x = x % 1
        fraction = Fraction(x).limit_denominator(8)
        if np.allclose(x, 1):
            x_str = "0"
        elif not np.allclose(x, float(fraction)):
            x = np.around(x, decimals=3)
            x_str = f"{x:.3g}"
        else:
            x_str = str(fraction)
        return x_str

    @property
    def title(self) -> str:
        return "Symmetry"

    @property
    def description(self) -> str:
        return "Analyze the symmetry of your crystal structure or molecule."

    def contents_layout(self):
        state = {"symprec": 0.01, "angle_tolerance": 5}

        symprec = self.get_numerical_input(
            label="Symmetry-finding tolerance",
            kwarg_label="symprec",
            state=state,
            help_str="Tolerance of distance between atomic positions and between lengths "
            "of lattice vectors to be tolerated in the symmetry finding in Ångstroms. "
            "The angle distortion between lattice vectors is converted to a length and "
            "compared with this distance tolerance.",
            shape=(),
            min=0,
        )
        angle_tolerance = self.get_numerical_input(
            label="Angle tolerance",
            kwarg_label="angle_tolerance",
            state=state,
            help_str="Explicit angle tolerance for symmetry finding in degrees. "
            "Set to a negative value to disable.",
            shape=(),
        )

        return html.Div(
            [
                symprec,
                angle_tolerance,
                html.Br(),
                html.Br(),
                Loading(id=self.id("analysis")),
            ]
        )

    def generate_callbacks(self, app, cache) -> None:
        super().generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("analysis"), "children"),
            Input(self.id(), "data"),
            Input(self.get_kwarg_id("symprec"), "value"),
            Input(self.get_kwarg_id("angle_tolerance"), "value"),
        )
        def update_contents(data, symprec, angle_tolerance):
            if not data:
                return html.Div()

            struct = self.from_data(data)

            if not isinstance(struct, Structure):
                return html.Div(
                    "Can only analyze symmetry of crystal structures at present."
                )

            kwargs = self.reconstruct_kwargs_from_state(callback_context.inputs)
            symprec = kwargs["symprec"]
            angle_tolerance = kwargs["angle_tolerance"]

            if symprec <= 0:
                return html.Span(
                    f"Please use a positive symmetry-finding tolerance (currently {symprec})."
                )

            sga = SpacegroupAnalyzer(
                struct, symprec=symprec, angle_tolerance=angle_tolerance
            )

            try:
                data = dict()
                data["Crystal System"] = sga.get_crystal_system().title()
                data["Lattice System"] = sga.get_lattice_type().title()
                data["Hall Number"] = sga.get_hall()
                data["International Number"] = sga.get_space_group_number()
                data["Symbol"] = unicodeify_spacegroup(sga.get_space_group_symbol())
                data["Point Group"] = unicodeify_spacegroup(
                    sga.get_point_group_symbol()
                )

                sym_struct = sga.get_symmetrized_structure()
            except Exception:
                return html.Span(
                    f"Failed to calculate symmetry with this combination of "
                    f"symmetry-finding ({symprec}) and angle tolerances ({angle_tolerance})."
                )

            datalist = get_data_list(data)

            wyckoff_contents = []

            wyckoff_data = sorted(
                zip(sym_struct.wyckoff_symbols, sym_struct.equivalent_sites),
                key=lambda x: "".join(filter(lambda w: w.isalpha(), x[0])),
            )

            for symbol, equiv_sites in wyckoff_data:
                wyckoff_contents.append(
                    html.Label(
                        f"{symbol}, {unicodeify_species(equiv_sites[0].species_string)}",
                        className="mpc-label",
                    )
                )
                site_data = [
                    (
                        self.pretty_frac_format(site.frac_coords[0]),
                        self.pretty_frac_format(site.frac_coords[1]),
                        self.pretty_frac_format(site.frac_coords[2]),
                    )
                    for site in equiv_sites
                ]
                wyckoff_contents.append(get_table(site_data))

            return Columns(
                [
                    Column([H5("Overview"), datalist]),
                    Column([H5("Wyckoff Positions"), html.Div(wyckoff_contents)]),
                ]
            )
