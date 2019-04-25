"""
Link up the StructureMoleculeComponent objects to pythreejs
Also includes some helper functions for draw addition objects using pythreejs
"""

from pythreejs import MeshLambertMaterial, Mesh, SphereBufferGeometry, CylinderBufferGeometry, Object3D, LineSegments2, LineSegmentsGeometry, LineMaterial, Scene, AmbientLight, PerspectiveCamera, Renderer, OrbitControls
from crystal_toolkit.components.structure import StructureMoleculeComponent
from IPython.display import display
from scipy.spatial.transform import Rotation as R
import numpy as np

ball = Mesh(
    geometry=SphereBufferGeometry(radius=1, widthSegments=32, heightSegments=16),
    material=MeshLambertMaterial(color='red'),
    position=[0, 1, 0])

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
    if object['type']=='spheres':
        for ipos in object['positions']:
            obj3d = Mesh(
                geometry=SphereBufferGeometry(
                    radius=object['radius'], widthSegments=32, heightSegments=16),
                material=MeshLambertMaterial(color=object["color"]),
                position=ipos)
            obs.append(obj3d)
    elif object['type']=='cylinders':
        for ipos in object['positionPairs']:
            obj3d = _get_cylinder_from_vec(ipos[0], ipos[1], color=object['color'])
            obs.append(obj3d)
    elif object['type']=='lines':
        for ipos, jpos in zip(object['positions'][::2], object['positions'][1::2]):
            obj3d = _get_line_from_vec(ipos, jpos)
            obs.append(obj3d)
    return obs

def get_scene(structure):
    """
    :param structure:
    """

    smc = StructureMoleculeComponent(structure, bonded_sites_outside_unit_cell=False, hide_incomplete_bonds=False)
    obs = traverse_scene_object(smc.initial_scene_data)

    scene = Scene(children=[
        obs,
        AmbientLight(color='#FFFFFF', intensity=0.75)
    ])
    c = PerspectiveCamera(position=[10, 10, 10])
    renderer = Renderer(
        camera=c,
        background='black',
        background_opacity=1,
        scene=scene,
        controls=[OrbitControls(controlling=c)],
        width=400,
        height=400)
    display(renderer)


def _get_line_from_vec(v0, v1):
    line = LineSegments2(LineSegmentsGeometry(
        positions=[
            [v0, v1],
        ],
    ), LineMaterial(linewidth=3, color='black'))
    return line

def _get_cube_from_pos(v0, **kwargs):
    pass

def _get_cylinder_from_vec(v0, v1, radius=0.15, color="#FFFFFF"):
    v0 = np.array(v0)
    v1 = np.array(v1)
    vec = v1 - v0
    mid_point = (v0 + v1) / 2.
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
            heightSegments=10),
        material=MeshLambertMaterial(color=color),
        position=tuple(mid_point))
    rot = R.from_rotvec(rot_arg * rot_vec)
    new_bond.quaternion = tuple(rot.as_quat())
    return new_bond
