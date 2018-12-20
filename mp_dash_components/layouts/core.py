import dash_core_components as dcc
import dash_html_components as html

from abc import ABC, abstractmethod
from json import loads, dumps
from monty.json import MontyEncoder, MontyDecoder
from datetime import datetime
from time import mktime
from warnings import warn
from dash import Dash
from dash.dependencies import Input, Output


class MPComponent(ABC):

    _instances = {}

    def __init__(self, id=None, origin_component=None, contents=None, app=None):
        """
        :param id: a unique id for this component, if not specified a random
        one will be chosen
        :param origin_component: if specified, component will reference the
        Store in the origin MPComponent instead of creating its own Store
        :param contents: an object that can be serialized using the MSON
        protocol, can be set to None initially
        :param app: Dash app to generate callbacks, if None will look for 'app'
        in global scope
        """

        if id is None:
            id = self.__class__.__name__

        if id in MPComponent._instances:
            raise ValueError(
                "You cannot instantiate more than one instance of "
                "the class with the same id."
            )

        self._id = id
        self._instances[id] = self

        if app:
            self.app = app
        elif "app" in globals() and isinstance(globals()["app"], Dash):
            self.app = globals()["app"]
        elif app is None:
            warn("No app defined, callbacks cannot be created.")

        if self.app:
            self._generate_callbacks(self.app)

        if origin_component is None:
            self._contents = contents
            self._store_id = id
            if contents is not None:
                self._store = dcc.Store(id=id, data=contents.to_json())
            else:
                self._store = dcc.Store(id=id)
        else:
            self._contents = origin_component._contents
            self._store = origin_component._store
            self._store_id =  origin_component._store_id

    @property
    def id(self):
        """
        The primary id for this component.
        """
        return self._id

    @property
    def store_id(self):
        """
        The id for the primary Store backing this component, usually corresponds
        to the primary id unless primary Store references another component.
        """
        return self._store_id

    @staticmethod
    def to_data(msonable_obj):
        """
        Converts any MSONable object into a format suitable for storing in
        a dcc.Store

        :param msonable_obj: Any MSONable object
        :return: A JSON string (a string is preferred over a dict since this can
        be easily memoized)
        """
        return dumps(msonable_obj, cls=MontyEncoder, indent=4)

    @staticmethod
    def from_data(data):
        """
        Converts the contents of a dcc.Store back into a Python object.
        :param data: contents of a dcc.Store created by to_data
        :return: a Python object
        """
        return loads(data, cls=MontyDecoder)

    def attach_from(self, origin_component, origin_store_suffix=None,
                    this_store_suffix=None):
        """
        Link two MPComponents together.

        :param origin_component: An MPComponent
        :param origin_store_suffix: The suffix for the Store layout in the
        origin component, e.g. "structure" or "mpid", if None will link to
        the component's default Store
        :param this_store_suffix: The suffix for the Store layout in this
        component to be linked to, this is usually equal to the
        origin_store_suffix
        :return:
        """

        if self.app is None:
            raise AttributeError("No app defined, callbacks cannot be created.")

        if origin_store_suffix:
            origin_store_id = f'{self.id}_{origin_store_suffix}'
        else:
            origin_store_id = origin_component.store_id

        if this_store_suffix:
            dest_store_id = f'{self.id}_{this_store_suffix}'
        else:
            dest_store_id = self.store_id

        @self.app.callback(
            Output(dest_store_id, "data"),
            [Input(origin_store_id, "data")]
        )
        def update_store(data):
            return data

    @property
    @abstractmethod
    def layouts(self):
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
        return {
            "main": html.Div(id=f"{self.id}_main"),
            "error": html.Div(id=f"{self.id}_error", className="mpc_error"),
            "warning": html.Div(id=f"{self.id}_warning", className="mpc_warning"),
            "label": html.Label(id=f"{self.id}_label", className="mpc_label"),
            "help": dcc.Markdown(id=f"{self.id}_help", className="mpc_help"),
            "store": self._store
        }

    @property
    @abstractmethod
    def all_layouts(self):
        """
        :return: A Dash layout for the full component, for example including
        both the main component and controls for that component. Must
        """
        return html.Div(list(self.layouts.values()))

    @abstractmethod
    def _generate_callbacks(self, app):
        """
        Generate all callbacks associated with the layouts in this app. Assume
        that "suppress_callback_exceptions" is True, since it is not always
        guaranteed that all layouts will be displayed to the end user at all
        times, but it's important the callbacks are defined on the server.
        """
        raise NotImplementedError
