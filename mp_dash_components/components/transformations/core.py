import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from mp_dash_components.components.core import PanelComponent
from mp_dash_components.helpers.layouts import *


class TransformationsComponent(PanelComponent):

    @property
    def title(self):
        return "Transform Material"
