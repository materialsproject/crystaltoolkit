import mp_viewer
import dash
import dash_html_components as html

app = dash.Dash('')

app.scripts.config.serve_locally = True

app.layout = html.Div([
    mp_viewer.ExampleComponent(
        id='input',
        value='my-value',
        label='my-label'
    ),
    html.Div(id='output')
])

@app.callback(
	dash.dependencies.Output('output', 'children'),
	[dash.dependencies.Input('input', 'value')])
def display_output(value):
    return 'You have entered {}'.format(value)

if __name__ == '__main__':
    app.run_server(debug=True)
