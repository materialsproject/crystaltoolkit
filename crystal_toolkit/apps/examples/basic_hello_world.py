import dash
from dash import html

from crystal_toolkit.settings import SETTINGS

# create Dash app as normal
app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

# create your layout
app.layout = html.Span(["Hello scientist!"])

# allow app to be run using "python app.py"
# in production, deploy behind gunicorn or similar
# see Dash documentation for more information
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
