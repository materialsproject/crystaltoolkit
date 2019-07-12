import numpy as np

from crystal_toolkit.core.scene import Scene, Lines

from pymatgen import Lattice


def get_lattice_scene(self, origin=(0, 0, 0), **kwargs):

    o = -np.array(origin)
    a, b, c = self.matrix[0], self.matrix[1], self.matrix[2]
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

    name = (
        f"a={self.a}, b={self.b}, c={self.c}, "
        f"alpha={self.alpha}, beta={self.beta}, gamma={self.gamma}"
    )

    return Scene(name, contents=[Lines(line_pairs, **kwargs)])


# todo: re-think origin, shift globally at end (scene.origin)
Lattice.get_scene = get_lattice_scene
