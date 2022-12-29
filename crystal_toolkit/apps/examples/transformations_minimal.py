import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from dash_mp_components import JsonView
from pymatgen.core.lattice import Lattice
from pymatgen.core.structure import Structure
from pymatgen.ext.matproj import MPRester

import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

# create the Structure object
structure = Structure(Lattice.cubic(4.2), ["Na", "K"], [[0, 0, 0], [0.5, 0.5, 0.5]])


# create an input structure as an example
structure = MPRester().get_structure_by_material_id("mp-804")
structure_in = dcc.Store(id="structure_in", data=structure.as_dict())
# patch, this should be a JSON component ...
structure_in.id = lambda: "structure_in"

# and the transformation component itself
transformation_component = ctc.AllTransformationsComponent(
    transformations=[
        "AutoOxiStateDecorationTransformationComponent",
        "SupercellTransformationComponent",
        # "SlabTransformationComponent",
        # "SubstitutionTransformationComponent",
        "CubicSupercellTransformationComponent",
        # "GrainBoundaryTransformationComponent"
    ],
    input_structure=structure_in,
)

# example layout to demonstrate capabilities of component
my_layout = html.Div(
    [
        html.H1("TransformationComponent Example"),
        html.H2("Standard Layout"),
        transformation_component.layout(),
        html.H3("Example Input Structure"),
        JsonView(src=structure.as_dict()),
        html.H3("Example Transformed Structure"),
        JsonView(src={}, id="structure_out"),
    ]
)

# tell crystal toolkit about your app and layout
ctc.register_crystal_toolkit(app, layout=my_layout)


@app.callback(
    Output("structure_out", "data"),
    Input(transformation_component.id(), "data"),
)
def update_structure(struct):
    return struct


# run this app with "python path/to/this/file.py"
# in production, deploy behind gunicorn or similar
# see Dash documentation for more information
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
