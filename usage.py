import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from mp_dash_components.layouts.search import SearchComponent
from mp_dash_components.layouts.json import JSONComponent

app = dash.Dash()

app.scripts.config.serve_locally = True
app.config['suppress_callback_exceptions'] = True

search_component = SearchComponent(app=app)
search_output = JSONComponent(app=app, origin_component=search_component)

search_example = html.Div([
    dcc.Markdown("""
# SearchComponent

The search component can be used to query Materials Project's database of
inorganic crystal structures. Queries can be one of the following:

* A chemical formula, e.g. Fe2O3 or \*2O3 (\* acts as a wildcard)
* A chemical system, e.g. Fe-O or \*-Fe-O
* A Materials Project ID (mp-id), a unique database identifier, e.g. mp-1234
* A chemical name, e.g. iron oxide

If multiple results are returned, they are presented as a dropdown list to
choose from.
    """),
    search_component.all_layouts,
    search_output.all_layouts,
    html.Hr()
])

app.layout = html.Div([
    search_example,
])

if __name__ == '__main__':
    app.run_server(debug=True, threaded=True, port=8000,
                   dev_tools_hot_reload_interval=5000,
                   dev_tools_hot_reload_max_retry=30)
