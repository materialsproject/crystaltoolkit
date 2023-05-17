from __future__ import annotations

import dash
from dash import html
from dash.dependencies import Input, Output
from dash_mp_components import JsonView
from pymatgen.core import Lattice, Structure
from pymatgen.ext.matproj import MPRester

import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

# create the Structure object
structure = Structure(Lattice.cubic(4.2), ["Na", "K"], [[0, 0, 0], [0.5, 0.5, 0.5]])


# create an input structure as an example
structure_component = ctc.StructureMoleculeComponent(
    MPRester().get_structure_by_material_id("mp-804"), id="structure_in"
)
# and a way to view the transformed structure
structure_component_transformed = ctc.StructureMoleculeComponent(
    MPRester().get_structure_by_material_id("mp-804"), id="structure_out"
)

# and the transformation component itself
transformation_component = ctc.AllTransformationsComponent(
    input_structure_component=structure_component,
)

# example layout to demonstrate capabilities of component
my_layout = html.Div(
    [
        html.H1("TransformationComponent Example"),
        html.H2("Standard Layout"),
        transformation_component.layout(),
        html.H3("Example Input Structure"),
        structure_component.layout(size="500px"),
        html.H3("Example Transformed Structure"),
        structure_component_transformed.layout(size="500px"),
        html.H3("JSON View of Transformations"),
        JsonView(id="json"),
    ]
)

# tell crystal toolkit about your app and layout
ctc.register_crystal_toolkit(app, layout=my_layout)

# this is here for to see the JSON representation of
# the transformations when running the example app,
# it is not necessary for running the component
app.clientside_callback(
    """
    function (...args) {
        return {"transformations": args}
    }
    """,
    Output("json", "src"),
    [
        Input(trafo.id(), "data")
        for trafo in transformation_component.transformations.values()
    ],
)


@app.callback(
    Output(structure_component_transformed.id(), "data"),
    Input(transformation_component.id(), "data"),
)
def update_structure(struct):
    return struct


# run this app with "python path/to/this/file.py"
# in production, deploy behind gunicorn or similar
# see Dash docs for more info
if __name__ == "__main__":
    app.run(debug=True, port=8050)
