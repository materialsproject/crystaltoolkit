import dash
import numpy as np
from pymatgen.io.vasp import Chgcar
from skimage import measure

import crystal_toolkit.components as ctc
import crystal_toolkit.core.scene as cts

app = dash.Dash(__name__)

app.config["suppress_callback_exceptions"] = True
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True
app.title = "Crystal Toolkit Example Components"


# so that Crystal Toolkit can create callbacks
# ctc.register_app(app)

# StructureMoleculeComponent


def get_mesh(chgcar, data_tag="total", isolvl=2.0, step_size=3):
    vertices, faces, _normals, _values = measure.marching_cubes_lewiner(
        chgcar.data[data_tag], level=isolvl, step_size=step_size
    )
    vertices = (
        vertices / chgcar.data[data_tag].shape
    )  # transform to fractional coordinates
    vertices = np.dot(
        vertices - 0.5, cc.structure.lattice.matrix
    )  # transform to cartesian
    return vertices, faces


cc = Chgcar.from_file("./test_files/chgcar.vasp")
vertices, faces = get_mesh(cc)
vertices = vertices
pos = [vert for triangle in vertices[faces].tolist() for vert in triangle]

add_comp = [
    cts.Scene(
        "test",
        contents=[
            cts.Surface(positions=pos),
            cts.Arrows(positionPairs=[[[0, 0, 0], [1, 1, 1]]]),
        ],
    )
]

struct_component = ctc.StructureMoleculeComponent(
    cc.structure,
    scene_additions=add_comp,
    hide_incomplete_bonds=True
    # get the data points to plot
)

# for a custom-sized component, use `struct_component.struct_layout` and put
# it inside a Div of the required size
app.layout = dash.html.Div(
    [
        # not required in this minimal example but usually necessary for interactivity
        ctc.MPComponent.all_app_stores(),
        struct_component.standard_layout,
    ]
)


if __name__ == "__main__":
    app.run_server(debug=True)
