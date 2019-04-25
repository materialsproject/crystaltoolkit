# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class JSONViewComponent(Component):
    """A JSONViewComponent component.
JSONViewComponent renders JSON using
react-json-view from @mac-s-g

Keyword arguments:
- id (string; optional): The ID used to identify this component in Dash callbacks
- src (dict; optional)
- name (boolean | string; optional)
- theme (string; optional)
- style (dict; optional)
- iconStyle (string; optional)
- identWidth (optional)
- collapsed (boolean; optional)
- collapseStringsAfterLength (boolean; optional)
- groupArraysAfterLength (optional)
- enableClipboard (boolean; optional)
- displayObjectSize (boolean; optional)
- displayDataTypes (boolean; optional)
- defaultValue (dict; optional)
- sortKeys (boolean; optional)
- validationMessage (string; optional)"""
    @_explicitize_args
    def __init__(self, id=Component.UNDEFINED, src=Component.UNDEFINED, name=Component.UNDEFINED, theme=Component.UNDEFINED, style=Component.UNDEFINED, iconStyle=Component.UNDEFINED, identWidth=Component.UNDEFINED, collapsed=Component.UNDEFINED, collapseStringsAfterLength=Component.UNDEFINED, groupArraysAfterLength=Component.UNDEFINED, enableClipboard=Component.UNDEFINED, displayObjectSize=Component.UNDEFINED, displayDataTypes=Component.UNDEFINED, defaultValue=Component.UNDEFINED, sortKeys=Component.UNDEFINED, validationMessage=Component.UNDEFINED, **kwargs):
        self._prop_names = ['id', 'src', 'name', 'theme', 'style', 'iconStyle', 'identWidth', 'collapsed', 'collapseStringsAfterLength', 'groupArraysAfterLength', 'enableClipboard', 'displayObjectSize', 'displayDataTypes', 'defaultValue', 'sortKeys', 'validationMessage']
        self._type = 'JSONViewComponent'
        self._namespace = 'crystal_toolkit'
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'src', 'name', 'theme', 'style', 'iconStyle', 'identWidth', 'collapsed', 'collapseStringsAfterLength', 'groupArraysAfterLength', 'enableClipboard', 'displayObjectSize', 'displayDataTypes', 'defaultValue', 'sortKeys', 'validationMessage']
        self.available_wildcard_properties =            []

        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs
        args = {k: _locals[k] for k in _explicit_args if k != 'children'}

        for k in []:
            if k not in args:
                raise TypeError(
                    'Required argument `' + k + '` was not specified.')
        super(JSONViewComponent, self).__init__(**args)
