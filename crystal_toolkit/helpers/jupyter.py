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


def view(struct_or_mol, smc_kwargs={}):
    # populate the StructureMoleculeComponent with some default kwargs
    smc_kwargs_defaults = {
        'bonded_sites_outside_unit_cell':True,
        'color_scheme':'VESTA',
        'radius_strategy':'uniform',
    }
    for key in smc_kwargs_defaults.keys():
        if key not in smc_kwargs:
            smc_kwargs[key] = smc_kwargs_defaults[key]
    if 'crystal_toolkit_app' not in globals():
        init_viewer()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        component = StructureMoleculeComponent(struct_or_mol, **smc_kwargs)

    crystal_toolkit_app.title = struct_or_mol.composition.reduced_formula
    crystal_toolkit_app.layout = html.Div([component.standard_layout])
    crystal_toolkit_viewer.show(crystal_toolkit_app)


def get_component(obj):

    if not isinstance(obj, MSONable):
        raise ValueError("Can only display MSONable types.")

    if isinstance(obj, Structure) or isinstance(obj, Molecule):
        return StructureMoleculeComponent

    return JSONViewComponent(src=obj.to_json())
