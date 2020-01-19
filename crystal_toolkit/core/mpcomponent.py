import logging
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from json import dumps, loads
from time import mktime
from uuid import uuid4
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

# Crystal Toolkit namespace, added to the start of all ids
# so we can see which layouts have been added by Crystal Toolkit
CT_NAMESPACE = "_ct_"


class MPComponent(ABC):
    """
    The abstract base class for an MPComponent. MPComponent
    is designed to help render an MSONable object.
    """

    # reference to global Dash app
    app = None

    # reference to Flask cache
    cache = None

    # used to track all dcc.Stores required for all MPComponents to work
    # keyed by the MPComponent id
    _app_stores_dict: Dict[str, List[dcc.Store]] = defaultdict(list)

    # used to track what individual Dash components are defined
    # by this MPComponent
    _all_id_basenames: Set[str] = set()

    # used to track what callbacks have been generated
    _callbacks_generated_for_ids: Set[str] = set()

    # used to defer generation of callbacks until app.layout defined
    # can be helpful to callback exceptions retained
    _callbacks_to_generate: Set["MPComponent"] = set()

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
        if cache:
            MPComponent.cache = cache
        else:
            MPComponent.cache = Cache(
                MPComponent.app.server, config={"CACHE_TYPE": "simple"}
            )

    @staticmethod
    def crystal_toolkit_layout(layout: html.Div) -> html.Div:

        if not MPComponent.app:
            raise ValueError(
                "Please register the Dash app with Crystal Toolkit "
                "using register_app()."
            )

        layout_str = str(layout)
        stores_to_add = []
        for basename in MPComponent._all_id_basenames:
            if basename in layout_str:
                stores_to_add += MPComponent._app_stores_dict[basename]
        layout.children += stores_to_add

        # set app.layout to layout so that callbacks can be validated
        MPComponent.app.layout = layout

        for component in MPComponent._callbacks_to_generate:
            if component.id() not in MPComponent._callbacks_generated_for_ids:
                component.generate_callbacks(MPComponent.app, MPComponent.cache)
                MPComponent._callbacks_generated_for_ids.add(component.id())

        return layout

    @staticmethod
    def register_crystal_toolkit(app, layout, cache=None):

        MPComponent.register_app(app)
        MPComponent.register_cache(cache)
        app.config["suppress_callback_exceptions"] = True
        app.layout = MPComponent.crystal_toolkit_layout(layout)

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
        default_data: Optional[MSONable] = None,
        id: Optional[str] = None,
        links: Optional[Dict[str, str]] = None,
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
            default_data: inital contents for the component, can be None
            id: a unique id, required if multiple of the same type of
            MPComponent are included in an app
            links: if set, will set store contents from the stores of another
            component to reduce unnecessary callbacks and duplication of data,
            note that links are one directional only and specific the origin
            stores, e.g. set {"default": my_other_component.id()} to fill this
            component's default store contents from the other component's default store,
            or {"graph": my_other_component.id("graph")} to fill this component's
            "graph" store from another component's "graph" store
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
        # Note: shadowing Python built-in here, but only because Dash does it...
        if id is None:
            id = f"{CT_NAMESPACE}{self.__class__.__name__}_{str(uuid4())[0:6]}"
        else:
            id = f"{CT_NAMESPACE}{id}"
        MPComponent._all_id_basenames.add(id)

        self._id = id
        self._all_ids = set()
        self._stores = {}
        self._initial_data = {}

        self.links = links or {}

        if self.links and not MPComponent.app:
            raise ValueError(
                "Can only link stores if an app is registered. Either register the "
                "global Dash app variable with Crystal Toolkit, or remove links and "
                "run with disable_callbacks=True."
            )

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
            self.create_store(
                name="default", initial_data=default_data, storage_type=storage_type
            )
            self.links["default"] = self.id()
        else:
            print("origin component deprecated", self.id())
            self.links["default"] = origin_component.links["default"]

        if not disable_callbacks:
            # callbacks generated as final step by crystal_toolkit_layout()
            self._callbacks_to_generate.add(self)

        self.logger = logging.getLogger(self.__class__.__name__)

    def id(self, name: str = "default") -> str:
        """
        Generate an id from a name combined with the
        base id of the MPComponent itself, useful for generating
        ids of individual components in the layout.

        Args:
            name: e.g. "default"

        Returns: e.g. "MPComponent_default"
        """

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

    def create_store(
        self,
        name: str,
        initial_data: Optional[Union[MSONable, Dict, str]] = None,
        storage_type: Literal["memory", "local", "session"] = "memory",
        debug_clear: bool = False,
    ):
        """
        Generate a dcc.Store to hold something (MSONable object, Dict
        or string), and register it so that it will be included in the
        Dash app automatically.

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
            id=self.id(name),
            data=initial_data,
            storage_type=storage_type,
            clear_data=debug_clear,
        )
        self._stores[name] = store
        self._initial_data[name] = initial_data
        MPComponent._app_stores_dict[self.id()].append(store)

    @property
    def initial_data(self):
        """
        :return: Initial data for all the stores defined by component,
        keyed by store name.
        """
        return self._initial_data

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
        print("attach_from deprecated", self.id())

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

    @property
    def all_stores(self) -> List[str]:
        """
        :return: List of all store ids generated by this component
        """
        return list(self._stores.keys())

    @property
    def all_ids(self) -> List[str]:
        """
        :return: List of all ids generated by this component
        """
        return list(
            [
                component_id
                for component_id in self._all_ids
                if component_id not in self.all_stores
            ]
        )

    def __repr__(self):
        ids = "\n".join(
            [f"* {component_id}  " for component_id in sorted(self.all_ids)]
        )
        stores = "\n".join([f"* {store}  " for store in sorted(self.all_stores)])
        layouts = "\n".join(
            [f"* {layout}  " for layout in sorted(self._sub_layouts.keys())]
        )

        return f"""{self.id()}<{self.__class__.__name__}>  \n
IDs:  \n{ids}  \n
Stores:  \n{stores}  \n
Sub-layouts:  \n{layouts}"""

    @property
    def _sub_layouts(self):
        """
        Layouts associated with this component, available for book-keeping
        if your component is complex, so that the layout() method is just
        assembles individual sub-layouts.

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

    @abstractmethod
    def generate_callbacks(self, app, cache):
        """
        Generate all callbacks associated with the layouts in this app. Assume
        that "suppress_callback_exceptions" is True, since it is not always
        guaranteed that all layouts will be displayed to the end user at all
        times, but it's important the callbacks are defined on the server.
        """
        raise NotImplementedError
