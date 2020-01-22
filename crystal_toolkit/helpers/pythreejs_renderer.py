"""
Link up the StructureMoleculeComponent objects to pythreejs
Also includes some helper functions for draw addition objects using pythreejs
"""

import logging
import warnings
from math import isnan

import numpy as np
from IPython.display import display
from pymatgen import Structure
from pymatgen.analysis.graphs import StructureGraph
from pythreejs import (
    BufferAttribute,
    EdgesGeometry,
    BufferGeometry,
    MeshLambertMaterial,
    Mesh,
    SphereBufferGeometry,
    CylinderBufferGeometry,
    Object3D,
    LineSegments,
    LineSegments2,
    LineSegmentsGeometry,
    LineBasicMaterial,
    LineMaterial,
    # LineDashedMaterial,
    # Box3,
    Scene,
    AmbientLight,
    Renderer,
    OrbitControls,
    OrthographicCamera,
    DirectionalLight,
)
from scipy.spatial.transform import Rotation as R

from crystal_toolkit.helpers.utils import update_object_args

logger = logging.getLogger(__name__)


def _traverse_scene_object(scene_data, parent=None):
    """
    Recursivesly populate a nested Object3D object from pythreejs
    using the same tree structure from crystaltoolkit

    :param scene_data: The content of the current branch of the Scene object
    :param parent: Reference to the parent in the pythreejs tree
        (default: {None} means you are at the root)
    :return: Object3D of the current pythreejs object with all the children fully populated
    """

    if parent is None:
        # At the tree root
        new_parent = Object3D(name=scene_data.name)
        parent = new_parent

    for sub_object in scene_data.contents:
        if isinstance(sub_object, list):
            for iobj in sub_object:
                _traverse_scene_object(iobj, parent)
            continue
        elif hasattr(sub_object, "type"):
            parent.add(_convert_object_to_pythreejs(sub_object))
        else:
            new_parent = Object3D(name=sub_object.name)
            parent.add(new_parent)
            _traverse_scene_object(sub_object, parent)
    return parent


def _convert_object_to_pythreejs(scene_obj):
    """
    Convert different primitive geometries of crystal toolkit objects
    to pythreejs geometry objects

    :param scene_obj: primitive object from crystal_toolkit.core.scene
    :return: List[Object3D] from pythreejs
    """

    obs = []
    if scene_obj.type == "spheres":
        obs.extend(_get_spheres(scene_obj))
    elif scene_obj.type == "surface":
        obj3d, edges = _get_surface_from_positions(
            scene_obj.positions, scene_obj.__dict__, draw_edges=scene_obj.show_edges
        )
        obs.append(obj3d)
        obs.append(edges)
    elif scene_obj.type == "cylinders":
        for ipos in scene_obj.positionPairs:
            obj3d = _get_cylinder_from_vec(
                tuple(ipos[0]), tuple(ipos[1]), scene_obj.__dict__
            )
            obs.append(obj3d)
    elif scene_obj.type == "lines":
        for ipos, jpos in zip(scene_obj.positions[::2], scene_obj.positions[1::2]):
            logger.debug(scene_obj.__dict__)
            obj3d = _get_line_from_vec(tuple(ipos), tuple(jpos), scene_obj.__dict__)
            obs.append(obj3d)
    else:
        warnings.warn(
            f"Primitive type {scene_obj.type} has not been implemented for this renderer."
        )
    return obs


def view(renderable_obj, **kwargs):
    """
    View a renderable object such as Structure, Molecule, etc.

    :param renderable_obj: Any Object with a get_scene method
    :param kwargs: keyword args to pass to the get_scene method
    :return:
    """

    # convex types are not implemented in pythreejs
    if isinstance(renderable_obj, Structure) or isinstance(
        renderable_obj, StructureGraph
    ):
        kwargs["explicitly_calculate_polyhedra_hull"] = True

    display_scene(renderable_obj.get_scene(**kwargs))


def display_scene(scene, size=500):
    """
    Render a Scene object with pythreejs.
    :param scene: Scene object
    :param size: Display size
    :return:
    """

    obs = _traverse_scene_object(scene)

    logger.debug(type(obs))
    scene2render = Scene(children=list(obs.children))
    logger.debug(len(scene2render.children))
    # cannot use the setFromObject function because the function call is asyncronous
    # https://github.com/jupyter-widgets/pythreejs/issues/282
    bounding_box = scene.bounding_box
    extent = max([p[1] - p[0] for p in zip(*bounding_box)]) * 1.2
    logger.debug(f"extent : {extent}")
    camera = OrthographicCamera(
        -extent, +extent, extent, -extent, -2000, 2000, position=[0, 0, 10]
    )
    origin = scene.origin or (0, 0, 0)
    cam_target = tuple(-i for i in origin)
    controls = OrbitControls(target=cam_target, controlling=camera)
    camera.lookAt(cam_target)

    scene2render.children = scene2render.children + (
        AmbientLight(color="#cccccc", intensity=0.75),
        DirectionalLight(color="#ccaabb", position=[0, 20, 10], intensity=0.5),
        camera,
    )
    renderer = Renderer(
        camera=camera,
        background="white",
        background_opacity=1,
        scene=scene2render,
        controls=[controls],
        width=size,
        height=size,
        antialias=True,
    )
    logger.debug("Start drawing to the notebook")
    display(renderer)


def _get_line_from_vec(v0, v1, scene_args):
    """
    Draw the line given the two endpoints, some Three.js capabilities still
    don't work well in pythreejs (unable to update linewidth and such)
    LineSegments2 is the only one that has been tested successfully, but
    it cannot handle LineDashedMaterial
    :param v0: list, one endpoint of line
    :param v1: list, other endpoint of line
    :param scene_args: dict, properties of the line (line_width and color)
    :return: pythreejs object that displays the line segment
    """
    obj_args = update_object_args(scene_args, "Lines", ["linewidth", "color"])
    logger.debug(obj_args)
    line = LineSegments2(
        LineSegmentsGeometry(positions=[[v0, v1]]),
        LineMaterial(**obj_args),  # Dashed lines do not work in pythreejs yet
    )
    return line


def _get_spheres(ctk_scene, d_args=None):

    if ctk_scene.phiEnd and ctk_scene.phiStart:
        phi_length = ctk_scene.phiEnd - ctk_scene.phiStart
    else:
        phi_length = np.pi * 2

    return [
        Mesh(
            geometry=SphereBufferGeometry(
                radius=ctk_scene.radius,
                phiStart=ctk_scene.phiStart or 0,
                phiLength=phi_length,
                widthSegments=32,
                heightSegments=32,
            ),
            material=MeshLambertMaterial(color=ctk_scene.color),
            position=tuple(ipos),
        )
        for ipos in ctk_scene.positions
    ]


def _get_surface_from_positions(positions, d_args, draw_edges=False):
    # get defaults
    obj_args = update_object_args(d_args, "Surfaces", ["color", "opacity"])
    num_triangle = len(positions) / 3.0
    assert num_triangle.is_integer()
    # make decision on transparency
    if obj_args["opacity"] > 0.99:
        transparent = False
    else:
        transparent = True

    num_triangle = int(num_triangle)
    index_list = [[itr * 3, itr * 3 + 1, itr * 3 + 2] for itr in range(num_triangle)]
    # Vertex ositions as a list of lists
    surf_vertices = BufferAttribute(array=positions, normalized=False)
    # Indices
    surf_indices = BufferAttribute(
        array=np.array(index_list, dtype=np.uint16).ravel(), normalized=False
    )
    geometry = BufferGeometry(
        attributes={"position": surf_vertices, "index": surf_indices}
    )
    new_surface = Mesh(
        geometry=geometry,
        material=MeshLambertMaterial(
            color=obj_args["color"],
            side="DoubleSide",
            transparent=transparent,
            opacity=obj_args["opacity"],
        ),
    )
    if draw_edges == True:
        edges = EdgesGeometry(geometry)
        edges_lines = LineSegments(edges, LineBasicMaterial(color=obj_args["color"]))
        return new_surface, edges_lines
    else:
        return new_surface, None


def _get_cube_from_pos(v0, **kwargs):
    warnings.warn("Rendering cubes not yet implemented.")
    pass


def _get_cylinder_from_vec(v0, v1, d_args=None):
    """
    Draw the cylinder given the two endpoints.

    :param v0: list, one endpoint of line
    :param v1: list, other endpoint of line
    :param d_args: dict, properties of the line (line_width and color)
    :return: Mesh, pythreejs object that displays the cylinders
    """
    obj_args = update_object_args(d_args, "Cylinders", ["radius", "color"])
    v0 = np.array(v0)
    v1 = np.array(v1)
    vec = v1 - v0
    mid_point = (v0 + v1) / 2.0
    rot_vec = np.cross([0, 1, 0], vec)
    rot_vec_len = np.linalg.norm(rot_vec)
    rot_vec = rot_vec / rot_vec_len
    rot_arg = np.arccos(np.dot([0, 1, 0], vec) / np.linalg.norm(vec))
    new_bond = Mesh(
        geometry=CylinderBufferGeometry(
            radiusTop=obj_args["radius"],
            radiusBottom=obj_args["radius"],
            height=np.linalg.norm(v1 - v0),
            radialSegments=12,
            heightSegments=10,
        ),
        material=MeshLambertMaterial(color=obj_args["color"]),
        position=tuple(mid_point),
    )
    rot = R.from_rotvec(rot_arg * rot_vec)
    quat = tuple(rot.as_quat())
    if any(isnan(itr_q) for itr_q in quat):
        new_bond.quaternion = (0, 0, 0, 0)
    else:
        new_bond.quaternion = quat

    return new_bond
