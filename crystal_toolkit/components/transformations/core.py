import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq

import traceback

from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
from dash import no_update

from crystal_toolkit.components import StructureMoleculeComponent
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import *


from crystal_toolkit.settings import SETTINGS

from typing import List, Optional, Tuple
from itertools import chain

from json import loads

from frozendict import frozendict

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

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

        self._kwarg_type_hints = {}

        super().__init__(*args, **kwargs)
        if input_structure_component:
            self.links["input_structure"] = input_structure_component.id()

        self.create_store("input_structure")
        self.create_store(
            "transformation_args_kwargs", initial_data={"args": [], "kwargs": {}}
        )

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

        enable = daq.BooleanSwitch(
            id=self.id("enable_transformation"),
            style={"display": "inline-block", "vertical-align": "middle"},
        )

        message = html.Div(id=self.id("message"))

        description = dcc.Markdown(self.description)

        options = html.Div(self.options_layouts(), id=self.id("options"))

        preview = dcc.Loading(id=self.id("preview"))

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

    def id(self, name: str = "default", is_kwarg=False) -> Union[Dict, str]:

        if not is_kwarg:
            return super().id(name=name)

        return {"component_id": self._id, "kwarg_label": name}

    def container_layout(self, state=None, structure=None) -> html.Div:
        """
        :return: Layout defining transformation and its options.
        """

        container = MessageContainer(
            [
                MessageHeader(
                    html.Div(
                        [
                            self._sub_layouts["enable"],
                            html.Span(
                                self.title,
                                style={
                                    "vertical-align": "middle",
                                    "margin-left": "1rem",
                                },
                            ),
                        ]
                    )
                ),
                MessageBody(
                    [
                        Columns(
                            [
                                Column(
                                    [
                                        self._sub_layouts["description"],
                                        html.Br(),
                                        html.Div(
                                            self.options_layouts(
                                                state=state, structure=structure
                                            )
                                        ),
                                        html.Br(),
                                        self._sub_layouts["message"],
                                    ]
                                )
                            ]
                        )
                    ]
                ),
            ],
            kind="dark",
            id=self.id("container"),
        )

        return container

    def options_layouts(self, state=None, structure=None) -> List[html.Div]:
        """
        Return a layout to change the transformation options (that is,
        that controls the args and kwargs that will be passed to pymatgen).

        The "state" option is so that the controls can be populated appropriately
        using existing args and kwargs, e.g. when restoring the control panel
        from a previous state.

        :param state: existing state in format {"args": [], "kwargs": {}}
        :return:
        """
        return [html.Div()]

    @property
    def transformation(self):
        raise NotImplementedError

    @property
    def kwarg_type_hints(self) -> Dict:
        """
        Valid keys are a tuple for a numpy array of that shape, e.g. (3, 3) for a 3x3 matrix,
        (1, 3) for a vector, or "literal" to parse kwarg value using ast.literal_eval, or "bool"
        to parse a boolean value.

        In future iterations, we may be able to replace this with native Python type hints. The
        problem here is being able to specify array shape where appropriate.

        :return: e.g. {"scaling_matrix": (3, 3)} or {"sym_tol": "literal"}
        """
        return self._kwarg_type_hints

    @property
    def title(self):
        raise NotImplementedError

    @property
    def description(self):
        raise NotImplementedError

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

    def get_matrix_input(
        self,
        kwarg_label: str,
        state: Optional[dict] = None,
        label: Optional[str] = None,
        help_str: str = None,
        is_int: bool = False,
        shape: Tuple[int, int] = (3, 3),
        **kwargs,
    ):
        """
        For Python classes which take matrices as inputs, this will generate
        a corresponding Dash input layout.

        :param kwarg_label: The name of the corresponding Python input, this is used
        to name the component.
        :param label: A description for this input.
        :param state: Used to set state for this input, dict with arg name or kwarg name as key
        :param help_str: Text for a tooltip when hovering over label.
        :param is_int: if True, will use a numeric input
        :param shape: (3, 3) for matrix, (1, 3) for vector, (1, 1) for scalar
        :return: a Dash layout
        """

        default = state.get(kwarg_label) or np.empty(shape)
        default = np.reshape(default, shape)
        ids = []

        self._kwarg_type_hints[kwarg_label] = shape

        def matrix_element(element, value=0):
            # TODO: maybe move element out of the name
            mid = self.id(f"{kwarg_label}-{element}", is_kwarg=True)
            ids.append(mid)
            if not is_int:
                return dcc.Input(
                    id=mid,
                    inputMode="numeric",
                    className="input",
                    style={
                        "textAlign": "center",
                        # shorter default width if matrix or vector
                        "width": "2.5rem"
                        if (shape == (3, 3)) or (shape == (1, 3))
                        else "5rem",
                        "marginRight": "0.2rem",
                        "marginBottom": "0.2rem",
                    },
                    value=value,
                    persistence=True,
                    **kwargs,
                )
            else:
                return daq.NumericInput(id=mid, value=value, **kwargs)

        matrix_contents = []

        for i in range(shape[0]):
            row = []
            for j in range(shape[1]):
                row.append(matrix_element(f"{i}-{j}", value=default[i][j]))
            matrix_contents.append(html.Div(row))

        matrix = html.Div(matrix_contents)

        return add_label_help(matrix, label, help_str)

    def get_bool_input(
        self,
        kwarg_label: str,
        state: Optional[dict] = None,
        label: Optional[str] = None,
        help_str: str = None,
    ):
        """
        For Python classes which take boolean values as inputs, this will generate
        a corresponding Dash input layout.

        :param kwarg_label: The name of the corresponding Python input, this is used
        to name the component.
        :param label: A description for this input.
        :param state: Used to set state for this input, dict with arg name or kwarg name as key
        :param help_str: Text for a tooltip when hovering over label.
        :return: a Dash layout
        """

        default = state.get(kwarg_label) or False

        self._kwarg_type_hints[kwarg_label] = "bool"

        bool_input = dcc.Checklist(
            id=self.id(kwarg_label, is_kwarg=True),
            style={"width": "5rem"},
            options=[{"label": "", "value": "enabled"}],
            value=["enabled"] if default else [],
            persistence=True,
        )

        return add_label_help(bool_input, label, help_str)

    def get_choice_input(
        self,
        kwarg_label: str,
        state: Optional[dict] = None,
        label: Optional[str] = None,
        help_str: str = None,
        options: Optional[List[Dict]] = None,
    ):
        """
        For Python classes which take floats as inputs, this will generate
        a corresponding Dash input layout.

        :param kwarg_label: The name of the corresponding Python input, this is used
        to name the component.
        :param label: A description for this input.
        :param state: Used to set state for this input, dict with arg name or kwarg name as key
        :param help_str: Text for a tooltip when hovering over label.
        :param options: Options to choose from, as per dcc.Dropdown
        :return: a Dash layout
        """

        default = state.get(kwarg_label)

        self._kwarg_type_hints[kwarg_label] = "literal"

        option_input = dcc.Dropdown(
            id=self.id(kwarg_label),
            style={"width": "10rem"},
            options=options if options else [],
            value=default,
            persistence=True,
        )

        return add_label_help(option_input, label, help_str)

    def get_dict_input(
        self,
        kwarg_label: str,
        key_name: str,
        value_name: str,
        state: Optional[dict] = None,
        label: Optional[str] = None,
        help_str: str = None,
    ):
        ...

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

            # Transformation previews need to be included in layout too (see preview sublayout)
            # Transformation previews need a full transformation pipeline replica (I/O heavy)
            # Might abandon.
            warnings.warn("Transformation previews under active development.")

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
                Output({"component_id": self._id, "kwarg_label": ALL}, "disabled"),
            ],
            [Input(self.id("enable_transformation"), "on")],
            [State({"component_id": self._id, "kwarg_label": ALL}, "value")],
        )
        @cache.memoize(
            timeout=60 * 60 * 24,
            make_name=lambda x: f"{self.__class__.__name__}_{x}_cached",
        )
        def update_transformation(enabled, states):

            kwargs = {}
            for k, v in dash.callback_context.states.items():

                # TODO: hopefully this will be less hacky in future Dash versions
                # remove trailing ".value" and convert back into dictionary
                # need to sort k somehow ...

                d = loads(k[: -len(".value")])
                kwarg_label = d["kwarg_label"]

                # combine kwarg_label with element indixes, delimited by -
                # since we need multiple inputs for a single kwarg
                # TODO: remove this, explicitly store element index in id
                k_type = self.kwarg_type_hints[d["kwarg_label"].split("-")[0]]

                if isinstance(k_type, tuple):
                    # matrix or vector
                    kwarg_label, i, j = kwarg_label.split("-")
                    i = int(i)
                    j = int(j)
                    if kwarg_label not in kwargs:
                        kwargs[kwarg_label] = np.empty(k_type).tolist()
                    kwargs[kwarg_label][i][j] = literal_eval(str(v))
                    if k_type == (1, 1):
                        kwargs[kwarg_label] = kwargs[kwarg_label][0][0]

                elif k_type == "literal":
                    kwargs[kwarg_label] = literal_eval(str(v))

                elif k_type == "bool":
                    kwargs[kwarg_label] = bool("enabled" in v)

                elif k_type == "dict":
                    raise NotImplementedError

            # TODO: move callback inside AllTransformationsComponent for efficiency?

            if not enabled:
                input_state = (False,) * len(states)
                return None, "message is-dark", html.Div(), input_state
            else:
                input_state = (True,) * len(states)

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
                    input_state,
                )

            else:

                return trans, "message is-success", html.Div(), input_state


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
            persistence=True,
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
            [
                Input(self.id("choices"), "value"),
                Input(self.id("input_structure"), "data"),
            ],
            [State(t.id(), "data") for t in self.transformations.values()],
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
