from __future__ import annotations

import logging
from abc import ABC
from ast import literal_eval
from base64 import b64encode
from collections import defaultdict
from itertools import chain
from json import JSONDecodeError, dumps, loads
from typing import Any, Literal

import dash
import dash_mp_components as mpc
import numpy as np
import plotly.graph_objects as go
from dash import dash_table as dt
from dash import dcc, html
from dash.dependencies import ALL
from flask_caching import Cache
from monty.json import MontyDecoder, MSONable

from crystal_toolkit import __version__ as ct_version
from crystal_toolkit.helpers.layouts import Button, Icon, Loading, add_label_help
from crystal_toolkit.settings import SETTINGS

# fallback cache if Redis etc. isn't set up
null_cache = Cache(config={"CACHE_TYPE": "null"})

# Crystal Toolkit namespace, added to the start of all ids
# so we can see which layouts have been added by Crystal Toolkit
CT_NAMESPACE = "CT"


class MPComponent(ABC):
    """The abstract base class for an MPComponent.

    MPComponent is designed to help render an MSONable object.
    """

    # reference to global Dash app
    app = None

    # reference to Flask cache
    cache = None

    # used to track all dcc.Stores required for all MPComponents to work
    # keyed by the MPComponent id
    _app_stores_dict: dict[str, list[dcc.Store]] = defaultdict(list)

    # used to track what individual Dash components are defined
    # by this MPComponent
    _all_id_basenames: set[str] = set()

    # used to defer generation of callbacks until app.layout defined
    # can be helpful to callback exceptions retained
    _callbacks_to_generate: set[MPComponent] = set()

    @staticmethod
    def register_app(app: dash.Dash):
        """This method must be called at least once in your Crystal Toolkit Dash app if you want to
        enable interactivity with the MPComponents. The "app" variable is a special global variable
        used by Dash/Flask, and registering it with MPComponent allows callbacks to be registered
        with the app on instantiation.

        Args:
            app: a Dash app instance
        """
        MPComponent.app = app
        # add metadata
        app.config.meta_tags.append(
            {
                "name": "generator",
                "content": f"Crystal Toolkit {ct_version} (Materials Project)",
            }
        )
        # set default title, but respect the user if they override it
        if app.title == "Dash":
            app.title = "Crystal Toolkit"

    @staticmethod
    def register_cache(cache: Cache) -> None:
        """This method must be called at least once in your Crystal Toolkit Dash app if you want to
        enable callback caching. Callback caching is one of the easiest ways to see significant
        performance improvements, especially for callbacks that are computationally expensive.

        Args:
            cache: a flask_caching Cache instance
        """
        if SETTINGS.DEBUG_MODE:
            cache = null_cache
        elif cache:
            MPComponent.cache = cache
        else:
            MPComponent.cache = Cache(
                MPComponent.app.server, config={"CACHE_TYPE": "simple"}
            )

    @staticmethod
    def crystal_toolkit_layout(layout: html.Div) -> html.Div:

        if not MPComponent.app:
            raise ValueError(
                "Please register the Dash app with Crystal Toolkit using register_app()."
            )

        # layout_str = str(layout)
        stores_to_add = []
        for basename in MPComponent._all_id_basenames:
            # can use "if basename in layout_str:" to restrict to components present in initial layout
            # this would cause bugs for components displayed dynamically
            stores_to_add += MPComponent._app_stores_dict[basename]
        layout.children += stores_to_add

        # set app.layout to layout so that callbacks can be validated
        MPComponent.app.layout = layout

        for component in MPComponent._callbacks_to_generate:
            component.generate_callbacks(MPComponent.app, MPComponent.cache)

        return layout

    @staticmethod
    def register_crystal_toolkit(app, layout, cache=None):

        MPComponent.register_app(app)
        MPComponent.register_cache(cache)
        app.config["suppress_callback_exceptions"] = True
        app.layout = MPComponent.crystal_toolkit_layout(layout)

    @staticmethod
    def all_app_stores() -> html.Div:
        """This must be included somewhere in your Crystal Toolkit Dash app's layout for
        interactivity to work. This is a hidden element that contains the MSON for each MPComponent.

        Returns: a html.Div Dash Layout
        """
        return html.Div(
            list(chain.from_iterable(MPComponent._app_stores_dict.values()))
        )

    def __init__(
        self,
        default_data: MSONable | dict | str | None = None,
        id: str | None = None,
        links: dict[str, str] | None = None,
        storage_type: Literal["memory", "local", "session"] = "memory",
        disable_callbacks: bool = False,
    ):
        """The abstract base class for an MPComponent.

        The MPComponent is designed to help render any MSONable object,
        for example many of the objects in pymatgen (Structure, PhaseDiagram, etc.)

        To instantiate an MPComponent, you will need to create it outside
        of your Dash app layout:

        my_component = MPComponent(my_msonable_object)

        Then, inside the app.layout, you can include the component's layout
        anywhere you choose: my_component.layout

        If you want the layouts to be interactive, i.e. to respond to callbacks,
        you have to also use the MPComponent.register_app(app) method in your app,
        and also include MPComponent.all_app_stores in your app.layout (an
        invisible layout that contains the MSON itself).

        If you do not want the layouts to be interactive, set disable_callbacks
        to True to prevent errors.

        If including multiple MPComponents of the same type, make sure
        to set the id field to a unique value, as you would in any other
        Dash component.

        When sub-classing MPComponent, the most important methods to implement
        are _sub_layouts and generate_callbacks().

        Args:
            default_data: initial contents for the component, can be None
            id: a unique id, required if multiple of the same type of
            MPComponent are included in an app
            links: if set, will set store contents from the stores of another
            component to reduce unnecessary callbacks and duplication of data,
            note that links are one directional only and specific the origin
            stores, e.g. set {"default": my_other_component.id()} to fill this
            component's default store contents from the other component's default store,
            or {"graph": my_other_component.id("graph")} to fill this component's
            "graph" store from another component's "graph" store
            storage_type: whether to persist contents of component through
            browser refresh or browser sessions, use with caution, defaults
            to "memory" so component store will be emptied on refresh, see
            dcc.Store documentation for more information
            disable_callbacks: if True, will not generate callbacks, useful
            for static layouts or returning new MPComponents dynamically where
            generating callbacks are not possible due to limitations of Dash
        """

        # ensure ids are unique
        # Note: shadowing Python built-in here, but only because Dash does it...
        # TODO: do something else here
        if id is None:
            # TODO: this could lead to duplicate ids and an error, but if
            # setting random ids, this could also lead to undefined behavior
            id = f"{CT_NAMESPACE}{type(self).__name__}"
        elif not id.startswith(CT_NAMESPACE):
            id = f"{CT_NAMESPACE}{id}"
        MPComponent._all_id_basenames.add(id)

        self._id = id
        self._all_ids: set[str] = set()
        self._stores = {}
        self._initial_data = {}

        self.links = links or {}

        self.create_store(
            name="default", initial_data=default_data, storage_type=storage_type
        )
        self.links["default"] = self.id()

        if not disable_callbacks:
            # callbacks generated as final step by crystal_toolkit_layout()
            self._callbacks_to_generate.add(self)

        self.logger = logging.getLogger(type(self).__name__)

    def id(
        self,
        name: str = "default",
        is_kwarg: bool = False,
        idx=False,
        hint=None,
        is_store: bool = False,
    ) -> str | dict[str, str]:
        """Generate an id from a name combined with the base id of the MPComponent itself, useful
        for generating ids of individual components in the layout.

        In the special case of the id of an element that is used to re-construct
        a keyword argument for a specific class, it will store information necessary
        to reconstruct that keyword argument (e.g. its type hint and, in the case of
        a vector or matrix, the corresponding index).

        A hint could be a tuple for a numpy array of that shape, e.g. (3, 3) for a 3x3 matrix,
        (1, 3) for a vector, or "literal" to parse kwarg value using ast.literal_eval, or "bool"
        to parse a boolean value. In future iterations, we may be able to replace this with native
        Python type hints. The problem here is being able to specify array shape where appropriate.


        Args:
            name: e.g. "default"

        Returns: e.g. "MPComponent_default"
        """

        if name in self._stores:
            is_store = True

        if is_kwarg:
            return {
                "component_id": self._id,
                "kwarg_label": name,
                "idx": str(idx),
                "hint": str(hint),
            }

        # if we're linking to another component, return that id
        if name in self.links:
            return self.links[name]

        # otherwise create a new id
        self._all_ids.add(name)
        if name != "default":
            name = f"{self._id}_{name}"
        else:
            name = f"{self._id}"
        return name
        if is_store:
            return name
        else:
            return {"id": name}

    def create_store(
        self,
        name: str,
        initial_data: MSONable | dict | str | None = None,
        storage_type: Literal["memory", "local", "session"] = "memory",
        debug_clear: bool = False,
    ) -> None:
        """Generate a dcc.Store to hold something (MSONable object, Dict or string), and register it
        so that it will be included in the Dash app automatically.

        The initial data will be stored in a class attribute as
        self._initial_data[name].

        Args:
            name: name for the store
            initial_data: initial data to include
            storage_type: as in dcc.Store
            debug_clear: set to True to empty the store if using
            persistent storage
        """

        # if we're linking to another component, do not create a new store
        if name in self.links:
            return

        store = dcc.Store(
            id=self.id(name, is_store=True),
            data=initial_data,
            storage_type=storage_type,
            clear_data=debug_clear,
        )
        self._stores[name] = store
        self._initial_data[name] = initial_data
        MPComponent._app_stores_dict[self.id()].append(store)

    @property
    def initial_data(self) -> dict[str, Any]:
        """
        :return: Initial data for all the stores defined by component,
        keyed by store name.
        """
        return self._initial_data

    @staticmethod
    def from_data(data: dict[str, Any]) -> MPComponent:
        """Converts the contents of a dcc.Store back into a Python object.

        :param data: contents of a dcc.Store created by to_data
        :return: a Python object
        """
        return loads(dumps(data), cls=MontyDecoder)

    @property
    def all_stores(self) -> list[str]:
        """
        :return: List of all store ids generated by this component
        """
        return list(self._stores)

    @property
    def all_ids(self) -> list[str]:
        """
        :return: List of all ids generated by this component
        """
        return list(
            component_id
            for component_id in self._all_ids
            if component_id not in self.all_stores
        )

    def __repr__(self) -> str:
        return f"{self.id()}<{type(self).__name__}>"

    def __str__(self) -> str:
        ids = "\n".join(
            [f"* {component_id}  " for component_id in sorted(self.all_ids)]
        )
        stores = "\n".join([f"* {store}  " for store in sorted(self.all_stores)])
        layouts = "\n".join([f"* {layout}  " for layout in sorted(self._sub_layouts)])

        return f"""{self.id()}<{type(self).__name__}>  \n
IDs:  \n{ids}  \n
Stores:  \n{stores}  \n
Sub-layouts:  \n{layouts}"""

    @property
    def _sub_layouts(self) -> dict[str, dash.development.base_component.Component]:
        """Layouts associated with this component, available for book-keeping if your component is
        complex, so that the layout() method is just assembles individual sub-layouts.

        :return: A dictionary with names of layouts as keys (str) and Dash
        layouts (e.g. html.Div) as values.
        """
        return {}

    def layout(self) -> html.Div:
        """
        :return: A Dash layout for the full component. Basic implementation
        provided, but should in general be overridden.
        """
        return html.Div(list(self._sub_layouts.values()))

    def generate_callbacks(self, app, cache) -> None:
        """Generate all callbacks associated with the layouts in this app.

        Assume that "suppress_callback_exceptions" is True, since it is not always guaranteed that
        all layouts will be displayed to the end user at all times, but it's important the callbacks
        are defined on the server.
        """
        return None

    def get_numerical_input(
        self,
        kwarg_label: str,
        default: int | float | list | None = None,
        state: dict | None = None,
        label: str | None = None,
        help_str: str = None,
        is_int: bool = False,
        shape: tuple[int, ...] = (),
        **kwargs,
    ) -> html.Div:
        """For Python classes which take matrices as inputs, this will generate a corresponding Dash
        input layout.

        :param kwarg_label: The name of the corresponding Python input, this is used
        to name the component.
        :param label: A description for this input.
        :param default: A default value for this input.
        :param state: Used to set default state for this input, use a dict with the kwarg_label as a key
        and the default value as a value. Ignored if `default` is set. It can be useful to use
        `state` if you want to set defaults for multiple inputs from a single dictionary.
        :param help_str: Text for a tooltip when hovering over label.
        :param is_int: if True, will use a numeric input
        :param shape: (3, 3) for matrix, (1, 3) for vector, (1, 1) for scalar
        :return: a Dash layout
        """

        state = state or {}
        default = np.full(shape, default or state.get(kwarg_label))
        default = np.reshape(default, shape)

        style = {
            "textAlign": "center",
            # shorter default width if matrix or vector
            "width": "5rem",
            "marginRight": "0.2rem",
            "marginBottom": "0.2rem",
            "height": "36px",
        }
        if "style" in kwargs:
            style.update(kwargs["style"])
            del kwargs["style"]

        def matrix_element(idx, value=0):
            # TODO: maybe move element out of the name
            mid = self.id(kwarg_label, is_kwarg=True, idx=idx, hint=shape)
            if isinstance(value, np.ndarray):
                value = value.item()
            if not is_int:
                return dcc.Input(
                    id=mid,
                    inputMode="numeric",
                    debounce=True,
                    className="input",
                    style=style,
                    value=float(value) if value is not None else None,
                    persistence=True,
                    type="number",
                    **kwargs,
                )
            else:
                return dcc.Input(
                    id=mid,
                    inputMode="numeric",
                    debounce=True,
                    className="input",
                    style=style,
                    value=int(value) if value is not None else None,
                    persistence=True,
                    type="number",
                    step=1,
                    **kwargs,
                )

        # dict of row indices, column indices to element
        matrix_contents = defaultdict(dict)

        # determine what individual input boxes we need
        # note that shape = () for floats, shape = (3,) for vectors
        # but we may also need to accept input for e.g. (3, 1)
        it = np.nditer(default, flags=["multi_index", "refs_ok"])
        while not it.finished:
            idx = it.multi_index
            row = (idx[1] if len(idx) > 1 else 0,)
            column = idx[0] if len(idx) > 0 else 0
            matrix_contents[row][column] = matrix_element(idx, value=it[0])
            it.iternext()

        # arrange the input boxes in two dimensions (rows, columns)
        matrix_div_contents = []
        print("matrix_contents", matrix_contents)
        for column_idx in sorted(matrix_contents):
            row = []
            for row_idx in sorted(matrix_contents[column_idx]):
                row.append(matrix_contents[column_idx][row_idx])
            matrix_div_contents.append(html.Div(row))

        matrix = html.Div(matrix_div_contents)

        return add_label_help(matrix, label, help_str)

    def get_slider_input(
        self,
        kwarg_label: str,
        default: Any | None = None,
        state: dict = None,
        label: str | None = None,
        help_str: str = None,
        multiple: bool = False,
        **kwargs,
    ):

        state = state or {}
        # TODO: bug if default == 0
        default = default or state.get(kwarg_label)

        # mpc.RangeSlider requires a domain to be specified
        slider_kwargs = {"domain": [0, default * 2]}
        slider_kwargs.update(**kwargs)

        if multiple:
            slider_input = mpc.DualRangeSlider(
                id=self.id(kwarg_label, is_kwarg=True, hint="slider"),
                value=default,
                **slider_kwargs,
            )
        else:
            slider_input = mpc.RangeSlider(
                id=self.id(kwarg_label, is_kwarg=True, hint="slider"),
                value=default,
                **slider_kwargs,
            )

        return add_label_help(slider_input, label, help_str)

    def get_bool_input(
        self,
        kwarg_label: str,
        default: bool | None = None,
        state: dict | None = None,
        label: str | None = None,
        help_str: str = None,
        **kwargs,
    ):
        """For Python classes which take boolean values as inputs, this will generate a
        corresponding Dash input layout.

        :param kwarg_label: The name of the corresponding Python input, this is used
        to name the component.
        :param label: A description for this input.
        :param default: A default value for this input.
        :param state: Used to set default state for this input, use a dict with the
            kwarg_label as a key
        and the default value as a value. Ignored if `default` is set. It can be useful
            to use `state` if you want to set defaults for multiple inputs from a single dictionary.
        :param help_str: Text for a tooltip when hovering over label.
        :return: a Dash layout
        """

        state = state or {}
        default = default or state.get(kwarg_label) or False

        bool_input = mpc.Switch(
            id=self.id(kwarg_label, is_kwarg=True, hint="bool"),
            value=True if default else False,
            hasLabel=True,
            **kwargs,
        )

        return add_label_help(bool_input, label, help_str)

    def get_choice_input(
        self,
        kwarg_label: str,
        default: str | None = None,
        state: dict | None = None,
        label: str | None = None,
        help_str: str = None,
        options: list[dict] | None = None,
        clearable: bool = False,
        **kwargs,
    ):
        """For Python classes which take pre-defined values as inputs, this will generate a
        corresponding input layout using mpc.Select.

        :param kwarg_label: The name of the corresponding Python input, this is used
        to name the component.
        :param label: A description for this input.
        :param default: A default value for this input.
        :param state: Used to set default state for this input, use a dict with the kwarg_label as a key
        and the default value as a value. Ignored if `default` is set. It can be useful to use
        `state` if you want to set defaults for multiple inputs from a single dictionary.
        :param help_str: Text for a tooltip when hovering over label.
        :param options: Options to choose from, as per dcc.Dropdown
        :param clearable: If True, will allow Dropdown to be cleared after a selection is made.
        :return: a Dash layout
        """

        state = state or {}
        default = default or state.get(kwarg_label)

        option_input = mpc.Select(
            id=self.id(kwarg_label, is_kwarg=True, hint="literal"),
            options=options if options else [],
            value=default,
            isClearable=clearable,
            arbitraryProps={**kwargs},
        )

        return add_label_help(option_input, label, help_str)

    def get_dict_input(
        self,
        kwarg_label: str,
        default: Any | None = None,
        state: dict | None = None,
        label: str | None = None,
        help_str: str = None,
        key_name: str = "key",
        value_name: str = "value",
    ):
        """

        :param kwarg_label:
        :param default:
        :param state:
        :param label:
        :param help_str:
        :param key_name:
        :param value_name:
        :return:
        """

        state = state or {}
        default = default or state.get(kwarg_label) or {}

        dict_input = dt.DataTable(
            id=self.id(kwarg_label, is_kwarg=True, hint="dict"),
            columns=[
                {"id": "key", "name": key_name},
                {"id": "value", "name": value_name},
            ],
            data=[{"key": k, "value": v} for k, v in default.items()],
            editable=True,
            persistence=False,
        )

        return add_label_help(dict_input, label, help_str)

    def get_kwarg_id(self, kwarg_name) -> dict[str, str]:
        """

        :param kwarg_name:
        :return:
        """
        return {
            "component_id": self._id,
            "kwarg_label": kwarg_name,
            "idx": ALL,
            "hint": ALL,
        }

    def get_all_kwargs_id(self) -> dict[str, str]:
        """

        :return:
        """
        return {"component_id": self._id, "kwarg_label": ALL, "idx": ALL, "hint": ALL}

    def reconstruct_kwarg_from_state(self, state, kwarg_name):
        return self.reconstruct_kwargs_from_state(
            state=state, kwarg_labels=[kwarg_name]
        )[kwarg_name]

    def reconstruct_kwargs_from_state(self, state=None, kwarg_labels=None) -> dict:
        """Generate.

        :param state: optional, a Dash callback context input or state
        :param kwarg_labels: optional, parse only a specific kwarg or list of kwargs
        :return: A dictionary of keyword arguments with their values
        """

        if not state:
            state = {}
            state.update(dash.callback_context.inputs)
            state.update(dash.callback_context.states)

        kwargs = {}
        for k, v in state.items():

            # TODO: hopefully this will be less hacky in future Dash versions
            # remove trailing ".value" and convert back into dictionary
            # need to sort k somehow ...

            try:
                d = loads(k[: -len(".value")])
            except JSONDecodeError:
                continue

            kwarg_label = d["kwarg_label"]

            if kwarg_labels and kwarg_label not in kwarg_labels:
                continue

            try:
                k_type = literal_eval(d["hint"])
            except ValueError:
                k_type = d["hint"]

            idx = literal_eval(d["idx"])

            try:

                if isinstance(k_type, tuple):
                    # matrix or vector
                    if kwarg_label not in kwargs:
                        kwargs[kwarg_label] = np.empty(k_type)
                    v = literal_eval(str(v))
                    if (v is not None) and (kwargs[kwarg_label] is not None):
                        # print("debugging", kwargs, kwarg_label, idx, v)
                        if isinstance(v, list):
                            print(
                                "This shouldn't happen! Debug required.",
                                kwarg_label,
                                idx,
                                v,
                            )
                            kwargs[kwarg_label][idx] = None
                        else:
                            kwargs[kwarg_label][idx] = v
                    else:
                        # require all elements to have value, otherwise set
                        # entire kwarg to None
                        kwargs[kwarg_label] = None

                elif k_type == "literal":

                    try:
                        kwargs[kwarg_label] = literal_eval(str(v))
                    except (ValueError, SyntaxError):
                        kwargs[kwarg_label] = str(v)

                elif k_type == "bool":
                    kwargs[kwarg_label] = v

                elif k_type == "slider":
                    kwargs[kwarg_label] = v

                elif k_type == "dict":
                    pass

            except Exception as exc:
                # Not raised intentionally but if you notice this in logs please investigate.
                print("This is a problem, debug required.", exc, d, v, type(v))

        for k, v in kwargs.items():
            if isinstance(v, np.ndarray):
                kwargs[k] = v.tolist()

        if SETTINGS.DEBUG_MODE:
            print(type(self).__name__, "kwargs", kwargs)

        return kwargs

    @staticmethod
    def data_uri_from_fig(
        fig: go.Figure,
        fmt: str = "png",
        width: int = 600,
        height: int = 400,
        scale: int = 4,
    ) -> str:
        """Generate a data URI from a Plotly Figure.

        Args:
            fig (Figure): Plotly Figure object or corresponding dictionary
            fmt (str, optional): "png", "jpg", etc. (see PlotlyScope for supported formats). Defaults to "png".
            width (int, optional): width in pixels. Defaults to 600.
            height (int, optional): height in pixels. Defaults to 400.
            scale (int, optional): scale factor. Defaults to 4.

        Returns:
            str: Data URI containing base64-encoded image.
        """
        from kaleido.scopes.plotly import PlotlyScope

        scope = PlotlyScope()
        output = scope.transform(
            fig, format=fmt, width=width, height=height, scale=scale
        )
        image = b64encode(output).decode("ascii")

        return f"data:image/{fmt};base64,{image}"

    def get_figure_placeholder(self, figure_id: str) -> html.Div:
        """Get a layout to act as a placeholder for an interactive figure.

        When used with `generate_static_figure_callbacks`, and assuming
        kaleido is installed on the server, a static image placeholder will
        be generated.

        :return:
        """

        return html.Div(
            [
                html.Div(
                    [Loading(id=self.id(f"{figure_id}-wrapped-figure-inner"))],
                    id=self.id("wrapped-figure-outer"),
                ),
                Button(
                    [Icon(kind="chart-pie"), html.Span(), "Make Plot Interactive"],
                    kind="primary",
                    id=self.id(f"{figure_id}-wrapped-figure-button"),
                ),
            ]
        )
