import jupyterlab_dash
import dash

import warnings
import dash_html_components as html

from monty.json import MSONable
from pymatgen.core.structure import Structure, Molecule

from crystal_toolkit import JSONViewComponent
from crystal_toolkit.components.structure import StructureMoleculeComponent


def init_viewer():

    global crystal_toolkit_viewer
    global crystal_toolkit_app

    crystal_toolkit_viewer = jupyterlab_dash.AppViewer(port=8090)
    crystal_toolkit_app = dash.Dash(__name__)


def view(struct_or_mol, **kwargs):
    """
    View a Structure or Molecule inside a Jupyter notebook.
    :param struct_or_mol: Structure or Molecule object
    :param kwargs: kwargs to pass to StructureMoleculeComponent
    :return:
    """

    if 'crystal_toolkit_app' not in globals():
        init_viewer()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        component = StructureMoleculeComponent(struct_or_mol, **kwargs)

    crystal_toolkit_app.title = struct_or_mol.composition.reduced_formula
    crystal_toolkit_app.layout = html.Div([component.standard_layout])
    crystal_toolkit_viewer.show(crystal_toolkit_app)


def get_component(obj):

    if not isinstance(obj, MSONable):
        raise ValueError("Can only display MSONable types.")

    if isinstance(obj, Structure) or isinstance(obj, Molecule):
        return StructureMoleculeComponent

    return JSONViewComponent(src=obj.to_json())
