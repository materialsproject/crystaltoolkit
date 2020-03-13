import dash_core_components as dcc
import dash_html_components as html

import numpy as np

from crystal_toolkit.helpers.layouts import *
from crystal_toolkit.core.mpcomponent import MPComponent
from collections import namedtuple

from typing import List, Union, Optional


def _add_label_help(input, label, help):

    contents = []
    if label and not help:
        contents.append(html.Label(label, className="mpc-label"))
    if label and help:
        contents.append(get_tooltip(html.Label(label, className="mpc-label"), help))
    contents.append(input)

    return html.Div(
        contents, style={"display": "inline-block", "padding-right": "1rem"}
    )


def get_float_input(id, label=None, default=None, help=None):

    input = dcc.Input(
        id=id,
        inputMode="numeric",
        className="input",
        style={
            "textAlign": "center",
            "width": "2rem",
            "marginRight": "0.2rem",
            "marginBottom": "0.2rem",
        },
        value=default,
    )

    return _add_label_help(input, label, help)


def get_matrix_input(
    component: MPComponent,
    for_arg_kwarg_label: Union[str, int],
    state: Optional[dict] = None,
    label: Optional[str] = None,
    help: str = None,
):
    """
    For Python classes which take matrices as inputs, this will generate
    a corresponding Dash input layout.

    :param component: The MPComponent this input will be used in.
    :param for_arg_kwarg_label: The name of the corresponding Python input,
    if arg set as the arg index (int), if a kwarg set as the kwarg name (str).
    This is used to name the component.
    :param label: A description for this input.
    :param state: Used to set state for this input, dict with arg name or kwarg name as key
    :param help: Text for a tooltip when hovering over label.
    :return: a Dash layout
    """

    default = state.get(for_arg_kwarg_label) or ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    ids = []

    shape = np.array(default).shape

    if isinstance(for_arg_kwarg_label, int):
        for_arg_kwarg_label = f"arg_{for_arg_kwarg_label}"
    elif isinstance(for_arg_kwarg_label, str):
        for_arg_kwarg_label = f"kwarg_{for_arg_kwarg_label}"

    def matrix_element(element, value=0):
        mid = f"{component.id(for_arg_kwarg_label)}_m{element}"
        ids.append(mid)
        return dcc.Input(
            id=mid,
            inputMode="numeric",
            className="input",
            style={
                "textAlign": "center",
                "width": "2rem",
                "marginRight": "0.2rem",
                "marginBottom": "0.2rem",
            },
            value=value,
        )

    matrix_contents = []

    for i in range(shape[0]):
        row = []
        for j in range(shape[1]):
            row.append(matrix_element(f"{i}{j}", value=default[i][j]))
        matrix_contents.append(html.Div(row))

    matrix = html.Div(matrix_contents)

    component._option_ids[for_arg_kwarg_label] = ids

    return _add_label_help(matrix, label, help)


def get_bool_input(id):
    raise NotImplementedError


class NumericInput(html.Div):
    """
    id will generate ...

    """


class MatrixInput(html.Div):
    """

    """


class BooleanInput(html.Div):
    """

    """


class StringInput(html.Div):
    """

    """


class DictInput(html.Div):
    """

    """


class Dropdown(html.Div):
    """
    A helper that wraps dcc.Dropdown with some additional labels and styling.
    """


class RadioItems(html.Div):
    """
    A helper that wraps dcc.RadioItems with some additional labels and styling.
    """

    def __init__(self, label=None, help=None, **kwargs):
        """
        :param label:
        :param help:
        :param kwargs: as dcc.RadioItems
        """

        super().__init__(
            children=[
                Field(
                    Control(
                        [
                            html.Label(label, className="mpc-label"),
                            dcc.RadioItems(
                                inputClassName="mpc-radio",
                                labelClassName="mpc-radio-label",
                                **kwargs,
                            ),
                        ]
                    )
                )
            ]
        )
