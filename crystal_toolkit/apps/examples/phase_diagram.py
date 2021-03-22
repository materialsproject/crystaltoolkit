# standard Dash imports
import dash
import dash_core_components as dcc
import dash_html_components as html

# import for this example
from pymatgen.ext.matproj import MPRester
from pymatgen.analysis.phase_diagram import PhaseDiagram

# standard Crystal Toolkit import
import crystal_toolkit.components as ctc

# create Dash app as normal
app = dash.Dash()

# If callbacks created dynamically they cannot be statically checked at app startup.
# For this simple example this is not a problem, but if creating a complicated,
# nested layout this will need to be enabled -- consult Dash documentation
# for more information.
app.config["suppress_callback_exceptions"] = True

# tell Crystal Toolkit about the app
ctc.register_app(app)

# first, retrieve entries from Materials Project
with MPRester() as mpr:
    # li_entries = mpr.get_entries_in_chemsys(["Li"])
    # li_o_entries = mpr.get_entries_in_chemsys(["Li", "O"])
    li_co_o_entries = mpr.get_entries_in_chemsys(["Li", "O", "Co"])
    # li_co_o_fe_entries = mpr.get_entries_in_chemsys(["Li", "O", "Co", "Fe"])

# and then create the phase diagrams
# li_phase_diagram = PhaseDiagram(li_entries)
# li_o_phase_diagram = PhaseDiagram(li_o_entries)
li_co_o_phase_diagram = PhaseDiagram(li_co_o_entries)
# li_co_o_fe_phase_diagram = PhaseDiagram(li_co_o_fe_entries)

# and the corresponding Crystal Toolkit components
# we're creating four components here to demonstrate
# visualizing 1-D, 2-D, 3-D and 4-D phase diagrams
# li_phase_diagram_component = ctc.PhaseDiagramComponent(li_phase_diagram)
# li_o_phase_diagram_component = ctc.PhaseDiagramComponent(li_o_phase_diagram)
li_co_o_phase_diagram_component = ctc.PhaseDiagramComponent(li_co_o_phase_diagram)
# li_co_o_fe_phase_diagram_component = ctc.PhaseDiagramComponent(li_co_o_fe_phase_diagram)

print(li_co_o_entries)

# example layout to demonstrate capabilities of component
my_layout = html.Div(
    [
        html.H1("PhaseDiagramComponent Example"),
        html.H2("Standard Layout (1 Element)"),
        html.H2("Standard Layout (2 Elements)"),
        html.H2("Standard Layout (3 Elements)"),
        li_co_o_phase_diagram_component.layout(),
        html.H2("Standard Layout (4 Elements)"),
        html.H2("Technical Details"),
        dcc.Markdown(str(li_co_o_phase_diagram_component)),
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
