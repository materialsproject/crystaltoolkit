# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class GraphComponent(Component):
    """A GraphComponent component.
GraphComponent renders a force-directed graph using 
react-graph-vis by @crubier and vis.js

Keyword arguments:
- id (string; optional): The ID used to identify this component in Dash callbacks
- graph (dict; optional): A graph that will be displayed when this component is rendered
- options (dict; optional): Display options for the graph"""
    @_explicitize_args
    def __init__(self, id=Component.UNDEFINED, graph=Component.UNDEFINED, options=Component.UNDEFINED, **kwargs):
        self._prop_names = ['id', 'graph', 'options']
        self._type = 'GraphComponent'
        self._namespace = 'crystal_toolkit'
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'graph', 'options']
        self.available_wildcard_properties =            []

        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs
        args = {k: _locals[k] for k in _explicit_args if k != 'children'}

        for k in []:
            if k not in args:
                raise TypeError(
                    'Required argument `' + k + '` was not specified.')
        super(GraphComponent, self).__init__(**args)
