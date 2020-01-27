import dash_core_components as dcc
import dash_html_components as html

import numpy as np

from crystal_toolkit.helpers.layouts import *

from collections import namedtuple


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
            "text-align": "center",
            "width": "2rem",
            "margin-right": "0.2rem",
            "margin-bottom": "0.2rem",
        },
        value=default,
    )

    return _add_label_help(input, label, help)


def get_matrix_input(
    id, label=None, default=((1, 0, 0), (0, 1, 0), (0, 0, 1)), help=None
):

    shape = np.array(default).shape

    def matrix_element(element, value=0):
        return dcc.Input(
            id=f"{id}_m{element}",
            inputMode="numeric",
            min=0,
            max=9,
            step=1,
            className="input",
            maxLength=1,
            style={
                "text-align": "center",
                "width": "2rem",
                "margin-right": "0.2rem",
                "margin-bottom": "0.2rem",
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
