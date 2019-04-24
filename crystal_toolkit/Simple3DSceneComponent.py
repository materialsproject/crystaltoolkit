# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class Simple3DSceneComponent(Component):
    """A Simple3DSceneComponent component.
Simple3DSceneComponent is intended to draw simple 3D scenes using the popular
Three.js scene graph library. In particular, the JSON representing the 3D scene
is intended to be human-readable, and easily generated via Python. In future, a
long-term approach would be to develop a library to generate Three.js JSON directly
inside Python to make this component redundant.

Keyword arguments:
- id (string; optional): The ID used to identify this component in Dash callbacks
- data (dict; optional): Simple3DScene JSON
- settings (dict; optional): Options used for generating scene
- toggleVisibility (dict; optional): Hide/show nodes in scene by name (key), value is 1 to show the node
and 0 to hide it
- downloadRequest (dict; optional): Increment to trigger a screenshot or scene download."""
    @_explicitize_args
    def __init__(self, id=Component.UNDEFINED, data=Component.UNDEFINED, settings=Component.UNDEFINED, toggleVisibility=Component.UNDEFINED, downloadRequest=Component.UNDEFINED, **kwargs):
        self._prop_names = ['id', 'data', 'settings', 'toggleVisibility', 'downloadRequest']
        self._type = 'Simple3DSceneComponent'
        self._namespace = 'crystal_toolkit'
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'data', 'settings', 'toggleVisibility', 'downloadRequest']
        self.available_wildcard_properties =            []

        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs
        args = {k: _locals[k] for k in _explicit_args if k != 'children'}

        for k in []:
            if k not in args:
                raise TypeError(
                    'Required argument `' + k + '` was not specified.')
        super(Simple3DSceneComponent, self).__init__(**args)
