import logging
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from json import dumps, loads
from time import mktime
from warnings import warn
import dash

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State
from monty.json import MontyEncoder, MontyDecoder, MSONable

from crystal_toolkit import __version__ as ct_version

from flask_caching import Cache

from collections import defaultdict
from itertools import chain

from typing import Optional, Union, Dict, List, Set
from typing_extensions import Literal

from functools import wraps

# fallback cache if Redis etc. isn't set up
null_cache = Cache(config={"CACHE_TYPE": "null"})


class MPComponent(ABC):
    """
    The abstract base class for an MPComponent. MPComponent
    is designed to help render an MSONable object.
    """

    app = None  # reference to global Dash app
    cache = null_cache  # reference to Flask cache

    _app_stores_dict: Dict[str, List[dcc.Store]] = defaultdict(list)
    _all_id_basenames: Set[str] = set()
    _callbacks_generated_for_ids: Set[str] = set()

    @staticmethod
    def register_app(app: dash.Dash):
        """
        This method must be called at least once in your Crystal
        Toolkit Dash app if you want to enable interactivity with the
        MPComponents. The "app" variable is a special global
        variable used by Dash/Flask, and registering it with
        MPComponent allows callbacks to be registered with the
        app on instantiation.

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

    @staticmethod
    def register_cache(cache: Cache):
        """
        This method must be called at least once in your
        Crystal Toolkit Dash app if you want to enable
        callback caching. Callback caching is one of the
        easiest ways to see significant performance
        improvements, especially for callbacks that are
        computationally expensive.

        Args:
            cache: a flask_caching Cache instance
        """
        MPComponent.cache = cache

    # TODO: move these to Crystal Toolkit singleton (?)
    @staticmethod
    def crystal_toolkit_layout(layout: html.Div) -> html.Div:
        layout_str = str(layout)
        stores_to_add = []
        for basename in MPComponent._all_id_basenames:
            if basename in layout_str:
                stores_to_add += MPComponent._app_stores_dict[basename]
        layout.children += stores_to_add
        return layout

    @staticmethod
    def all_app_stores() -> html.Div:
        """
        This must be included somewhere in your
        Crystal Toolkit Dash app's layout for
        interactivity to work. This is a hidden element
        that contains the MSON for each MPComponent.

        Returns: a html.Div Dash Layout
        """
        return html.Div(
            list(chain.from_iterable(MPComponent._app_stores_dict.values()))
        )

    def __init__(
        self,
        contents: Optional[MSONable] = None,
        id: Optional[str] = None,
        origin_component: Optional["MPComponent"] = None,
        storage_type: Literal["memory", "local", "session"] = "memory",
        disable_callbacks: bool = False,
    ):
        """
        The abstract base class for an MPComponent.

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
            contents: inital contents for the component, can be None
            id: a unique id, required if multiple of the same type of
            MPComponent are included in an app
            origin_component: if set, will fill contents using the contents
            of the origin_component, can be useful to chain together multiple
            components without creating unnecessary duplication of contents
            storage_type: whether to persist contents of component through
            browser refresh or browser sessions, use with caution, defaults
            to "memory" so component store will be emptied on refresh, see
            dcc.Store documentation for more information
            disable_callbacks: if True, will not generate callbacks, useful
            for static layouts or returning new MPComponents dynamically where
            generating callbacks are not possible due to limitations of Dash
        """

        # ensure ids are unique
        if id is None:
            counter = 0
            while id not in MPComponent._all_id_basenames:
                if counter == 0:
                    test_id = self.__class__.__name__
                else:
                    test_id = f"{self.__class__.__name__}_{counter}"
                if test_id not in MPComponent._all_id_basenames:
                    id = test_id
                    MPComponent._all_id_basenames.add(id)

        self._id = id
        self._all_ids = set()
        self._stores = {}

        if MPComponent.app is None:
            warn(
                f"No app defined for component {self._id}, "
                f"callbacks cannot be created. Please register app using "
                f"MPComponent.register_app(app)."
            )

        if MPComponent.cache is null_cache:
            warn(
                f"No cache is defined for component {self._id}, "
                f"performance of app may be degraded. Please register cache "
                f"using MPComponent.register_cache(cache)."
            )

        if origin_component is None:
            self._canonical_store_id = self._id
            self.create_store(
                name="default", initial_data=contents, storage_type=storage_type
            )
            self.initial_data = contents
        else:
            if MPComponent.app is None:
                raise ValueError("Can only link stores if an app is registered.")
            self._canonical_store_id = origin_component._canonical_store_id
            self.initial_data = origin_component.initial_data

        if (
            MPComponent.app
            and not disable_callbacks
            and (self.id not in MPComponent._callbacks_generated_for_ids)
        ):
            self.generate_callbacks(MPComponent.app, MPComponent.cache)
            # prevent callbacks being generated twice for the same ID
            MPComponent._callbacks_generated_for_ids.add(self.id)

        self.logger = logging.getLogger(self.__class__.__name__)

    def id(self, name: str = "default"):
        """
        Generate an id from a name combined with the
        base id of the MPComponent itself, useful for generating
        ids of individual components in the layout.

        Args:
            name: e.g. "default"

        Returns: e.g. "MPComponent_default"
        """
        self._all_ids.add(name)
        if name != "default":
            name = f"{self._id}_{name}"
        else:
            name = self._canonical_store_id
        return name

    def create_store(
        self,
        name: str,
        initial_data: Optional[Union[MSONable, Dict, str]] = None,
        storage_type: Literal["memory", "local", "session"] = "memory",
        debug_clear: bool = False,
        to_data: bool = True,
    ):
        """
        Generate a dcc.Store to hold something (MSONable object, Dict
        or string), and register it so that it will be included in the
        Dash app automatically.

        Args:
            name: name for the store
            initial_data: initial data to include
            storage_type: as in dcc.Store
            debug_clear: set to True to empty the store if using
            persistent storage
        """
        store = dcc.Store(
            id=self.id(name),
            data=initial_data,
            storage_type=storage_type,
            clear_data=debug_clear,
        )
        self._stores[name] = store
        MPComponent._app_stores_dict[self.id()].append(store)

    @staticmethod
    def from_data(data):
        """
        Converts the contents of a dcc.Store back into a Python object.
        :param data: contents of a dcc.Store created by to_data
        :return: a Python object
        """
        return loads(dumps(data), cls=MontyDecoder)

    def attach_from(
        self, origin_component, origin_store_name="default", this_store_name="default"
    ):
        """
        Link two MPComponents together.

        :param origin_component: An MPComponent
        :param origin_store_name: The suffix for the Store layout in the
        origin component, e.g. "structure" or "mpid", if None will link to
        the component's default Store
        :param this_store_name: The suffix for the Store layout in this
        component to be linked to, this is usually equal to the
        origin_store_suffix
        :return:
        """

        if MPComponent.app is None:
            raise AttributeError("No app defined, callbacks cannot be created.")

        origin_store_id = origin_component.id(origin_store_name)
        dest_store_id = self.id(this_store_name)

        self.logger.debug(
            f"Linking the output of {origin_store_id} to {dest_store_id}."
        )

        @MPComponent.app.callback(
            Output(dest_store_id, "data"),
            [Input(origin_store_id, "modified_timestamp")],
            [State(origin_store_id, "data")],
        )
        def update_store(modified_timestamp, data):
            # TODO: make clientside callback!
            return data

    def __getattr__(self, item):
        # TODO: remove, this isn't helpful (or add autocomplete)
        if item == "supported_stores":
            raise AttributeError  # prevent infinite recursion
        if item.endswith("store") and item.split("_store")[0] in self.supported_stores:
            print(self.__class__.__name__, "attr hack")
            return self.id(item)
        elif (
            item.endswith("layout")
            and item.split("_layout")[0] in self.supported_layouts
        ):
            print(self.__class__.__name__, "attr hack")
            return self._sub_layouts[item.split("_layout")[0]]
        else:
            raise AttributeError

    @property
    def supported_stores(self):
        return self._stores.keys()

    @property
    def supported_layouts(self):
        return self._sub_layouts.keys()

    @property
    def supported_ids(self):
        return list(self._all_ids)

    def __repr__(self):
        return f"""{self.id()}<{self.__class__.__name__}>
IDs: {list(self.supported_ids)}
Stores: {list(self.supported_stores)}
Layouts: {list(self.supported_layouts)}"""

    @property
    @abstractmethod
    def _sub_layouts(self):
        """
        Layouts associated with this component.

        All individual layout ids *must* be derived from main id followed by an
        underscore, for example, for an input box layout a suitable id name
        might be f"{self.id}_input".

        The underlying store (self._store) *must* be included in self.layouts.

        :return: A dictionary with names of layouts as keys (str) and Dash
        layouts as values. Preferred keys include:
        "main" for the primary layout for this component,
        "label" for a html.Label describing the component with className
        "mpc_label",
        "help" for a dcc.Markdown component explaining how it works,
        "controls" for controls to interact with the component (for example to
        change how the data is displayed) with className "mpc_help",
        "error" for a component that will display any appropriate errors, this
        should contain a html.Div with className "mpc_error", and
        "warning" for a component that will display any appropriate warnings,
        this should contain a html.Div with className "mpc_warning".

        These layouts are not mandatory but are at the discretion of the
        component author.
        """
        return {}

    @property
    def layout(self):
        """
        :return: A Dash layout for the full component, for example including
        both the main component and controls for that component. Must
        """
        return html.Div(list(self._sub_layouts.values()))

    @abstractmethod
    def generate_callbacks(self, app, cache):
        """
        Generate all callbacks associated with the layouts in this app. Assume
        that "suppress_callback_exceptions" is True, since it is not always
        guaranteed that all layouts will be displayed to the end user at all
        times, but it's important the callbacks are defined on the server.
        """
        raise NotImplementedError
