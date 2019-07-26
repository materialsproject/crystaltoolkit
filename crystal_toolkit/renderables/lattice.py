import numpy as np
from crystal_toolkit.core.scene import Scene, Lines

def get_lattice_scene(lattice, origin=(0, 0, 0), **kwargs):

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

    name = (
        f"a={lattice.a}, b={lattice.b}, c={lattice.c}, "
        f"alpha={lattice.alpha}, beta={lattice.beta}, gamma={lattice.gamma}"
    )

    return Scene(name, contents=[Lines(line_pairs, **kwargs)])
