"""
Link up the StructureMoleculeComponent objects to pythreejs
Also includes some helper functions for draw addition objects using pythreejs
"""

from pythreejs import (
    MeshLambertMaterial,
    Mesh,
    SphereBufferGeometry,
    CylinderBufferGeometry,
    Object3D,
    LineSegments2,
    LineSegmentsGeometry,
    LineMaterial,
    LineDashedMaterial,
    Scene,
    AmbientLight,
    Renderer,
    OrbitControls,
    OrthographicCamera,
    DirectionalLight,
    Box3,
)

from IPython.display import display
from scipy.spatial.transform import Rotation as R
from pymatgen import Structure, Molecule

import numpy as np
import warnings
import os
import json
from collections import defaultdict
from crystal_toolkit.renderables import *
from crystal_toolkit.core.scene import Scene as CrystalToolkitScene
from crystal_toolkit.components.structure import StructureMoleculeComponent

import logging

logger = logging.getLogger('crystaltoolkit.pythreejs_renderer')

# Populate the default values from the JSON file
_DEFAULTS = defaultdict(lambda: None)
default_js = os.path.join(os.path.join(os.path.dirname(
    os.path.abspath(__file__))), "../core/", "defaults.js")
with open(default_js) as handle:
    _DEFAULTS.update(json.loads(handle.read()))


def traverse_scene_object(scene_data, parent=None):
    """
    Recursivesly populate a scene object with tree of children 
    :param scene_data:
    :param parent:
    :return:
    """

    if parent is None:
        # At the tree root
        new_parent = Object3D(name=scene_data.name)
        parent = new_parent

    for sub_object in scene_data.contents:
        if type(sub_object) == list:
            for iobj in sub_object:
                traverse_scene_object(iobj, parent)
            continue
        elif hasattr(sub_object, "type"):
            parent.add(convert_object_to_pythreejs(sub_object))
        else:
            new_parent = Object3D(name=sub_object.name)
            parent.add(new_parent)
            traverse_scene_object(sub_object, parent)
    return parent


def convert_object_to_pythreejs(scene_obj):
    """
    Cases for the conversion
    :return:
    """
    obs = []
    if scene_obj.type == "spheres":
        for ipos in scene_obj.positions:
            obj3d = Mesh(
                geometry=SphereBufferGeometry(
                    radius=scene_obj.radius, dthSegments=32, heightSegments=16
                ),
                material=MeshLambertMaterial(color=scene_obj.color),
                position=tuple(ipos),
            )
            obs.append(obj3d)
    elif scene_obj.type == "cylinders":
        for ipos in scene_obj.positionPairs:
            obj3d = _get_cylinder_from_vec(
                tuple(ipos[0]), tuple(ipos[1]), scene_obj.__dict__)
            obs.append(obj3d)
    elif scene_obj.type == "lines":
        for ipos, jpos in zip(scene_obj.positions[::2], scene_obj.positions[1::2]):
            logger.debug(scene_obj.__dict__)
            obj3d = _get_line_from_vec(
                tuple(ipos), tuple(jpos), scene_obj.__dict__)
            obs.append(obj3d)
    else:
        warnings.warn(
            f"Primitive type {scene_obj.type} has not been implemented for this renderer."
        )
    return obs


def view(molecule_or_structure, **kwargs):
    """
    View a pymatgen Molecule or Structure object interactively in a
    Jupyter notebook.
    :param molecule_or_structure: Molecule or Structure object
    """
    obj_or_scene = molecule_or_structure
    if isinstance(obj_or_scene, CrystalToolkitScene):
        scene = obj_or_scene
    elif hasattr(obj_or_scene, "get_scene"):
        scene = obj_or_scene.get_scene(**kwargs)
    # TODO: next two elif statements are only here until Molecule and Structure have get_scene()
    elif isinstance(obj_or_scene, Structure):
        # TODO Temporary place holder for render structure until structure.get_scene() is implemented
        smc = StructureMoleculeComponent(
            obj_or_scene, static=True, draw_image_atoms=False, bonded_sites_outside_unit_cell=False, hide_incomplete_bonds=True)
        scene = smc.initial_graph.get_scene(
            draw_image_atoms=False, bonded_sites_outside_unit_cell=False, hide_incomplete_edges=True, **kwargs)
    elif isinstance(obj_or_scene, Molecule):
        # TODO Temporary place holder for render molecules
        smc = StructureMoleculeComponent(
            obj_or_scene, static=True, draw_image_atoms=False, bonded_sites_outside_unit_cell=False, hide_incomplete_bonds=True)
        scene = smc.initial_graph.get_scene(
            draw_image_atoms=False, bonded_sites_outside_unit_cell=False, hide_incomplete_edges=True, **kwargs)
    else:
        raise ValueError(
            "Only Scene objects or objects with get_scene() methods "
            "can be displayed."
        )
    display_scene(scene)


def display_scene(scene):
    """
    :param smc: input structure structure molecule component
    """
    obs = traverse_scene_object(scene)
    logger.debug(type(obs))
    scene2render = Scene(children=list(obs.children))
    logger.debug(len(scene2render.children))
    # cannot use the setFromObject function because the function call is asyncronous
    # https://github.com/jupyter-widgets/pythreejs/issues/282
    bounding_box = scene.bounding_box
    extent = max([p[1]-p[0] for p in zip(*bounding_box)]) * 1.2
    logger.debug(f"extent : {extent}")
    camera = OrthographicCamera(
        -extent, extent, extent, -extent, -2000, 2000, position=(0, 0, 2)
    )
    scene2render.children = scene2render.children + (
        AmbientLight(color="#cccccc", intensity=0.75),
        DirectionalLight(color="#ccaabb", position=[0, 20, 10], intensity=0.5),
    )
    renderer = Renderer(
        camera=camera,
        background="white",
        background_opacity=1,
        scene=scene2render,
        controls=[OrbitControls(controlling=camera)],
        width=500,
        height=500,
        antialias=True,
    )
    logger.debug("Start drawing to the notebook")
    display(renderer)


def _get_line_from_vec(v0, v1, d_args):
    """Draw the line given the two endpoints, some threejs functionalities still don't work well in pythreejs (unable to update linewidth and such) 
    LineSegments2 is the onlyone that has tested sucessfully but it cannot handle LineDashedMaterial
    
    Args:
        v0 (list): one endpoint of line
        v1 (list): other endpoint of line
        d_args (dict): properties of the line (line_width and color)
    
    Returns:
        LineSegments2: Pythreejs object that displays the line sement
    """
    allowed_args = ['linewidth', 'color']
    obj_args = dict(
        {k: v for k, v in (_DEFAULTS['Lines'] or {}).items() if k in allowed_args})
    obj_args.update({k: v for k, v in (d_args or {}).items()
                     if k in allowed_args and v != None})
    logger.debug(obj_args)
    line = LineSegments2(
        LineSegmentsGeometry(positions=[[v0, v1]]),
        LineMaterial(**obj_args),  # Dashed lines do not work in pythreejs yet
    )
    return line


def _get_cube_from_pos(v0, **kwargs):
    pass


def _get_cylinder_from_vec(v0, v1, d_args=None):
    """Draw the cylinder given the two endpoints.
    
    Args:
        v0 (list): one endpoint of line
        v1 (list): other endpoint of line
        d_args (dict): properties of the line (line_width and color)
    
    Returns:
        Mesh: Pythreejs object that displays the cylinders
    """
    allowed_args = ['radius', 'color']
    obj_args = dict(
        {k: v for k, v in (_DEFAULTS['Cylinders'] or {}).items() if k in allowed_args})
    obj_args.update({k: v for k, v in (d_args or {}).items()
                     if k in allowed_args and v != None})

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
            radiusTop=obj_args['radius'],
            radiusBottom=obj_args['radius'],
            height=np.linalg.norm(v1 - v0),
            radialSegments=12,
            heightSegments=10,
        ),
        material=MeshLambertMaterial(color=obj_args['color']),
        position=tuple(mid_point),
    )
    rot = R.from_rotvec(rot_arg * rot_vec)
    new_bond.quaternion = tuple(rot.as_quat())
    return new_bond
