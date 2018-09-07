from mp_dash_components.converters.structure import StructureIntermediateFormat
from mp_dash_components import StructureViewerComponent

import dash_core_components as dcc
import dash_html_components as html


from json import loads, dumps
from monty.json import MSONable, MontyDecoder
from pymatgen.core import Structure


def _sanitize_input(msonable_object):

    # restrict to loading from supported classes to be slightly safer
    # tuple of (module, class)
    SUPPORTED_OBJECTS = [('pymatgen.core.structure', 'Structure')]

    if isinstance(msonable_object, MSONable):
        return msonable_object
    elif type(msonable_object) == str:
        msonable_object = loads(msonable_object)

    if (type(msonable_object) == dict) and ((msonable_object.get('@module', None),
                                             msonable_object.get('@class', None))
                                            in SUPPORTED_OBJECTS):
        msonable_object = MontyDecoder(dumps(msonable_object))
    else:
        # if it's not supported, convert back to string
        msonable_object = dumps(msonable_object, indent=4)

    return msonable_object


def mp_component(msonable_object, id=None, *args, **kwargs):
    """
    :param msonable_object: an MSONable object, or the JSON string representation
    of an MSONable object, or the dictionary representation of an MSONable object
    :return: Dash layout
    """

    msonable_object = _sanitize_input(msonable_object)

    if isinstance(msonable_object, Structure):
        return mp_structure_component(msonable_object, id=id, *args, **kwargs)
    elif isinstance(msonable_object, str):
        return dcc.SyntaxHighlighter(id=id, children="'''\n{}\n'''".format(msonable_object))
    else:
        raise ValueError("Cannot generate a layout for this object.")


def mp_structure_component(structure, id=None, *args, **kwargs):

    structure = _sanitize_input(structure)

    if isinstance(structure, Structure):
        intermediate_json = StructureIntermediateFormat(structure, *args, **kwargs).json
        return StructureViewerComponent(id=id, data=intermediate_json)
    else:
        raise ValueError