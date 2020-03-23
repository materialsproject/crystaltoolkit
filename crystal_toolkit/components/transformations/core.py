import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq

import traceback

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import no_update

from crystal_toolkit.components import StructureMoleculeComponent
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import *

from crystal_toolkit.settings import SETTINGS

from typing import List, Optional
from itertools import chain

from ast import literal_eval

import flask
import numpy as np


class TransformationComponent(MPComponent):
    def __init__(
        self, input_structure_component: Optional[MPComponent] = None, *args, **kwargs
    ):

        if self.__class__.__name__ != f"{self.transformation.__name__}Component":
            # sanity check, enforcing conventions
            raise NameError(
                f"Class has to be named corresponding to the underlying "
                f"transformation name: {self.transformation.__name__}Component"
            )

        super().__init__(*args, **kwargs)
        if input_structure_component:
            self.links["input_structure"] = input_structure_component.id()

        self.create_store("input_structure")
        self.create_store(
            "transformation_args_kwargs", initial_data={"args": [], "kwargs": {}}
        )
        self._option_ids = {}

    @property
    def is_one_to_many(self) -> bool:
        """
        This should reflect the underlying transformation.
        """
        # need to initialize transformation to access property, which isn't
        # possible in all cases without necessary kwargs, which is why
        # we duplicate the property here
        return False

    @property
    def _sub_layouts(self):

        enable = daq.BooleanSwitch(id=self.id("enable_transformation"))

        message = html.Div(id=self.id("message"))

        description = dcc.Markdown(self.description)

        options = html.Div(self.options_layout(), id=self.id("options"))

        preview = html.Div(["Preview", dcc.Loading(id=self.id("preview"))])

        if self.is_one_to_many:
            ranked_list = daq.NumericInput(
                value=1, min=1, max=10, id=self.id("ranked_list")
            )
        else:
            # if not 1-to-many, we don't need the control, we keep
            # an empty container here to make the callbacks simpler
            # since "ranked_list" will then always be present in layout
            ranked_list = html.Div(id=self.id("ranked_list"))

        return {
            "options": options,
            "description": description,
            "enable": enable,
            "message": message,
            "preview": preview,
            "ranked_list": ranked_list,
        }

    def container_layout(self, state=None, structure=None) -> html.Div:
        """
        :return: Layout defining transformation and its options.
        """

        container = MessageContainer(
            [
                MessageHeader([self.title, self._sub_layouts["enable"]]),
                MessageBody(
                    Columns(
                        [
                            Column([self.options_layout(state=state)], narrow=True),
                            Column(
                                [
                                    self._sub_layouts["description"],
                                    html.Br(),
                                    self._sub_layouts["message"],
                                    html.Br(),
                                    self._sub_layouts["preview"],
                                ]
                            ),
                        ]
                    )
                ),
            ],
            kind="dark",
            id=self.id("container"),
        )

        return container

    def options_layout(self, state=None):
        """
        Return a layout to change the transformation options (that is,
        that controls the args and kwargs that will be passed to pymatgen).

        The "state" option is so that the controls can be populated appropriately
        using existing args and kwargs, e.g. when restoring the control panel
        from a previous state.

        :param state: existing state in format {"args": [], "kwargs": {}}
        :return:
        """
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

    @property
    def option_ids(self) -> List[str]:
        """
        If set, these controls will have their user inputs disabled
        when the transformation is enabled, essentially "freezing"
        the transformation options. This can help prevent latency
        due to users changing transformation options while transformations
        are updating.

        :return: List of names of option controls
        """
        return list(chain.from_iterable(self._option_ids.values()))

    def get_preview_layout(self, struct_in, struct_out):
        """
        Override this method to give a layout that previews the transformation.
        Has beneficial side effect of priming the transformation cache when
        entire transformation pipeline is enabled.

        :param struct_in: input Structure
        :param struct_out: transformed Structure
        :return:
        """
        return html.Div()

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

        if SETTINGS.TRANSFORMATION_PREVIEWS:

            @app.callback(
                Output(self.id("preview"), "children"),
                [Input(self.id(), "data"), Input(self.id("input_structure"), "data")],
            )
            def update_preview(transformation_data, input_structure):
                if (not transformation_data) or (not input_structure):
                    return html.Div()
                input_structure = self.from_data(input_structure)
                output_structure, error = apply_transformation(
                    transformation_data, input_structure
                )
                if len(output_structure) > 64:
                    warning = html.Span(
                        f"The transformed crystal structure has {len(output_structure)} atoms "
                        f"and might take a moment to display."
                    )
                return self.get_preview_layout(input_structure, output_structure)

        @app.callback(
            [
                Output(self.id(), "data"),
                Output(self.id("container"), "className"),
                Output(self.id("message"), "children"),
            ]
            + [Output(option, "disabled") for option in self.option_ids],
            [Input(self.id("enable_transformation"), "on")],
            [State(option_id, "value") for option_id in self.option_ids],
        )
        @cache.memoize(
            timeout=60 * 60 * 24,
            make_name=lambda x: f"{self.__class__.__name__}_{x}_cached",
        )
        def update_transformation(enabled, *args):

            state = dash.callback_context.states
            kwargs = {}
            for k, v in state.items():
                # examples of strings being parsed:
                # ...kwarg-supercell-matrix-00
                # ...kwarg-some_option-bool-0
                k = k.split("kwarg")[1]
                k = k.split("-")[1:]
                kwarg_name = k[0]
                k_type = k[1]
                if k_type == "matrix":
                    i = int(k[2][0])
                    j = int(k[2][1])
                    if kwarg_name not in kwargs:
                        kwargs[kwarg_name] = np.empty((3, 3)).tolist()
                    kwargs[kwarg_name][i][j] = v
                elif k_type == "bool":
                    kwargs[kwarg_name] = bool(v)

            # TODO: move callback inside AllTransformationsComponent for efficiency?

            if not enabled:
                input_state = (False,) * len(self.option_ids)
                return (None, "message is-dark", html.Div(), *input_state)
            else:
                input_state = (True,) * len(self.option_ids)

            try:
                trans = self.transformation(**kwargs)
                error = None
            except Exception as exception:
                trans = None
                error = str(exception)

            if error:

                return (
                    trans,
                    "message is-warning",
                    html.Strong(f"Error: {error}"),
                    *input_state,
                )

            else:

                return (trans, "message is-success", html.Div(), *input_state)


class AllTransformationsComponent(MPComponent):
    def __init__(
        self,
        transformations: List[str],
        input_structure_component: Optional[MPComponent] = None,
        *args,
        **kwargs,
    ):

        subclasses = TransformationComponent.__subclasses__()
        subclass_names = [s.__name__ for s in subclasses]
        for name in transformations:
            if name not in subclass_names:
                warnings.warn(
                    f'Unknown transformation "{name}", choose from: {", ".join(subclass_names)}'
                )

        transformations = [t for t in subclasses if t.__name__ in transformations]

        super().__init__(*args, **kwargs)

        if input_structure_component:
            self.links["input_structure"] = input_structure_component.id()
        self.create_store("input_structure")

        transformations = [t(input_structure_component=self) for t in transformations]
        self.transformations = {t.__class__.__name__: t for t in transformations}

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
            [State(self.id("input_structure"), "data")]
            + [State(t.id(), "data") for t in self.transformations.values()],
        )
        def show_transformation_options(values, structure, *args):

            values = values or []

            structure = self.from_data(structure)

            transformation_options = html.Div(
                [
                    self.transformations[name].container_layout(
                        state=state, structure=structure
                    )
                    for name, state in zip(values, args)
                ]
            )

            return [transformation_options]

        @app.callback(
            [Output(self.id(), "data"), Output(self.id("error"), "children")],
            [Input(t.id(), "data") for t in self.transformations.values()]
            + [
                Input(self.id("input_structure"), "data"),
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
