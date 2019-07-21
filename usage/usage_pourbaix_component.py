import dash
import dash_html_components as html
import crystal_toolkit.components as ctc
from pymatgen import MPRester
from pymatgen.analysis.pourbaix_diagram import PourbaixDiagram

from pymatgen import Structure, Lattice

app = dash.Dash(__name__)

app.config["suppress_callback_exceptions"] = True
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True
app.title = "Crystal Toolkit Example Components"


# so that Crystal Toolkit can create callbacks
# ctc.register_app(app)

# Pourbaix diagram
with MPRester() as mpr:
    pbx_entries = mpr.get_pourbaix_entries(["Fe"])
pbx = PourbaixDiagram(pbx_entries)

# instantiate a component to view structures
component = ctc.PourbaixDiagramComponent(
    contents=pbx # this is a pymatgen PourbaixDiagram object
)

# for a custom-sized component, use `struct_component.struct_layout` and put
# it inside a Div of the required size
app.layout = html.Div([
    ctc.MPComponent.all_app_stores(),  # not required in this minimal example, but usually necessary for interactivity
    component.standard_layout
])

component.generate_callbacks(app, None)

if __name__ == "__main__":
    app.run_server(debug=True)
