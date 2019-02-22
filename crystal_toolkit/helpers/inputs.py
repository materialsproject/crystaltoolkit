import dash_core_components as dcc
import dash_html_components as html

from crystal_toolkit.helpers.layouts import *

def get_float_input(id, label=None, default=None, help=None):

    input = dcc.Input(id=id, inputmode="numeric", className="input",
                             maxlength=1,
                             style={"text-align": "center", "width": "2rem",
                                    "margin-right": "0.2rem", "margin-bottom": "0.2rem"},
                             value=default)

    contents = []
    if label and not help:
        contents.append(html.Label(label, className="mpc-label"))
    if label and help:
        contents.append(get_tooltip(html.Label(label, className="mpc-label"), help))
    contents.append(input)

    return html.Div(contents, style={"display": "inline-block", "padding-right": "1rem"})
