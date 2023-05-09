from __future__ import annotations

import random

import dash
from dash import Input, Output, dcc, html
from dash.exceptions import PreventUpdate

import crystal_toolkit.components as ctc
import crystal_toolkit.helpers.layouts as ctl
from crystal_toolkit.settings import SETTINGS

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

your_component = ctc.MPComponent(id="example")

bool_input = your_component.get_bool_input(
    kwarg_label="bool_example",
    default=False,
    label="Example Boolean Input",
    help_str="This can explain to the user what this boolean input controls.",
)

matrix_input = your_component.get_numerical_input(
    kwarg_label="matrix_example",
    default=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    shape=(3, 3),
    label="Example Matrix Input",
    help_str="This can explain to the user what this slider input controls.",
)

slider_input = your_component.get_slider_input(
    kwarg_label="slider_example",
    default=2.0,
    label="Example Slider Input",
    help_str="This can explain to the user what this slider input controls.",
)

# create your layout
my_layout = ctl.Section(
    [
        ctl.H1("Example of input controls"),
        dcc.Markdown(
            "These examples are intended for people developing their own `MPComponent`."
        ),
        ctl.H2("Boolean input"),
        bool_input,
        ctl.H2("Matrix input"),
        matrix_input,
        ctl.H2("Slider input"),
        slider_input,
        ctl.H2("Dynamic inputs"),
        ctl.Button("Generate inputs", id="generate-inputs"),
        html.Div(id="dynamic-inputs"),
        ctl.H1("Output"),
        html.Span(id="output"),
    ]
)


@app.callback(
    Output("output", "children"), Input(your_component.get_all_kwargs_id(), "value")
)
def show_outputs(*args):
    """Reconstruct the kwargs from the state of the component and display them as string."""
    kwargs = your_component.reconstruct_kwargs_from_state()

    return str(kwargs)


@app.callback(
    Output("dynamic-inputs", "children"), Input("generate-inputs", "n_clicks")
)
def add_inputs(n_clicks):
    """Add a slider input with random initial value to the layout."""
    if not n_clicks:
        raise PreventUpdate

    element = random.choice(["Li", "Na", "K"])
    return your_component.get_slider_input(
        kwarg_label=f"slider_{element}",
        default=random.uniform(0, 1),
        label=f"{element} Slider Input",
        help_str="This can explain to the user what this slider input controls.",
    )


# tell Crystal Toolkit about the app and layout we want to display
ctc.register_crystal_toolkit(app=app, layout=my_layout, cache=None)

# run this app with "python path/to/this/file.py"
# in production, deploy behind gunicorn or similar
# see Dash docs for more info
if __name__ == "__main__":
    app.run(debug=True, port=8050)
