import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt

from dash.dependencies import Input, Output, State

from crystal_toolkit.helpers.layouts import Label
from crystal_toolkit.components.transformations.core import TransformationComponent

from pymatgen import Specie, Element
from pymatgen.transformations.standard_transformations import SubstitutionTransformation

from ast import literal_eval


class SubstitutionTransformationComponent(TransformationComponent):
    @property
    def title(self):
        return "Substitute one species for another"

    @property
    def description(self):
        return """Replace one species in your structure (\"Previous Species\")
with another species (\"New Species\"). The new species can be specified as an
element (for example, O), as an element with an oxidation state (for example, O2-)
or as a composition (for example, {"Au":0.5, "Cu":0.5} for a 50/50 mixture of gold
and copper). Please consult the pymatgen documentation for more information.
"""

    @property
    def transformation(self):
        return SubstitutionTransformation

    def options_layout(self, inital_args_kwargs):

        options = html.Div(
            [
                dt.DataTable(
                    id=self.id("species_mapping"),
                    columns=[
                        {"id": "prev", "name": "Previous Species"},
                        {"id": "new", "name": "New Species"},
                    ],
                    data=[{"prev": None, "new": None} for i in range(4)],
                    editable=True,
                )
            ]
        )

        return options

    def generate_callbacks(self, app, cache):
        super().generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("transformation_args_kwargs"), "data"),
            [Input(self.id("species_mapping"), "data")],
        )
        def update_transformation_kwargs(rows):
            def get_el_occu(string):
                try:
                    el_occu = literal_eval(string)
                except ValueError:
                    el_occu = string
                return el_occu

            species_map = {
                get_el_occu(row["prev"]): get_el_occu(row["new"])
                for row in rows
                if (row["prev"] and row["new"])
            }

            print(species_map)

            return {"args": [species_map], "kwargs": {}}
