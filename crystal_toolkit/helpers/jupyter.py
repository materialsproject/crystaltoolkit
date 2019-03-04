import jupyterlab_dash
import dash

import warnings
import dash_html_components as html

from crystal_toolkit.components.structure import StructureMoleculeComponent


def init_viewer():

    global viewer
    global app

    viewer = jupyterlab_dash.AppViewer(port=8090)
    app = dash.Dash(__name__)


def view(struct_or_mol):

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        component = StructureMoleculeComponent(struct_or_mol,
                                               bonded_sites_outside_unit_cell=True,
                                               color_scheme='VESTA',
                                               radius_strategy='uniform')

    app.title = struct_or_mol.composition.reduced_formula
    app.layout = html.Div([component.standard_layout])
    viewer.show(app)
