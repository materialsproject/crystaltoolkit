import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.components.core import PanelComponent
from crystal_toolkit.helpers.layouts import *


class TransformationsComponent(PanelComponent):

    @property
    def title(self):
        return "Transform Material"
