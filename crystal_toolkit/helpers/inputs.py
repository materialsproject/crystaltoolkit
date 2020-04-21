import dash_core_components as dcc
import dash_html_components as html

import numpy as np

from crystal_toolkit.helpers.layouts import *
from crystal_toolkit.core.mpcomponent import MPComponent
from collections import namedtuple

from typing import List, Union, Optional, Tuple


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
