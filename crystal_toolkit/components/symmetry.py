import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from pymatgen.util.string import unicodeify_spacegroup, unicodeify_species
from crystal_toolkit.core.panelcomponent import PanelComponent, PanelComponent2
from crystal_toolkit.helpers.inputs import *

from pymatgen.core.structure import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from ast import literal_eval

from fractions import Fraction


class SymmetryPanel(PanelComponent2):
    ...


class SymmetryComponent(PanelComponent):
    @property
    def title(self):
        return "Symmetry"

    @property
    def description(self):
        return "Analyze the symmetry of your crystal structure or molecule."

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
    def header(self):

        symprec = get_float_input(
            id=self.id("symprec"),
            default=0.01,
            label="Symmetry-finding tolerance",
            help="Tolerance of distance between atomic positions and between lengths "
            "of lattice vectors to be tolerated in the symmetry finding in Ångstroms. "
            "The angle distortion between lattice vectors is converted to a length and "
            "compared with this distance tolerance.",
        )
        angle_tolerance = get_float_input(
            id=self.id("angle_tolerance"),
            default=5,
            label="Angle tolerance",
            help="Explicit angle tolerance for symmetry finding in degrees. "
            "Set to a negative value to disable.",
        )

        return html.Div([symprec, angle_tolerance, html.Br(), html.Br()])

    @property
    def update_contents_additional_inputs(self):
        return [(self.id("symprec"), "value"), (self.id("angle_tolerance"), "value")]

    def update_contents(self, new_store_contents, symprec, angle_tolerance):

        try:
            # input sanitation
            symprec = float(literal_eval(str(symprec)))
            angle_tolerance = float(literal_eval(str(angle_tolerance)))
        except:
            raise PreventUpdate

        struct_or_mol = self.from_data(new_store_contents)

        if not isinstance(struct_or_mol, Structure):
            return html.Div(
                "Can only analyze symmetry of crystal structures at present."
            )

        sga = SpacegroupAnalyzer(
            struct_or_mol, symprec=symprec, angle_tolerance=angle_tolerance
        )

        try:
            data = {}
            data["Crystal System"] = sga.get_crystal_system().title()
            data["Lattice System"] = sga.get_lattice_type().title()
            data["Hall Number"] = sga.get_hall()
            data["International Number"] = sga.get_space_group_number()
            data["Symbol"] = unicodeify_spacegroup(sga.get_space_group_symbol())
            data["Point Group"] = unicodeify_spacegroup(sga.get_point_group_symbol())

            sym_struct = sga.get_symmetrized_structure()
        except:
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
