import numpy as np

from crystal_toolkit.core.scene import Scene, Lines, Arrows, Spheres

from pymatgen import Lattice


def _axes_from_lattice(self, origin=None, scale=1, offset=0, **kwargs):
    """
    Get the display components of the compass
    :param lattice: the pymatgen Lattice object that contains the primitive
    lattice vectors
    :param origin: the reference position to place the compass
    :param scale: scale all the geometric objects that makes up the compass
    the lattice vectors are normalized before the scaling so everything should
    be the same size
    :param offset: shift the compass from the origin by a ratio of the diagonal
    of the cell relative the size
    :param **kwargs: keyword args to pass to the Arrows initializer
    :return: Scene object
    """

    origin = origin or list([0, 0, 0])

    o = np.array(origin)
    # o = -self.get_cartesian_coords([0.5, 0.5, 0.5])
    # o = o - offset * (self.matrix[0] + self.matrix[1] + self.matrix[2])
    a = self.matrix[0] / np.linalg.norm(self.matrix[0]) * scale
    b = self.matrix[1] / np.linalg.norm(self.matrix[1]) * scale
    c = self.matrix[2] / np.linalg.norm(self.matrix[2]) * scale
    a_arrow = [[o, o + a]]
    b_arrow = [[o, o + b]]
    c_arrow = [[o, o + c]]

    radius_scale = 0.07
    head_scale = 0.24
    head_width = 0.14

    o_sphere = Spheres(positions=[o], color="white", radius=2 * radius_scale * scale)

    return Scene(
        name="axes",
        contents=[
            Arrows(
                a_arrow,
                color="red",
                radius=radius_scale * scale,
                headLength=head_scale * scale,
                headWidth=head_width * scale,
                **kwargs,
            ),
            Arrows(
                b_arrow,
                color="green",
                radius=radius_scale * scale,
                headLength=head_scale * scale,
                headWidth=head_width * scale,
                **kwargs,
            ),
            Arrows(
                c_arrow,
                color="blue",
                radius=radius_scale * scale,
                headLength=head_scale * scale,
                headWidth=head_width * scale,
                **kwargs,
            ),
            o_sphere,
        ],
        origin=origin,
    )


def get_lattice_scene(self, origin=None, show_axes=False, **kwargs):

    o = -np.array((0, 0, 0))
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

    contents = [Lines(line_pairs, **kwargs)]

    if show_axes:
        contents.append(self._axes_from_lattice(origin=origin))

    return Scene(name, contents, origin=origin)


# TODO: re-think origin, shift globally at end (scene.origin)
Lattice._axes_from_lattice = _axes_from_lattice
Lattice.get_scene = get_lattice_scene
