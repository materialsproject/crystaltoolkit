# standard Dash imports
import dash
import dash_html_components as html
import dash_core_components as dcc

# standard Crystal Toolkit import
import crystal_toolkit.components as ctc

# create Dash app as normal
app = dash.Dash()

# create your layout
my_layout = html.Div(["Hello scientist!"])

# tell Crystal Toolkit about the app and layout we want to display
ctc.register_crystal_toolkit(app=app, layout=my_layout, cache=None)

# allow app to be run using "python app.py"
# in production, deploy behind gunicorn or similar
# see Dash documentation for more information
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
