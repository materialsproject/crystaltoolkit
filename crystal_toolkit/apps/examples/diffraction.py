# standard Dash imports
import dash
import dash_html_components as html
import dash_core_components as dcc

# standard Crystal Toolkit import
import crystal_toolkit.components as ctc

# import for this example
from pymatgen import MPRester
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.analysis.diffraction.xrd import XRDCalculator

# create Dash app as normal
app = dash.Dash()

# tell Crystal Toolkit about the app
ctc.register_app(app)

# first, retrieve entries from Materials Project
with MPRester() as mpr:
    struct = mpr.get_structure_by_material_id("mp-13")

xrd_component = ctc.XRayDiffractionComponent(initial_structure=struct)
# xrd_component = ctc.XRayDiffractionComponent(mpid=mpid)

# example layout to demonstrate capabilities of component
my_layout = html.Div(
    [
        html.H1("XRDComponent Example"),
        html.H2("Shown from Spectra object"),
        html.H2("Generated from Structure object"),
        xrd_component.layout(),
        html.H2("Generated from mpid"),
    ]
)

# wrap your app.layout with crystal_toolkit_layout()
# to ensure all necessary components are loaded into layout
app.layout = ctc.crystal_toolkit_layout(my_layout)


# allow app to be run using "python structure.py"
# in production, deploy behind gunicorn or similar
# see Dash documentation for more information
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
