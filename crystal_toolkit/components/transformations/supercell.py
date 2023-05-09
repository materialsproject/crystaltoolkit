from __future__ import annotations

from dash import html
from dash_mp_components import CrystalToolkitScene
from pymatgen.transformations.standard_transformations import SupercellTransformation

from crystal_toolkit.components.transformations.core import TransformationComponent
from crystal_toolkit.core.scene import Scene


class SupercellTransformationComponent(TransformationComponent):
    @property
    def title(self) -> str:
        return "Make a supercell"

    @property
    def description(self) -> str:
        return """Create a supercell by providing a scaling matrix that transforms
input lattice vectors a, b and c into transformed lattice vectors a', b' and c'.


For example, to create a supercell with lattice vectors a'=2a, b'=2b, c'=2c enter a
scaling matrix [[2, 0, 0], [0, 2, 0], [0, 0, 2]] or to create a supercell with
lattice vectors a' = 2a+b, b' = 3b and c' = c enter a scaling matrix
[[2, 1, 0], [0, 3, 0], [0, 0, 1]]. All elements of the scaling matrix must be
integers."""

    @property
    def transformation(self):
        return SupercellTransformation

    def options_layouts(self, state=None, structure=None):
        state = state or {"scaling_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1))}

        return self.get_numerical_input(
            label="Scaling matrix",
            kwarg_label="scaling_matrix",
            state=state,
            help_str="""Scaling matrix that transforms
            input lattice vectors a, b and c into transformed lattice vectors a', b' and c'.""",
            shape=(3, 3),
        )

    def get_preview_layout(self, struct_in, struct_out):
        if struct_in.lattice == struct_out.lattice:
            return html.Div()

        lattice_in = struct_in.lattice.get_scene()
        lattice_out = struct_out.lattice.get_scene(color="red")

        scene = Scene("lattices", contents=[lattice_in, lattice_out])

        return html.Div(
            [CrystalToolkitScene(data=scene.to_json())],
            style={"width": "100px", "height": "100px"},
        )
