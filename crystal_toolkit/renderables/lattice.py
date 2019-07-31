import numpy as np
from crystal_toolkit.core.scene import Scene, Lines, Arrows, Spheres


class LatticeRenderer:

    scale = 0.7
    offset = 0.15
    compass_style = "corner"

    def __init__(self, scale=0.7, offset=0.15, compass_style="corner"):
        """
        :param scale: scale all the geometric objects that makes up the compass the lattice vectors are normalized before the scaling so everything should be the same size
        :param offset: shift the compass from the origin by a ratio of the diagonal of the cell relative the size 
        """
        self.scale = scale
        self.offset = offset
        self.compass_style = compass_style

    def to_scene(self, lattice, origin=(0, 0, 0)):

        components = []
        if self.compass_style in ["corner"]:
            return Scene(
                contents=[
                    self.get_compas_scene(lattice, origin),
                    self.get_lattice_scene(lattice, origin),
                ]
            )

        return self.get_lattice_scene(lattice, origin)

    def get_compass_scene(self, lattice, origin=(0, 0, 0), **kwargs):
        """
        Get the display components of the compass
        :param lattice: the pymatgen Lattice object that contains the primitive lattice vectors
        :param origin: the reference position to place the compass
        :return: list of cystal_toolkit.helper.scene objects that makes up the compass
        """
        scale = self.scale
        offset = self.offset
        compass_style = self.compass_style

        o = -np.array(origin)
        o = o - offset * (lattice.matrix[0] + lattice.matrix[1] + lattice.matrix[2])
        a = lattice.matrix[0] / np.linalg.norm(lattice.matrix[0]) * scale
        b = lattice.matrix[1] / np.linalg.norm(lattice.matrix[1]) * scale
        c = lattice.matrix[2] / np.linalg.norm(lattice.matrix[2]) * scale
        a_arrow = [[o, o + a]]
        b_arrow = [[o, o + b]]
        c_arrow = [[o, o + c]]

        o_sphere = Spheres(positions=[o], color="black", radius=0.1 * scale)

        return Scene(
            name="compass",
            contents=[
                Arrows(
                    a_arrow,
                    color="red",
                    radius=0.7 * scale,
                    headLength=2.3 * scale,
                    headWidth=1.4 * scale,
                ),
                Arrows(
                    b_arrow,
                    color="blue",
                    radius=0.7 * scale,
                    headLength=2.3 * scale,
                    headWidth=1.4 * scale,
                ),
                Arrows(
                    c_arrow,
                    color="green",
                    radius=0.7 * scale,
                    headLength=2.3 * scale,
                    headWidth=1.4 * scale,
                ),
                o_sphere,
            ],
        )

    def get_lattice_scene(self, lattice, origin=(0, 0, 0), **kwargs):

        o = -np.array(origin)
        a, b, c = lattice.matrix[0], lattice.matrix[1], lattice.matrix[2]
        line_pairs = [
            o,
            o + a,
            o,
            o + b,
            o,
            o + c,
            o + a,
            o + a + b,
            o + a,
            o + a + c,
            o + b,
            o + b + a,
            o + b,
            o + b + c,
            o + c,
            o + c + a,
            o + c,
            o + c + b,
            o + a + b,
            o + a + b + c,
            o + a + c,
            o + a + b + c,
            o + b + c,
            o + a + b + c,
        ]
        line_pairs = [line.tolist() for line in line_pairs]

        return Scene(name="lattice", contents=[Lines(line_pairs, **kwargs)])
