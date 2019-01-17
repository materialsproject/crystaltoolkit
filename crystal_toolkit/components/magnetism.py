import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.helpers.layouts import Columns, Column
from crystal_toolkit.components.core import PanelComponent
from crystal_toolkit.components.structure import StructureMoleculeComponent

from pymatgen.analysis.magnetism import CollinearMagneticStructureAnalyzer


class MagnetismComponent(PanelComponent):

    @property
    def title(self):
        return "Magnetic Properties"

    @property
    def description(self):
        return (
            "Information on magnetic moments and magnetic "
            "ordering of this crystal structure."
        )

    @property
    def loading_text(self):
        return "Creating visualization of magnetic structure"

    def update_contents(self, new_store_contents):

        struct = self.from_data(new_store_contents)

        msa = CollinearMagneticStructureAnalyzer(struct, round_magmoms=1)
        if not msa.is_magnetic:
            # TODO: detect magnetic elements (?)
            return html.Div(
                "This structure is not magnetic or does not have "
                "magnetic information associated with it."
            )

        mag_species_and_magmoms = msa.magnetic_species_and_magmoms
        for k, v in mag_species_and_magmoms.items():
            if not isinstance(v, list):
                mag_species_and_magmoms[k] = [v]
        magnetic_atoms = "\n".join(
            [
                f"{sp} ({', '.join([f'{magmom} µB' for magmom in magmoms])})"
                for sp, magmoms in mag_species_and_magmoms.items()
            ]
        )

        magnetization_per_formula_unit = (
            msa.total_magmoms
            / msa.structure.composition.get_reduced_composition_and_factor()[1]
        )

        rows = []
        rows.append(
            (
                html.B("Total magnetization per formula unit"),
                html.Br(),
                f"{magnetization_per_formula_unit:.1f} µB",
            )
        )
        rows.append((html.B("Atoms with local magnetic moments"), html.Br(),
                     magnetic_atoms))

        data_block = html.Div([html.P([html.Span(cell) for cell in row]) for row in rows])

        viewer = StructureMoleculeComponent(
            struct,
            id=self.id("structure"), color_scheme="magmom",
            static=True
        )

        return Columns([
            Column(html.Div([viewer.struct_layout], style={"height": "60vmin"})),
            Column(data_block)
        ])
