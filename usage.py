import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from dash.exceptions import PreventUpdate

from mp_dash_components.helpers import mp_component, sanitize_input
from mp_dash_components.layouts.structure import *
from mp_dash_components.layouts.structure_transformations import *
from mp_dash_components.layouts.misc import *

from monty.serialization import loadfn

app = dash.Dash()
app.title = "Structure Viewer"

app.scripts.config.serve_locally = True
app.config['suppress_callback_exceptions'] = True
app.css.append_css({'external_url': 'https://codepen.io/mkhorton/pen/aKmNxW.css'})

example_structure = loadfn('example_files/example_structure.json')

tab_style = {'width': '100%', 'height': '80vh',
             'border': '1px solid #d6d6d6', 'border-top': 'none',
             'box-sizing': 'border-box'}

from pymatgen import __version__ as pymatgen_version
all_mpids = loadfn('all_mpids.json')
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    structure_import_from_url(url_id='url', app=app),
    html.Br(),
    html.Br(),
    html.Div(className='one columns'),
    html.Div([
        dcc.Tabs(id="tabs", value="structure-tab", children=[
            dcc.Tab(label="Structure", value="structure-tab",
                    children=[html.Div([mp_component(example_structure, app=app, id='structure-viewer')],
                                       style=tab_style)]),
            dcc.Tab(label="Bonding Graph", value="graph-tab",
                    children=[html.Div([structure_graph(structure_viewer_id='structure-viewer', app=app)],
                                       style=tab_style)]),
            dcc.Tab(label="JSON Editor", value="json-tab",
                    children=[
                        html.Div([json_editor(structure_id='json-editor-structure', app=app,
                                              initial_structure=example_structure,
                                              structure_viewer_id='structure-viewer')],
                                  style=tab_style)])
        ]),
        dcc.Markdown('Powered by [pymatgen](http://pymatgen.org) v{}, '
                     'web app created by [@mkhorton](http://perssongroup.lbl.gov/people.html). '
                     '\nNo structures are stored after web app is closed. '
                     'In beta, please report bugs. '.format(pymatgen_version))
    ], className='seven columns'),
    html.Div([
        structure_viewer_header(structure_viewer_id='structure-viewer', app=app),
        html.Br(),
        html.Details(
            [html.Summary(html.H4(' Load Structure', style={'display': 'inline'})),
             html.Br(),
             structure_import_from_mpid(structure_id='query-structure', app=app),
             html.Br(),
             structure_import_from_file(structure_id='uploaded-structure', app=app),
             html.Br(),
             structure_random_input(structure_id='random-structure', app=app, mpid_list=all_mpids)
             ],
            open=True
        ),
        html.Br(),
        html.Details(
            [html.Summary(html.H4(' Inspector', style={'display': 'inline'})),
             html.Br(),
             structure_viewer_legend(structure_viewer_id='structure-viewer', app=app),
             html.Br(),
             structure_inspector(structure_id='structure-viewer', app=app)],
            open=True
        ),
        html.Br(),
        html.Details(
            [html.Summary(html.H4(' View Options', style={'display': 'inline'})),
             html.Br(),
             structure_view_options_layout(structure_viewer_id='structure-viewer', app=app),
             html.Br(),
             structure_view_range(structure_viewer_id='structure-viewer', app=app),
             html.Br(),
             structure_color_scheme_choice(structure_viewer_id='structure-viewer', app=app)],
            open=False
        ),
        html.Br(),
        html.Details(
            [html.Summary(html.H4(' Algorithm Options', style={'display': 'inline'})),
             html.Br(),
             structure_bonding_algorithm(structure_viewer_id='structure-viewer', app=app),
             ],
            open=False
        ),
        html.Br(),
        html.Details(
            [html.Summary(html.H4(' Transformations', style={'display': 'inline'})),
             html.Span('Not implemented yet. Coming soon!'),
             #replace_species_transformation()
             ],
            open=False
        ),
        html.Br(),
        html.Details(
            [html.Summary(html.H4(' Submit to MPComplete', style={'display': 'inline'})),
             html.Span('Not implemented yet. Coming soon!')
             ],
            open=False
        ),
        # structure_screenshot_button(structure_viewer_id='structure-viewer', app=app),  # beta
    ], className='three columns'),
    html.Div(className='one columns'),
], className='rows')

# hack because Dash doesn't support multiple callbacks to single output
combine_option_dicts([
    'structure-viewer_bonding_algorithm_generation_options',
    'structure-viewer_color_scheme_choice_generation_options',
    'structure-viewer_view_range_generation_options'
], 'structure-viewer', 'generationOptions', app=app)


# TODO: remove!
@app.callback(
    Output('tabs', 'children'),
    [Input('tabs', 'value')]
)
def temp_bug_fix(val):
    # stop tabs from switching back to first tab on every callback!
    raise PreventUpdate


@app.callback(
    Output('json-editor-structure', 'value'),
    [
        Input('random-structure', 'children'),
        Input('url_structure', 'children'),
        Input('uploaded-structure', 'children'),
        Input('query-structure', 'children')
    ],
    [State('json-editor-structure', 'value')]
)
def pass_structures_between_components(*args):

    all_structures = args[:-1]
    current_value = args[-1]

    all_structures = [loads(structure) for structure in all_structures if structure]
    all_structures = sorted(all_structures, key=lambda x: -x['_created_at'])

    if len(all_structures) > 0:
        structure = all_structures[0]
        del structure['_created_at']
        return dumps(structure, indent=4)
    else:
        return current_value

@app.callback(
    Output('query-structure_mpid_input', 'value'),
    [Input('url_mpid', 'children')]
)
def update_mpid_query_value(mpid):
    if mpid:
        return mpid
    else:
        raise PreventUpdate


from uuid import uuid4
app.server.secret_key = str(uuid4())
server = app.server

if __name__ == '__main__':
    app.run_server(debug=False)
