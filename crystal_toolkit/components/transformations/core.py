import dash
import dash_core_components as dcc
import dash_html_components as html

import traceback

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import no_update

from crystal_toolkit.components import StructureMoleculeComponent
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import *

from typing import List

import flask


class TransformationComponent(MPComponent):
    def __init__(self, input_structure: MPComponent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_structure = input_structure
        self.create_store(
            "transformation_args_kwargs", initial_data={"args": [], "kwargs": {}}
        )

    @property
    def _sub_layouts(self):

        enable = dcc.Checklist(
            options=[{"label": "Enable transformation", "value": "enable"}],
            value=["enable"],
            inputClassName="mpc-radio",
            id=self.id("enable_transformation"),
        )

        message = html.Div(id=self.id("message"))

        description = dcc.Markdown(self.description)

        options = html.Div(self.options_layout(), id=self.id("options"))

        preview = html.Div(id=self.id("preview"))

        container = MessageContainer(
            [
                MessageHeader([self.title, enable]),
                MessageBody(
                    Columns(
                        [
                            Column([options], narrow=True),
                            Column(
                                [description, html.Br(), message, html.Br(), preview]
                            ),
                        ]
                    )
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

    def container_layout(self) -> html.Div:
        """
        :return: Layout defining transformation and its options.
        """
        return self._sub_layouts["container"]

    def options_layout(self):
        return html.Div()

    @property
    def transformation(self):
        raise NotImplementedError

    @property
    def title(self):
        raise NotImplementedError

    @property
    def description(self):
        raise NotImplementedError

    def generate_callbacks(self, app, cache):
        @app.callback(
            [
                Output(self.id(), "data"),
                Output(self.id("container"), "className"),
                Output(self.id("message"), "children"),
            ],
            [
                Input(self.id("transformation_args_kwargs"), "data"),
                Input(self.id("enable_transformation"), "value"),
            ],
        )
        @cache.memoize(
            timeout=60 * 60 * 24,
            make_name=lambda x: f"{self.__class__.__name__}_{x}_cached",
        )
        def update_transformation(args_kwargs, enabled):

            # TODO: move callback inside AllTransformationsComponent for efficiency

            if "enable" not in enabled:
                return None, "message is-dark", html.Div()

            try:
                trans = self.transformation(
                    *args_kwargs["args"], **args_kwargs["kwargs"]
                )
                error = None
            except Exception as exception:
                trans = None
                error = str(exception)

            if error:

                return trans, "message is-warning", html.Strong(f"Error: {error}")

            else:

                return trans, "message is-success", html.Div()


class AllTransformationsComponent(MPComponent):
    def __init__(
        self, transformations: List[str], input_structure: MPComponent, *args, **kwargs
    ):

        subclasses = TransformationComponent.__subclasses__()
        subclass_names = [s.__name__ for s in subclasses]
        for name in transformations:
            if name not in subclass_names:
                warnings.warn(
                    f'Unknown transformation "{name}", choose from: {", ".join(subclass_names)}'
                )

        transformations = [t for t in subclasses if t.__name__ in transformations]
        transformations = [t(input_structure=input_structure) for t in transformations]

        self.transformations = {t.__class__.__name__: t for t in transformations}
        self.input_structure = input_structure
        super().__init__(*args, **kwargs)

    @property
    def _sub_layouts(self):
        layouts = super()._sub_layouts

        all_transformations = html.Div(
            [
                transformation.container_layout()
                for name, transformation in self.transformations.items()
            ]
        )

        choices = dcc.Dropdown(
            options=[
                {"label": transformation.title, "value": name}
                for name, transformation in self.transformations.items()
            ],
            multi=True,
            value=[],
            placeholder="Select one or more transformations...",
            id=self.id("choices"),
            style={"max-width": "65vmin"},
        )

        layouts.update({"all_transformations": all_transformations, "choices": choices})

        return layouts

    def layout(self):

        return html.Div(
            [
                html.Div(
                    "Transform your crystal structure using the power of pymatgen.",
                    className="mpc-panel-description",
                ),
                self._sub_layouts["choices"],
                html.Br(),
                html.Div(id=self.id("error")),
                html.Div(id=self.id("transformation_options")),
            ]
        )

    def generate_callbacks(self, app, cache):
        @cache.memoize()
        def apply_transformation(transformation_data, struct):

            transformation = self.from_data(transformation_data)
            error = None

            try:
                struct = transformation.apply_transformation(struct)
            except Exception as exc:
                error_title = (
                    f'Failed to apply "{transformation.__class__.__name__}" '
                    f"transformation: {exc}"
                )
                traceback_info = Reveal(
                    title=html.B("Traceback"),
                    children=[dcc.Markdown(traceback.format_exc())],
                )
                error = [error_title, traceback_info]

            return struct, error

        @app.callback(
            Output(self.id("transformation_options"), "children"),
            [Input(self.id("choices"), "value")],
        )
        def show_transformation_options(values):

            values = values or []

            transformation_options = html.Div(
                [self.transformations[name].container_layout() for name in values]
            )

            return [transformation_options]

        @app.callback(
            [Output(self.id(), "data"), Output(self.id("error"), "children")],
            [Input(t.id(), "data") for t in self.transformations.values()]
            + [
                Input(self.input_structure.id(), "data"),
                Input(self.id("choices"), "value"),
            ],
        )
        def run_transformations(*args):

            # do not update if we don't have a Structure to transform
            if not args[-2]:
                raise PreventUpdate

            user_visible_transformations = args[-1]
            struct = self.from_data(args[-2])

            errors = []

            transformations = []
            for transformation in args[:-2]:
                if transformation:
                    transformations.append(transformation)

            if not transformations:
                return struct, html.Div()

            for transformation_data in transformations:

                # following our naming convention, only apply transformations
                # that are user visible
                # TODO: this should be changed
                if (
                    f"{transformation_data['@class']}Component"
                    in user_visible_transformations
                ):

                    struct, error = apply_transformation(transformation_data, struct)

                    if error:
                        errors += error

            if not errors:
                error_msg = html.Div()
            else:
                errors = [
                    dcc.Markdown(
                        "Crystal Toolkit encountered an error when trying to "
                        "applying your chosen transformations. This is usually "
                        "because either the input crystal structure is not "
                        "suitable for the transformation, or the choice of "
                        "transformation settings is not appropriate. Consult "
                        "the pymatgen documentation for more information.  \n"
                        ""
                        "If you think this is a bug please report it.  \n"
                        ""
                    )
                ] + errors
                error_msg = html.Div(
                    [
                        MessageContainer(
                            [
                                MessageHeader("Error applying transformations"),
                                MessageBody(errors),
                            ],
                            kind="danger",
                        ),
                        html.Br(),
                    ]
                )

            return struct, error_msg

        # callback to take all transformations
        # and also state of which transformations are user-visible (+ their order)
        # apply them one by one with kwargs
        # external error callback(?) for each transformation, have ext error + combine with trans error
