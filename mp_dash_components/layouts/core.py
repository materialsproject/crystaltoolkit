import dash_core_components as dcc
import dash_html_components as html

from warnings import warn
from dash import Dash
from dash.dependencies import Input, Output
from abc import ABC, abstractmethod


class MPComponent(ABC):

    _instances = {}

    def __init__(self, id, msonable_object=None, from_component=None, app=None):
        """
        :param id: a unique id for this component
        :param msonable_object: an object that can be serialized using the MSON
        protocol, can be set to None initially
        :param from_component: (optional) automatically register a callback from
        another MPComponent of the same type
        :param app: Dash app to generate callbacks, if None will look for 'app'
        in global scope
        """

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
        else:
            warn("No app defined, callbacks cannot be created.")

        if self.app:

            if from_component:
                if not isinstance(from_component, MPComponent):
                    raise ValueError(
                        "The from_component must be an instance " "of MPComponent."
                    )

                @self.app.callback(
                    Output(self.id, "data"), [Input(from_component.id, "data")]
                )
                def update_store(data):
                    return data

            self._generate_callbacks(self.app)

        self._store = dcc.Store(id=id, data=msonable_object.to_json())

    @property
    def id(self):
        """
        The primary id for this component, corresponding to its underlying
        Store.
        """
        return self._id

    @abstractmethod
    @property
    def layouts(self):
        """
        Layouts associated with this component. All individual layout ids must
        be derived from main id followed by an underscore, for example, for an
        input box layout a suitable id name might be f"{self.id}_input".

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
            "error": html.Div(id=f"{self.id}_error", className="mpc_error"),
            "warning": html.Div(id=f"{self.id}_warning", className="mpc_warning"),
            "label": html.Label(id=f"{self.id}_label", className="mpc_label"),
            "help": dcc.Markdown(id=f"{self.id}_help", className="mpc_help"),
        }

    @abstractmethod
    @property
    def all_layouts(self):
        """
        :return: A Dash layout for the full component, for example including
        both the main component and controls for that component.
        """
        return NotImplementedError

    @abstractmethod
    def _generate_callbacks(self, app):
        """
        Generate all callbacks associated with the layouts in this app. Assume
        that "suppress_callback_exceptions" is True, since it is not always
        guaranteed that all layouts will be displayed to the end user at all
        times, but it's important the callbacks are defined on the server.
        """
        return NotImplementedError
