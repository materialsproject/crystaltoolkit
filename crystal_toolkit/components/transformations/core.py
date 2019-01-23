import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from crystal_toolkit.components.core import PanelComponent, MPComponent
from crystal_toolkit.helpers.layouts import *

from typing import List


class TransformationComponent(MPComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_store(
            "transformation_args_kwargs", initial_data={"args": [], "kwargs": {}}
        )

    @property
    def all_layouts(self):

        enable = dcc.Checklist(
            options=[{"label": "Enable transformation", "value": "enable"}],
            values=["enable"],
            inputClassName="mpc-radio",
            id=self.id("enable_transformation"),
        )

        message = html.Div(id=self.id("message"))

        description = dcc.Markdown(self.description)

        options = html.Div(self.options_layout, id=self.id("options"))

        container = MessageContainer(
            [
                MessageHeader([self.title, enable]),
                MessageBody(
                    Columns([Column([description, html.Br(), message]), Column([options], narrow=True)])
                ),
            ],
            kind="success",
            id=self.id("container"),
        )

        return {
            "options": options,
            "description": description,
            "enable": enable,
            "message": message,
            "container": container,
        }

    @property
    def options_layout(self):
        raise NotImplementedError

    @property
    def transformation(self):
        raise NotImplementedError

    @property
    def title(self):
        raise NotImplementedError

    @property
    def description(self):
        raise NotImplementedError

    def _generate_callbacks(self, app, cache):

        @app.callback(
            Output(self.id(), "data"),
            [Input(self.id("transformation_args_kwargs"), "data"),
             Input(self.id("enable_transformation"), "values")]
        )
        @cache.memoize(timeout=60*60*24,
                       make_name=lambda x: f"{self.__class__.__name__}_{x}_cached")
        def update_transformation(args_kwargs, enabled):
            if not enabled:
                return None
            try:
                trans = self.transformation(*args_kwargs['args'], **args_kwargs['kwargs'])
                data = self.to_data(trans)
                error = None
            except Exception as exception:
                data = None
                error = str(exception)
            return {'data': data, 'error': error}

        @app.callback(
            Output(self.id("container"), "className"),
            [Input(self.id(), "data")]
        )
        def update_transformation_style(transformation):
            if not transformation:
                return "message is-dark"
            elif transformation["error"]:
                return "message is-warning"
            else:
                return "message is-success"


        @app.callback(
            Output(self.id("message"), "children"),
            [Input(self.id(), "data")]
        )
        def update_transformation_style(transformation):
            if not transformation or not transformation["error"]:
                raise PreventUpdate
            return f'Error: {transformation["error"]}'



class AllTransformationsComponent(PanelComponent):
    def __init__(self, transformations: List[TransformationComponent], *args, **kwargs):
        self.transformations = {t.__class__.__name__: t for t in transformations}
        super().__init__(*args, **kwargs)

    @property
    def title(self):
        return "Transform Material 🌟"

    @property
    def description(self):
        return "Transform your crystal structure using the power of pymatgen transformations."

    @property
    def all_layouts(self):
        layouts = super().all_layouts

        all_transformations = html.Div(
            [
                transformation.container_layout
                for name, transformation in self.transformations.items()
            ]
        )

        choices = dcc.Dropdown(
            options=[{"label": transformation.title, "value": name} for name, transformation in
                     self.transformations.items()],
            multi=True,
            value=[],
            placeholder="Select one or more transformations...",
            id=self.id("choices"),
        )

        layouts.update({
            "all_transformations": all_transformations,
            "choices": choices
        })

        return layouts

    def update_contents(self, new_store_contents):

        return html.Div([
            self.choices_layout,
            html.Br(),
            html.Div(id=self.id("transformation_options"))
        ])

    def _generate_callbacks(self, app, cache):

        super()._generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("transformation_options"), "children"),
            [Input(self.id("choices"), "value")]
        )
        def show_transformation_options(values):

            values = values or []

            transformation_options = html.Div([
                self.transformations[name].container_layout for
                name in values
            ])

            hidden_transformations = html.Div([
                transformation.container_layout
                for name, transformation in self.transformations.items()
                if name not in values
            ], style={"display": "none"})

            return [transformation_options, hidden_transformations]
