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
- validationMessage (string; optional)

Available events: """
    @_explicitize_args
    def __init__(self, id=Component.UNDEFINED, src=Component.UNDEFINED, name=Component.UNDEFINED, theme=Component.UNDEFINED, style=Component.UNDEFINED, iconStyle=Component.UNDEFINED, identWidth=Component.UNDEFINED, collapsed=Component.UNDEFINED, collapseStringsAfterLength=Component.UNDEFINED, groupArraysAfterLength=Component.UNDEFINED, enableClipboard=Component.UNDEFINED, displayObjectSize=Component.UNDEFINED, displayDataTypes=Component.UNDEFINED, defaultValue=Component.UNDEFINED, sortKeys=Component.UNDEFINED, validationMessage=Component.UNDEFINED, **kwargs):
        self._prop_names = ['id', 'src', 'name', 'theme', 'style', 'iconStyle', 'identWidth', 'collapsed', 'collapseStringsAfterLength', 'groupArraysAfterLength', 'enableClipboard', 'displayObjectSize', 'displayDataTypes', 'defaultValue', 'sortKeys', 'validationMessage']
        self._type = 'JSONViewComponent'
        self._namespace = 'crystal_toolkit'
        self._valid_wildcard_attributes =            []
        self.available_events = []
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

    def __repr__(self):
        if(any(getattr(self, c, None) is not None
               for c in self._prop_names
               if c is not self._prop_names[0])
           or any(getattr(self, c, None) is not None
                  for c in self.__dict__.keys()
                  if any(c.startswith(wc_attr)
                  for wc_attr in self._valid_wildcard_attributes))):
            props_string = ', '.join([c+'='+repr(getattr(self, c, None))
                                      for c in self._prop_names
                                      if getattr(self, c, None) is not None])
            wilds_string = ', '.join([c+'='+repr(getattr(self, c, None))
                                      for c in self.__dict__.keys()
                                      if any([c.startswith(wc_attr)
                                      for wc_attr in
                                      self._valid_wildcard_attributes])])
            return ('JSONViewComponent(' + props_string +
                   (', ' + wilds_string if wilds_string != '' else '') + ')')
        else:
            return (
                'JSONViewComponent(' +
                repr(getattr(self, self._prop_names[0], None)) + ')')
