from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from itertools import chain
from collections import defaultdict
from warnings import warn

"""
This module gives a Python interface to generate JSON for the
Simple3DSceneComponent. To use, create a Scene whose contents can either be a
a list of any of the geometric primitives defined below (e.g. Spheres,
Cylinders, etc.) or can be another Scene. Then use scene_to_json() to convert
the Scene to the JSON format to pass to Simple3DSceneComponent's data attribute.
"""


@dataclass
class Scene:
    """
    A Scene is defined by its name (a string, does not have to be unique),
    and its contents (a list of geometric primitives or other Scenes).
    """

    name: str  # name for the scene, does not have to be unique
    contents: list = field(default_factory=list)
    _meta: Any = None

    def to_json(self):
        """
        Convert a Scene into JSON. It will implicitly assume all None values means
        that that attribute uses its default value, and so will be removed from
        the JSON to reduce the filesize size of the resulting JSON.

        Note that this function actually returns a Python dict, but in a format
        that can be converted to a JSON string using the standard library JSON
        encoder.

        :param scene: A Scene object
        :return: dict in a format that can be parsed by Simple3DSceneComponent
        """

        merged_scene = Scene(
            name=self.name, contents=self.merge_primitives(self.contents)
        )

        def remove_defaults(scene_dict):
            trimmed_dict = {}
            for k, v in scene_dict.items():
                if isinstance(v, dict):
                    v = remove_defaults(v)
                elif isinstance(v, list):
                    trimmed_dict[k] = [
                        remove_defaults(item) if isinstance(item, dict) else item
                        for item in v
                    ]
                elif v is not None:
                    trimmed_dict[k] = v
            return trimmed_dict

        return remove_defaults(asdict(merged_scene))

    @staticmethod
    def merge_primitives(primitives):
        """
        If primitives are of the same type but differ only in position, they
        are merged together. This is a small optimization, has not been benchmarked.
        :param primitives: list of primitives (Spheres, Cylinders, etc.)
        :return: list of primitives
        """
        spheres = defaultdict(list)
        cylinders = defaultdict(list)
        remainder = []

        for primitive in primitives:
            if isinstance(primitive, Scene):
                primitive.contents = Scene.merge_primitives(primitive.contents)
                remainder.append(primitive)
            elif isinstance(primitive, Spheres):
                key = f"{primitive.color}_{primitive.radius}_{primitive.phiStart}_{primitive.phiEnd}"
                spheres[key].append(primitive)
            elif isinstance(primitive, Cylinders):
                key = f"{primitive.color}_{primitive.radius}"
                cylinders[key].append(primitive)
            else:
                remainder.append(primitive)

        new_spheres = []
        for key, sphere_list in spheres.items():
            new_positions = list(
                chain.from_iterable([sphere.positions for sphere in sphere_list])
            )
            new_ellipsoids = None
            has_ellipsoids = any(
                [
                    sphere.ellipsoids["rotations"] if sphere.ellipsoids else None
                    for sphere in sphere_list
                ]
            )
            if has_ellipsoids:
                warn("Merging of ellipsoids doesn't work yet.")
                # TODO: should re-think how ellipsoids are stored, dict format is awkward
            # new_ellipsoids_rotations = list(
            #    chain.from_iterable(
            #        [
            #            sphere.ellipsoids["rotations"] if sphere.ellipsoids else None
            #            for sphere in sphere_list
            #        ]
            #    )
            # )
            # new_ellipsoids_scales = list(
            #    chain.from_iterable(
            #        [
            #            sphere.ellipsoids["scales"] if sphere.ellipsoids else None
            #            for sphere in sphere_list
            #        ]
            #    )
            # )
            # if any(new_ellipsoids_rotations):
            #    new_ellipsoids = {
            #        "rotations": new_ellipsoids_rotations,
            #        "scales": new_ellipsoids_scales,
            #    }
            # else:
            #    new_ellipsoids = None
            new_spheres.append(
                Spheres(
                    positions=new_positions,
                    color=sphere_list[0].color,
                    radius=sphere_list[0].radius,
                    phiStart=sphere_list[0].phiStart,
                    phiEnd=sphere_list[0].phiEnd,
                    ellipsoids=new_ellipsoids,
                    visible=sphere_list[0].visible,
                )
            )

        new_cylinders = []
        for key, cylinder_list in cylinders.items():
            new_positionPairs = list(
                chain.from_iterable(
                    [cylinder.positionPairs for cylinder in cylinder_list]
                )
            )
            new_cylinders.append(
                Cylinders(
                    positionPairs=new_positionPairs,
                    color=cylinder_list[0].color,
                    radius=cylinder_list[0].radius,
                    visible=cylinder_list[0].visible,
                )
            )

        return new_spheres + new_cylinders + remainder


@dataclass
class Spheres:
    """
    Create a set of spheres. All spheres will have the same color, radius and
    segment size (if only drawing a section of a sphere).
    :param positions: This is a list of lists corresponding to the vector
    positions of the spheres.
    :param color: Sphere color as a hexadecimal string, e.g. #ff0000
    :param radius: The radius of the sphere, defaults to 1.
    :param phiStart: Start angle in radians if drawing only a section of the
    sphere, defaults to 0
    :param phiEnd: End angle in radians if drawing only a section of the
    sphere, defaults to 2*pi
    :param ellipsoids: Any distortions to apply to the sphere to display
    ellipsoids. This is a dictionary with two keys, "rotations" and "scales",
    where rotations refers to the vector relative to (1, 0, 0) to rotate the
    ellipsoid major axis to align with, and scales refers to the vector to scale
    the ellipsoid by along x, y and z. The dictionary values should be lists of
    lists of the same length as positions, corresponding to a unique
    rotation/scale for each sphere.
    :param visible: If False, will hide the object by default.
    """

    positions: List[List[float]]
    color: Optional[str] = None
    radius: Optional[float] = None
    phiStart: Optional[float] = None
    phiEnd: Optional[float] = None
    ellipsoids: Optional[Dict[str, List[List[float]]]] = None
    type: str = field(default="spheres", init=False)  # private field
    visible: bool = None
    _meta: Any = None


@dataclass
class Cylinders:
    """
    Create a set of cylinders. All cylinders will have the same color and
    radius.
    :param positionPairs: This is a list of pairs of lists corresponding to the
    start and end position of the cylinder.
    :param color: Cylinder color as a hexadecimal string, e.g. #ff0000
    :param radius: The radius of the cylinder, defaults to 1.
    :param visible: If False, will hide the object by default.
    """

    positionPairs: List[List[List[float]]]
    color: Optional[str] = None
    radius: Optional[float] = None
    type: str = field(default="cylinders", init=False)  # private field
    visible: bool = None
    _meta: Any = None


@dataclass
class Cubes:
    """
    Create a set of cubes. All cubes will have the same color and width.
    :param positions: This is a list of lists corresponding to the vector
    positions of the cubes.
    :param color: Cube color as a hexadecimal string, e.g. #ff0000
    :param width: The width of the cube, defaults to 1.
    :param visible: If False, will hide the object by default.
    """

    positions: List[List[float]]
    color: Optional[str] = None
    width: Optional[float] = None
    type: str = field(default="cubes", init=False)  # private field
    visible: bool = None
    _meta: Any = None


@dataclass
class Lines:
    """
    Create a set of lines. All lines will have the same color, thickness and
    (optional) dashes.
    :param positions: This is a list of lists corresponding to the positions of
    the lines. Each consecutive pair of vectors corresponds to the start and end
    position of a line segment (line segments do not have to be joined
    together).
    :param color: Line color as a hexadecimal string, e.g. #ff0000
    :param lineWidth: The width of the line, defaults to 1
    :param scale: Optional, if provided will set a global scale for line dashes.
    :param dashSize: Optional, if provided will specify length of line dashes.
    :param gapSize: Optional, if provided will specify gap between line dashes.
    :param visible: If False, will hide the object by default.
    """

    positions: List[List[float]]
    color: str = None
    lineWidth: float = None
    scale: float = None
    dashSize: float = None
    gapSize: float = None
    type: str = field(default="lines", init=False)  # private field
    visible: bool = None
    _meta: Any = None


@dataclass
class Surface:
    """
    Define a surface by its vertices. Please also provide normals if known.
    Opacity can be set to enable transparency, but note that the current
    Three.js renderer doesn't support nested transparent objects very well.
    """

    positions: List[List[float]]
    normals: Optional[List[List[float]]] = None
    color: str = None
    opacity: float = None
    type: str = field(default="surface", init=False)  # private field
    visible: bool = None
    _meta: Any = None


@dataclass
class Convex:
    """
    Create a surface from the convex hull formed by list of points. Note that
    at least four points must be specified. The current Three.js renderer uses
    the QuickHull algorithm. Opacity can be set to enable transparency, but note
    that the current Three.js renderer doesn't support nested transparent
    objects very well.
    """

    positions: List[List[float]]
    color: str = None
    opacity: float = None
    type: str = field(default="convex", init=False)  # private field
    visible: bool = None
    _meta: Any = None


@dataclass
class Arrows:
    """
    Create a set of arrows. All arrows will have the same color radius and
    head shape.
    :param positionPairs: This is a list of pairs of lists corresponding to the
    start and end position of the cylinder.
    :param color: Cylinder color as a hexadecimal string, e.g. #ff0000
    :param radius: The radius of the cylinder, defaults to 1.
    :param visible: If False, will hide the object by default.
    """

    positionPairs: List[List[List[float]]]
    color: Optional[str] = None
    radius: Optional[float] = None
    headLength: Optional[float] = None
    headWidth: Optional[float] = None
    type: str = field(default="arrows", init=False)  # private field
    visible: bool = None
    _meta: Any = None


@dataclass
class Labels:
    """
    Not implemented yet.
    """

    type: str = field(default="labels", init=False)  # private field
    visible: bool = None
    _meta: Any = None
