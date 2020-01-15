# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class Simple3DSceneComponent(Component):
    """A Simple3DSceneComponent component.
Simple3DSceneComponent is intended to draw simple 3D scenes using the popular
Three.js scene graph library. In particular, the JSON representing the 3D scene
is intended to be human-readable, and easily generated via Python. This is not
intended to be a replacement for a full scene graph library, but for rapid
prototyping by non-experts.

Keyword arguments:
- id (string; optional): The ID used to identify this component in Dash callbacks
- data (dict; optional): Simple3DScene JSON, the easiest way to generate this is to use the Scene class
in crystal_toolkit.core.scene and its to_json method.
- settings (dict; optional): Options used for generating scene.
Supported options and their defaults are given as follows:
{
   antialias: true, // set to false to improve performance
   renderer: 'webgl', // 'svg' also an option, used for unit testing
   transparentBackground: false, // transparent background
   background: '#ffffff', // background color if not transparent,
   sphereSegments: 32, // decrease to improve performance
   cylinderSegments: 16, // decrease to improve performance
   staticScene: true, // disable if animation required
   defaultZoom: 0.8, // 1 will completely fill viewport with scene
}
There are several additional options used for debugging and testing,
please consult the source code directly for these.
- toggleVisibility (dict; optional): Hide/show nodes in scene by its name (key), value is 1 to show the node
and 0 to hide it.
- downloadRequest (dict; optional): Set to trigger a screenshot or scene download. Should be an object with
the structure:
{
   "n_requests": n_requests, // increment to trigger a new download request
   "filename": request_filename, // the download filename
   "filetype": "png", // the download format
}
- selectedObjectReference (string; optional): Reference to selected objects when clicked
- selectedObjectCount (number; optional): Click count for selected object"""

    @_explicitize_args
    def __init__(
        self,
        id=Component.UNDEFINED,
        data=Component.UNDEFINED,
        settings=Component.UNDEFINED,
        toggleVisibility=Component.UNDEFINED,
        downloadRequest=Component.UNDEFINED,
        selectedObjectReference=Component.UNDEFINED,
        selectedObjectCount=Component.UNDEFINED,
        **kwargs
    ):
        self._prop_names = [
            "id",
            "data",
            "settings",
            "toggleVisibility",
            "downloadRequest",
            "selectedObjectReference",
            "selectedObjectCount",
        ]
        self._type = "Simple3DSceneComponent"
        self._namespace = "crystal_toolkit"
        self._valid_wildcard_attributes = []
        self.available_properties = [
            "id",
            "data",
            "settings",
            "toggleVisibility",
            "downloadRequest",
            "selectedObjectReference",
            "selectedObjectCount",
        ]
        self.available_wildcard_properties = []

        _explicit_args = kwargs.pop("_explicit_args")
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs
        args = {k: _locals[k] for k in _explicit_args if k != "children"}

        for k in []:
            if k not in args:
                raise TypeError("Required argument `" + k + "` was not specified.")
        super(Simple3DSceneComponent, self).__init__(**args)
