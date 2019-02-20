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
        # for when trying to apply transformation to an actual structure,
        # needs to be connected to a structure to work
        self.create_store("error")

    @property
    def all_layouts(self):

        enable = dcc.Checklist(
            options=[{"label": "Enable transformation", "value": "enable"}],
            values=[],
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
                    Columns([Column([options], narrow=True), Column([description, html.Br(), message])])
                ),
            ],
            kind="dark",
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

    def check_input_structure(self, structure):
        """
        Implement this method if you want to check the input structure
        before attempting to apply the transformation.
        :param structure:
        :return:
        """
        pass

    def check_output_structure(self, transformed_structure):
        """
        Implement this method if you want to check the input structure
        before attempting to apply the transformation.
        :param transformed_structure:
        :return:
        """
        pass

    def _generate_callbacks(self, app, cache):


        @app.callback(
            Output(self.id(), "data"),
            [Input(self.id("transformation_args_kwargs"), "data"),
             Input(self.id("enable_transformation"), "values")]
        )
        #@cache.memoize(timeout=60*60*24,
        #               make_name=lambda x: f"{self.__class__.__name__}_{x}_cached")
        def update_transformation(args_kwargs, enabled):

            # TODO: this is madness
            if not isinstance(args_kwargs, dict):
                args_kwargs = self.from_data(args_kwargs)
            args = args_kwargs['args']
            kwargs = args_kwargs['kwargs']

            if not enabled:
                return None
            try:
                # its this part that to doesn't work(?)
                trans = self.transformation(*args, **kwargs)
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
            return html.Strong(f'Error: {transformation["error"]}')


class AllTransformationsComponent(PanelComponent):
    def __init__(self, transformations: List[TransformationComponent], *args, **kwargs):
        self.transformations = {t.__class__.__name__: t for t in transformations}
        super().__init__(*args, **kwargs)
        self.create_store("out")

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

        @app.callback(
            Output(self.id("out"), "data"),
            [Input(t.id(), "data") for t in self.transformations.values()],
            [State(self.id(), "data")]
        )
        def run_transformations(*args):

            struct = self.from_data(args[-1])
            errors = []

            transformations = []
            for transformation in args[:-1]:
                if transformation and transformation['data']:
                    transformations.append(self.from_data(transformation['data']))

            if not transformations:
                return self.to_data(struct)

            for transformation in transformations:
                try:
                    struct = transformation.apply_transformation(struct)
                except Exception as exc:
                    errors.append(f"Failed to apply transformation "
                                  f"{transformation}: {exc}")

            print("transformation errors", errors)

            return self.to_data(struct)

        # callback to take all transformations
        # and also state of which transformations are user-visible (+ their order)
        # apply them one by one with kwargs
        # external error callback(?) for each transformation, have ext error + combine with trans error
