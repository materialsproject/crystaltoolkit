import dash
import dash_html_components as html
import crystal_toolkit.components as ctc

from pymatgen import Structure, Lattice

app = dash.Dash(__name__)

app.config["suppress_callback_exceptions"] = True
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True
app.title = "Crystal Toolkit Example Components"


# so that Crystal Toolkit can create callbacks
ctc.register_app(app)

# StructureMoleculeComponent

example_struct = Structure.from_spacegroup(
    "P6_3mc",
    Lattice.hexagonal(3.22, 5.24),
    ["Ga", "N"],
    [[1 / 3, 2 / 3, 0], [1 / 3, 2 / 3, 3 / 8]],
)

# instantiate a component to view structures
struct_component = ctc.StructureMoleculeComponent(
    example_struct,  # this is a pymatgen Structure
    id='Comp1'
)
struct_component2 = ctc.StructureMoleculeComponent(
    example_struct,  # this is a pymatgen Structure
    id='Comp2'
)

# for a custom-sized component, use `struct_component.struct_layout` and put
# it inside a Div of the required size
# app.layout = html.Div([
#     # ctc.MPComponent.all_app_stores(),  # not required in this minimal example, but usually necessary for interactivity
#     struct_component2.standard_layout
# ])

app.layout = html.Div([
        html.Div([html.H3('Column 1'),
                  struct_component.standard_layout,
                  ],
                 style={'width': '50%', 'display': 'inline-block'}),
        html.Div([html.H3('Column 2'),
                  struct_component2.standard_layout,
                  ],
                 style={'width': '50%', 'display': 'inline-block'}),
    ])

app.layout = html.Div(children=[
    html.Div(
        struct_component.standard_layout,
        style={'width': '33%', 'display': 'inline-block'}
    ),
    html.Div(
        struct_component2.standard_layout,
        style={'width': '33%', 'display': 'inline-block'}
    ),
], style={'width': '100%', 'display': 'inline-block'})

if __name__ == "__main__":
    app.run_server(debug=True)
