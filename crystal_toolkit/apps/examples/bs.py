# standard Dash imports
import dash
import dash_html_components as html
import dash_core_components as dcc

# standard Crystal Toolkit import
import crystal_toolkit.components as ctc

# MPRester to get bs and dos
from pymatgen import MPRester

# create Dash app as normal
app = dash.Dash()

# If callbacks created dynamically they cannot be statically checked at app startup.
# For this simple example this IS a problem and,
# nested layout this will need to be enabled -- consult Dash documentation
# for more information.
# app.config["suppress_callback_exceptions"] = True

# tell Crystal Toolkit about the app
ctc.register_app(app)


mpid = {"mpid": "mp-149"}

with MPRester() as m:
    bandstructure_symm_line = m.get_bandstructure_by_material_id(mpid["mpid"])
    density_of_states = m.get_dos_by_material_id(mpid["mpid"])

# create the Crystal Toolkit component
structure_component = ctc.BandstructureAndDosComponent(
    bandstructure_symm_line=bandstructure_symm_line, density_of_states=density_of_states
)

# example layout to demonstrate capabilities of component
my_layout = html.Div(
    [
        html.H1("Band Structure and Density of States Example"),
        html.H2("Standard Layout"),
        structure_component.layout(),
        html.H2("Technical Details"),
        dcc.Markdown(str(structure_component)),
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
