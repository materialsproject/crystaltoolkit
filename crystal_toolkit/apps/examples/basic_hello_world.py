# standard Dash imports
import dash
import dash_html_components as html
import dash_core_components as dcc

# standard Crystal Toolkit import
import crystal_toolkit.components as ctc

# create Dash app as normal
app = dash.Dash()

# tell Crystal Toolkit about the app
ctc.register_app(app)

# create your layout
my_layout = html.Div(["Hello scientist!"])

# wrap your app.layout with crystal_toolkit_layout()
# to ensure all necessary components are loaded into layout
app.layout = ctc.crystal_toolkit_layout(my_layout)

# allow app to be run using "python app.py"
# in production, deploy behind gunicorn or similar
# see Dash documentation for more information
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
