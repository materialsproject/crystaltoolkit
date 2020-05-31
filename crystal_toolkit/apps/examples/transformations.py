# standard Dash imports
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

# standard Crystal Toolkit import
import crystal_toolkit.components as ctc
from dash_mp_components import JsonView

# import for this example
from pymatgen import Structure, Lattice

# create Dash app as normal
app = dash.Dash()

# create the Structure object
structure = Structure(Lattice.cubic(4.2), ["Na", "K"], [[0, 0, 0], [0.5, 0.5, 0.5]])

from pymatgen import MPRester

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
    [Input(t.id(), "data") for t in transformation_component.transformations.values()],
)


@app.callback(
    Output(structure_component_transformed.id(), "data"),
    [Input(transformation_component.id(), "data")],
)
def update_structure(struct):
    return struct


# allow app to be run using "python structure.py"
# in production, deploy behind gunicorn or similar
# see Dash documentation for more information
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
