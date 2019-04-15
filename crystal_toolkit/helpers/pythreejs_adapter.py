"""
Link up the StructureMoleculeComponent objects to pythreejs
Also includes some helper functions to draw addition ojects using pythreejs
"""

from pythreejs import *
from pymatgen import MPRester
from crystal_toolkit.components.structure import StructureMoleculeComponent
from crystal_toolkit.helpers.scene import *
from scipy.spatial.transform import Rotation as R

struct = MPRester().get_structure_by_material_id('mp-814')
smc = StructureMoleculeComponent(struct, bonded_sites_outside_unit_cell=False, hide_incomplete_bonds=True)


def show(smc):
    atoms = list(
        filter(lambda x: x['name'] == 'atoms',
               smc.initial_scene_data['contents']))[0]['contents']
    bonds = list(
        filter(lambda x: x['name'] == 'bonds',
               smc.initial_scene_data['contents']))[0]['contents']
    ucell = list(
        filter(lambda x: x['name'] == 'unit_cell',
               smc.initial_scene_data['contents']))[0]['contents']
    scene = []
    for ia in atoms:
        for ipos in ia['positions']:
            ball = Mesh(
                geometry=SphereGeometry(
                    radius=ia['radius'], widthSegments=32, heightSegments=16),
                material=MeshLambertMaterial(color=ia["color"]),
                position=ipos)
            scene.append(ball)

    for ib in bonds:
        for ipos in ib['positionPairs']:
            bond = get_cylinder_from_vec(ipos[0], ipos[1])
            scene.append(bond)
    for ib in bonds:
        for ipos in ib['positionPairs']:
            bond = get_cylinder_from_vec(ipos[0], ipos[1], color=ib['color'])
            scene.append(bond)
    for ib in ucell:
        for ipos, jpos in zip(ib['positions'][::2], ib['positions'][1::2]):
            bond = get_cylinder_from_vec(ipos, jpos, radius = 0.02, color='black')
            last_pos=ipos
            scene.append(bond)
    return scene


def get_cylinder_from_vec(v0, v1, radius=0.15, color="#FFFFFF"):
    v0 = np.array(v0)
    v1 = np.array(v1)
    vec = v1 - v0
    mid_point = (v0 + v1) / 2.
    rot_vec = np.cross([0, 1, 0], vec)
    rot_vec_len = np.linalg.norm(rot_vec)
    rot_vec = rot_vec / rot_vec_len
    rot_arg = np.arccos(np.dot([0, 1, 0], vec) / np.linalg.norm(vec))
    rot = R.from_rotvec(rot_arg * rot_vec)
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
