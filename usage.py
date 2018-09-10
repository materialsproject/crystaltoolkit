import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from dash.exceptions import PreventUpdate

from mp_dash_components.helpers import mp_component, sanitize_input
from mp_dash_components.layouts.structure import *
from mp_dash_components.layouts.misc import *

from monty.serialization import loadfn

app = dash.Dash()
app.title = "Materials Project Dash Component Examples"

app.scripts.config.serve_locally = True
app.config['suppress_callback_exceptions'] = True
app.css.append_css({'external_url': 'https://codepen.io/mkhorton/pen/aKmNxW.css'})

example_structure = loadfn('example_files/example_structure.json')

tab_style = {'width': '100%', 'height': '80vh',
             'border': '1px solid #d6d6d6', 'border-top': 'none',
             'box-sizing': 'border-box'}

app.layout = html.Div([
    html.Br(),
    html.Br(),
    html.Div(className='one columns'),
    html.Div([
        #html.H1('Crystal Toolkit 2.0'),
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
        ])
    ], className='seven columns'),
    html.Div([
        html.Details(
            [html.Summary(html.H4(' Load Structure', style={'display': 'inline'})),
             html.Br(),
             structure_import_from_file(structure_id='uploaded-structure', app=app)
             ],
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
            open=True
        ),
        html.Br(),
        html.Details(
            [html.Summary(html.H4(' Algorithm Options', style={'display': 'inline'})),
             html.Br(),
             structure_bonding_algorithm(structure_viewer_id='structure-viewer', app=app),
             ],
            open=True
        ),
        html.Br(),
        html.Details(
            [html.Summary(html.H4(' Transformations', style={'display': 'inline'})),
             html.Span('Not implemented yet. Coming soon!')
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
    [Input('uploaded-structure', 'children')],
    [State('json-editor-structure', 'value')]
)
def pass_structure_from_upload_to_editor(structure, current_value):
    if structure:
        return structure
    else:
        return current_value

### chain our structures together
#structure_locations = [
#    ('uploaded-structure', 'value'),
#    ('json-editor-structure', 'value')
#]
#for i in range(len(structure_locations)-1):
#    from_structure = structure_locations[i]
#    to_structure = structure_locations[i+1]
#    @app.callback(
#        Output(*to_structure),
#        [Input(*from_structure)]
#    )
#    def update_structure(structure):
#        try:
#            structure = sanitize_input(structure)
#            return dumps(structure.as_dict(verbosity=0), indent=4)
#        except:
#            raise PreventUpdate

if __name__ == '__main__':
    app.run_server(debug=True)
