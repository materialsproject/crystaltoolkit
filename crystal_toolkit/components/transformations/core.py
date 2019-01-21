import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.components.core import PanelComponent, MPComponent
from crystal_toolkit.helpers.layouts import *


class AllTransformationsComponent(PanelComponent):

    @property
    def title(self):
        return "Transform Material 🌟"


class TransformationComponent(MPComponent):

# preview box, enable preview check, enable transformation
# store is a transformation (or None)
# options box --> kwargs

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_store("transformation_kwargs")

    @property
    def all_layouts(self):

        preview_box = []



        return {
            ''
        }

    @property
    def options_layout(self):
        return html.Div()
