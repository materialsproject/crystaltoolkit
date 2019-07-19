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
from pymatgen import Structure

import numpy as np
import warnings
from crystal_toolkit.renderables import *
from crystal_toolkit.core.scene import Scene as CrystalToolkitScene
from crystal_toolkit.components.structure import StructureMoleculeComponent


def traverse_scene_object(scene_data, parent=None):
    """
    Recursivesly populate a scene object with tree of children
    :param scene_data:
    :param parent:
    :return:
    """
    for sub_object in scene_data["contents"]:
        if "type" in sub_object.keys():
            parent.add(convert_object_to_pythreejs(sub_object))
        else:
            new_parent = Object3D(name=sub_object["name"])
            if parent is None:
                parent = new_parent
            else:
                parent.add(new_parent)
            traverse_scene_object(sub_object, parent)
    return parent


def convert_object_to_pythreejs(object):
    """
    Cases for the conversion
    :return:
    """
    obs = []
    if object["type"] == "spheres":
        for ipos in object["positions"]:
            obj3d = Mesh(
                geometry=SphereBufferGeometry(
                    radius=object["radius"], widthSegments=32, heightSegments=16
                ),
                material=MeshLambertMaterial(color=object["color"]),
                position=ipos,
            )
            obs.append(obj3d)
    elif object["type"] == "cylinders":
        for ipos in object["positionPairs"]:
            obj3d = _get_cylinder_from_vec(ipos[0], ipos[1], color=object["color"])
            obs.append(obj3d)
    elif object["type"] == "lines":
        for ipos, jpos in zip(object["positions"][::2], object["positions"][1::2]):
            obj3d = _get_line_from_vec(ipos, jpos)
            obs.append(obj3d)
    else:
        warnings.warn(
            f"Primitive type {object['type']} has not been implemented for this renderer."
        )
    return obs


def view(obj_or_scene, **kwargs):
    """
    :param obj: input structure
    """
    print(isinstance(obj_or_scene, Structure))
    if isinstance(obj_or_scene, CrystalToolkitScene):
        scene = obj_or_scene
    elif hasattr(obj_or_scene, "get_scene"):
        scene = obj_or_scene.get_scene(**kwargs)
    elif isinstance(obj_or_scene, Structure):
        scene = StructureMoleculeComponent._preprocess_input_to_graph(obj_or_scene).get_scene(**kwargs)
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
    scene = Scene(children=list(obs.children))
    box = Box3.exec_three_obj_method("setFromObject", scene)
    extent = (
        max(box.max.z - box.min.z, box.max.y - box.min.y, box.max.x - box.min.x) * 1.2
    )
    camera = OrthographicCamera(
        -extent, extent, extent, -extent, -2000, 2000, position=(0, 0, 2)
    )
    camera.children.extend(
        [
            AmbientLight(color="#cccccc", intensity=0.75),
            DirectionalLight(color="#ccaabb", position=[0, 20, 10], intensity=0.5),
        ]
    )
    renderer = Renderer(
        camera=camera,
        background="white",
        background_opacity=1,
        scene=scene,
        controls=[OrbitControls(controlling=camera)],
        width=500,
        height=500,
        antialias=True,
    )
    display(renderer)


def _get_line_from_vec(v0, v1):
    line = LineSegments2(
        LineSegmentsGeometry(positions=[[v0, v1]]),
        LineMaterial(linewidth=3, color="black"),
    )
    return line


def _get_cube_from_pos(v0, **kwargs):
    pass


def _get_cylinder_from_vec(v0, v1, radius=0.15, color="#FFFFFF"):
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
            radiusTop=radius,
            radiusBottom=radius,
            height=np.linalg.norm(v1 - v0),
            radialSegments=12,
            heightSegments=10,
        ),
        material=MeshLambertMaterial(color=color),
        position=tuple(mid_point),
    )
    rot = R.from_rotvec(rot_arg * rot_vec)
    new_bond.quaternion = tuple(rot.as_quat())
    return new_bond
