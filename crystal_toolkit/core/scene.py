from __future__ import annotations

from abc import abstractmethod
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from itertools import chain
from json import dump
from typing import Any, Sequence

"""
This module gives a Python interface to generate JSON for the
CrystalToolkitSceneComponent. To use, create a Scene whose contents can either be a
a list of any of the geometric primitives defined below (e.g. Spheres,
Cylinders, etc.) or can be another Scene. Then use scene_to_json() to convert
the Scene to the JSON format to pass to CrystalToolkitSceneComponent's data attribute.
"""


class Primitive:
    """A Mixin class for standard plottable primitive behavior.

    For now, this just enforces some basic mergeability.
    """

    positions: tuple

    @property
    @abstractmethod
    def key(self):
        raise NotImplementedError

    @classmethod
    def merge(cls, items):
        raise NotImplementedError

    @property
    def bounding_box(self) -> list[list[float]]:
        x, y, z = zip(*self.positions)
        return [[min(x), min(y), min(z)], [max(x), max(y), max(z)]]


@dataclass
class Scene:
    """A Scene is defined by its name (a string, does not have to be unique), and its contents (a
    list of geometric primitives or other Scenes).
    """

    name: str  # name for the scene, does not have to be unique
    contents: list = field(default_factory=list)
    origin: Sequence[float] = field(default=(0, 0, 0))
    visible: bool = True
    lattice: list[list[float]] | None = None
    _meta: dict | None = None

    def __add__(self, other):
        """For convenience to combine multiple scenes.

        No good way to decide what origin to set for the new scene.

        :param other: another Scene
        """
        return Scene(
            name=f"{self.name}_{other.name}",
            contents=[*self.contents, other.contents],
            origin=self.origin,
            visible=self.visible,
            lattice=self.lattice,
            _meta={self.name: self._meta, other.name: other._meta},
        )

    def _repr_mimebundle_(self, include=None, exclude=None):
        """Render Scenes using crystaltoolkit-extension for Jupyter Lab."""
        return {
            "application/vnd.mp.ctk+json": self.to_json(),
            "text/plain": repr(self),
        }

    def to_json(self):
        """Convert a Scene into JSON. It will implicitly assume all None values means that attribute
        uses its default value, and so will be removed from the JSON to reduce the file size of the
        resulting JSON.

        Note that this function actually returns a Python dict, but in a format
        that can be converted to a JSON string using the standard library JSON
        encoder.

        :param scene: A Scene object
        :return: dict in a format that can be parsed by CrystalToolkitSceneComponent
        """
        merged_scene = Scene(
            name=self.name,
            contents=self.merge_primitives(self.contents),
            origin=self.origin,
            lattice=self.lattice,
        )

        def remove_defaults(scene_dict):
            """Reduce file size of JSON by removing any key which is just its default value."""
            trimmed_dict = {}
            for key, val in scene_dict.items():
                if isinstance(val, dict):
                    val = remove_defaults(val)  # noqa: PLW2901
                elif isinstance(val, list):
                    trimmed_dict[key] = [
                        remove_defaults(item) if isinstance(item, dict) else item
                        for item in val
                    ]
                elif val is not None:
                    trimmed_dict[key] = val
            return trimmed_dict

        return remove_defaults(asdict(merged_scene))

    def to_plotly_json(self):
        """Easy way to allow Scene objects to be returned from callbacks."""
        return self.to_json()

    def to(self, filename):
        """Write a Scene to a file. Can be opened by Jupyter Lab if Crystal Toolkit extension
        installed.

        :param filename: The filename (can include path),
        an extension will be set if not supplied.
        """
        # TODO: find a way to keep the original MSONable object + scene generation options alongside
        if not filename.endswith(".ctk.json"):
            filename += ".ctk.json"
        with open(filename, "w") as file:
            dump(self.to_json(), file)

    @property
    def bounding_box(self) -> list[list[float]]:
        """Returns the bounding box coordinates."""
        if len(self.contents) > 0:
            min_list, max_list = zip(*[p.bounding_box for p in self.contents])
            min_x, min_y, min_z = map(min, zip(*min_list))
            max_x, max_y, max_z = map(max, zip(*max_list))

            return [[min_x, min_y, min_z], [max_x, max_y, max_z]]
        return [[0, 0, 0], [0, 0, 0]]

    @staticmethod
    def merge_primitives(primitives):
        """If primitives are of the same type but differ only in position, they are merged together.
        This is a small optimization, has not been benchmarked.

        :param primitives: list of primitives (Spheres, Cylinders, etc.)
        :return: list of primitives
        """
        mergeable = defaultdict(list)
        remainder = []

        for primitive in primitives:
            if isinstance(primitive, Scene):
                primitive.contents = Scene.merge_primitives(primitive.contents)
                remainder.append(primitive)
            elif isinstance(primitive, Primitive):
                mergeable[primitive.key].append(primitive)
            else:
                remainder.append(primitive)

        merged = [v[0].merge(v) for v in mergeable.values()]

        return merged + remainder


@dataclass
class Spheres(Primitive):
    """Create a set of spheres. All spheres will have the same color, radius and segment size (if
    only drawing a section of a sphere).

    :param positions: This is a list of lists corresponding to the vector
    positions of the spheres.
    :param color: Sphere color as a hexadecimal string, e.g. #ff0000
    :param radius: The radius of the sphere, defaults to 1.
    :param phiStart: Start angle in radians if drawing only a section of the
    sphere, defaults to 0
    :param phiEnd: End angle in radians if drawing only a section of the
    sphere, defaults to 2*pi
    :param visible: If False, will hide the object by default.
    :param reference: name to reference the primitive for callback
    :param clickable: if true, allows this primitive to be clicked
    and trigger and event
    """

    positions: list[list[float]]
    _animate: list[list[float]] | None = None
    color: str | None = None
    radius: float | None = None
    phiStart: float | None = None
    phiEnd: float | None = None
    type: str = field(default="spheres", init=False)  # private field
    visible: bool | None = None
    tooltip: str | None = None
    clickable: bool = False
    reference: str | None = None
    _meta: Any = None

    @property
    def key(self):
        return f"sphere_{self.color}_{self.radius}_{self.phiStart}_{self.phiEnd}_{self.clickable}_{self.tooltip}"

    @classmethod
    def merge(cls, sphere_list):
        new_positions = list(
            chain.from_iterable([sphere.positions for sphere in sphere_list])
        )
        return cls(
            positions=new_positions,
            color=sphere_list[0].color,
            radius=sphere_list[0].radius,
            phiStart=sphere_list[0].phiStart,
            phiEnd=sphere_list[0].phiEnd,
            visible=sphere_list[0].visible,
            clickable=sphere_list[0].clickable,
            tooltip=sphere_list[0].tooltip,
        )


@dataclass
class Ellipsoids(Primitive):
    """Create a set of ellipsoids. All ellipsoids will have the same color, radius and segment size
    (if only drawing a section of a ellipsoid).

    :param scale: This is the scale to apply to the x,y and z axis of the ellipsoid prior to rotation to the target axes
    :param positions: This is a list of lists corresponding to the vector
    positions of the ellipsoids.
    :param rotate_to: This is a list of vectors that specify the direction the major axis of the ellipsoid should point
        towards. The major axis is the z-axis: (0,0,1)
    :param color: Ellipsoid color as a hexadecimal string, e.g. #ff0000
    :param phiStart: Start angle in radians if drawing only a section of the
    ellipsoid, defaults to 0
    :param phiEnd: End angle in radians if drawing only a section of the
    ellipsoid, defaults to 2*pi
    :param visible: If False, will hide the object by default.
    :param reference: name to reference the primitive for callback
    :param clickable: if true, allows this primitive to be clicked
    and trigger and event
    """

    scale: list[float]
    positions: list[list[float]]
    rotate_to: list[list[float]]
    _animate: list[list[float]] | None = None
    color: str | None = None
    phiStart: float | None = None
    phiEnd: float | None = None
    type: str = field(default="ellipsoids", init=False)  # private field
    visible: bool | None = None
    clickable: bool = False
    reference: str | None = None
    _meta: Any = None

    @property
    def key(self):
        return f"ellipsoid_{self.color}_{self.scale}_{self.phiStart}_{self.phiEnd}"

    @classmethod
    def merge(cls, ellipsoid_list):
        new_positions = list(
            chain.from_iterable([ellipsoid.positions for ellipsoid in ellipsoid_list])
        )
        rotate_to = list(
            chain.from_iterable([ellipsoid.rotate_to for ellipsoid in ellipsoid_list])
        )
        new__animate = list(
            chain.from_iterable(
                [
                    ellipsoid._animate
                    for ellipsoid in ellipsoid_list
                    if ellipsoid._animate
                ]
            )
        )

        return cls(
            positions=new_positions,
            rotate_to=rotate_to,
            _animate=new__animate,
            scale=ellipsoid_list[0].scale,
            color=ellipsoid_list[0].color,
            phiStart=ellipsoid_list[0].phiStart,
            phiEnd=ellipsoid_list[0].phiEnd,
            visible=ellipsoid_list[0].visible,
        )


@dataclass
class Cylinders(Primitive):
    """Create a set of cylinders. All cylinders will have the same color and radius.

    :param positionPairs: This is a list of pairs of lists corresponding to the
    start and end position of the cylinder.
    :param color: Cylinder color as a hexadecimal string, e.g. #ff0000
    :param radius: The radius of the cylinder, defaults to 1.
    :param visible: If False, will hide the object by default.
    :param reference: name to reference the primitive for callback
    :param clickable: if true, allows this primitive to be clicked
    and trigger and event
    """

    positionPairs: list[list[list[float]]]
    _animate: list[list[list[float]]] | None = None
    color: str | None = None
    radius: float | None = None
    type: str = field(default="cylinders", init=False)  # private field
    visible: bool | None = None
    tooltip: str | None = None
    clickable: bool = False
    reference: str | None = None
    _meta: Any = None

    @property
    def key(self):
        return f"cylinder_{self.color}_{self.radius}_{self.reference}_{self.clickable}_{self.tooltip}"

    @classmethod
    def merge(cls, cylinder_list):
        new_positionPairs = list(
            chain.from_iterable([cylinder.positionPairs for cylinder in cylinder_list])
        )

        return cls(
            positionPairs=new_positionPairs,
            color=cylinder_list[0].color,
            radius=cylinder_list[0].radius,
            visible=cylinder_list[0].visible,
            clickable=cylinder_list[0].clickable,
            tooltip=cylinder_list[0].tooltip,
        )

    @property
    def bounding_box(self) -> list[list[float]]:
        x, y, z = zip(*chain.from_iterable(self.positionPairs))
        return [[min(x), min(y), min(z)], [min(x), min(y), min(z)]]


@dataclass
class Cubes(Primitive):
    """Create a set of cubes. All cubes will have the same color and width.

    :param positions: This is a list of lists corresponding to the vector
    positions of the cubes.
    :param color: Cube color as a hexadecimal string, e.g. #ff0000
    :param width: The width of the cube, defaults to 1.
    :param visible: If False, will hide the object by default.
    :param reference: name to reference the primitive for callback
    :param clickable: if true, allows this primitive to be clicked
    and trigger and event
    """

    positions: list[list[float]]
    _animate: list[list[float]] | None = None
    color: str | None = None
    width: float | None = None
    type: str = field(default="cubes", init=False)  # private field
    visible: bool | None = None
    clickable: bool = False
    reference: str | None = None
    _meta: Any = None

    @property
    def key(self):
        return f"cube_{self.color}_{self.width}_{self.reference}"

    @classmethod
    def merge(cls, cube_list):
        new_positions = list(
            chain.from_iterable([cube.positions for cube in cube_list])
        )
        return cls(
            positions=new_positions,
            color=cube_list[0].color,
            width=cube_list[0].width,
            visible=cube_list[0].visible,
        )


@dataclass
class Lines(Primitive):
    """Create a set of lines. All lines will have the same color, thickness and (optional) dashes.

    :param positions: This is a list of lists corresponding to the positions of
    the lines. Each consecutive pair of vectors corresponds to the start and end
    position of a line segment (line segments do not have to be joined
    together).
    :param color: Line color as a hexadecimal string, e.g. #ff0000
    :param linewidth: The width of the line, defaults to 1
    :param scale: Optional, if provided will set a global scale for line dashes.
    :param dashSize: Optional, if provided will specify length of line dashes.
    :param gapSize: Optional, if provided will specify gap between line dashes.
    :param visible: If False, will hide the object by default.
    :param reference: name to reference the primitive for callback
    :param clickable: if true, allows this primitive to be clicked
    and trigger and event
    """

    positions: list[list[float]]
    _animate: list[list[float]] | None = None
    color: str | None = None
    linewidth: float | None = None
    scale: float | None = None
    dashSize: float | None = None
    gapSize: float | None = None
    type: str = field(default="lines", init=False)  # private field
    visible: bool | None = None
    clickable: bool = False
    reference: str | None = None
    _meta: Any = None

    @property
    def key(self):
        return f"line_{self.color}_{self.linewidth}_{self.dashSize}_{self.gapSize}_{self.reference}"

    @classmethod
    def merge(cls, line_list):
        new_positions = list(
            chain.from_iterable([line.positions for line in line_list])
        )
        return cls(
            positions=new_positions,
            color=line_list[0].color,
            linewidth=line_list[0].linewidth,
            scale=line_list[0].scale,
            dashSize=line_list[0].dashSize,
            gapSize=line_list[0].gapSize,
            visible=line_list[0].visible,
        )


@dataclass
class Surface:
    """Define a surface by its vertices.

    Please also provide normals if known. Opacity can be set to enable transparency, but note that
    the current Three.js renderer doesn't support nested transparent objects very well.
    """

    positions: list[list[float]]
    _animate: list[list[float]] | None = None
    normals: list[list[float]] | None = None
    color: str | None = None
    opacity: float | None = None
    show_edges: bool = False
    type: str = field(default="surface", init=False)  # private field
    visible: bool | None = None
    clickable: bool = False
    reference: str | None = None
    _meta: Any = None

    @property
    def bounding_box(self) -> list[list[float]]:
        # Not used in the calculation of the bounding box
        return [[0, 0, 0], [0, 0, 0]]


@dataclass
class Convex:
    """Create a surface from the convex hull formed by list of points.

    Note that at least four points must be specified. The current Three.js renderer uses the
    QuickHull algorithm. Opacity can be set to enable transparency, but note that the current
    Three.js renderer doesn't support nested transparent objects very well.
    """

    positions: list[list[float]]
    _animate: list[list[float]] | None = None
    color: str | None = None
    opacity: float | None = None
    type: str = field(default="convex", init=False)  # private field
    visible: bool | None = None
    clickable: bool = False
    reference: str | None = None
    _meta: Any = None

    @property
    def bounding_box(self) -> list[list[float]]:
        # Not used in the calculation of the bounding box
        return [[0, 0, 0], [0, 0, 0]]


@dataclass
class Arrows(Primitive):
    """Create a set of arrows. All arrows will have the same color radius and head shape.

    :param positionPairs: This is a list of pairs of lists corresponding to the
    start and end position of the cylinder.
    :param color: Cylinder color as a hexadecimal string, e.g. #ff0000
    :param radius: The radius of the cylinder, defaults to 1.
    :param visible: If False, will hide the object by default.
    :param reference: name to reference the primitive for callback
    :param clickable: if true, allows this primitive to be clicked
    and trigger and event
    """

    positionPairs: list[list[list[float]]]
    _animate: list[list[list[float]]] | None = None
    color: str | None = None
    radius: float | None = None
    headLength: float | None = None
    headWidth: float | None = None
    type: str = field(default="arrows", init=False)  # private field
    visible: bool | None = None
    clickable: bool = False
    reference: str | None = None
    _meta: Any = None

    @property
    def key(self):
        return f"arrow_{self.color}_{self.radius}_{self.headLength}_{self.headWidth}_{self.reference}"

    @classmethod
    def merge(cls, arrow_list: list[Arrows]) -> Arrows:
        """Merge a list of arrows into a new Arrows instance.

        Args:
            arrow_list (list[Arrows]): Arrows to merge

        Returns:
            Arrows: Merged arrows
        """
        new_positionPairs = list(
            chain.from_iterable([arrow.positionPairs for arrow in arrow_list])
        )
        return cls(
            positionPairs=new_positionPairs,
            color=arrow_list[0].color,
            radius=arrow_list[0].radius,
            headLength=arrow_list[0].headLength,
            headWidth=arrow_list[0].headWidth,
            visible=arrow_list[0].visible,
        )

    @property
    def bounding_box(self) -> list[list[float]]:
        x, y, z = zip(*chain.from_iterable(self.positionPairs))
        return [[min(x), min(y), min(z)], [max(x), max(y), max(z)]]


@dataclass
class Label:
    """Add a label to an object."""

    label: str
    labelHover: str | None = None
    position: list[list[float]] | None = None
    type: str = field(default="labels", init=False)  # private field
    visible: bool | None = None
    clickable: bool = False
    reference: str | None = None
    _meta: Any = None


@dataclass
class Bezier:
    """A tube shaped by Bézier control points."""

    controlPoints: list[list[list[float]]] | None = None
    color: list[str] | None = None
    radius: list[float] | None = None
    type: str = field(default="bezier", init=False)  # private field
    visible: bool | None = None
    clickable: bool = False
    reference: str | None = None
    _meta: Any = None
