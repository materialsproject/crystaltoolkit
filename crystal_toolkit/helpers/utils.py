import numpy as np

from fractions import Fraction
from skimage import measure


def pretty_frac_format(x):
    x = x % 1
    fraction = Fraction(x).limit_denominator(8)
    if np.allclose(x, 1):
        x_str = "0"
    elif not np.allclose(x, float(fraction)):
        x = np.around(x, decimals=3)
        x_str = f"{x:.3g}"
    else:
        x_str = str(fraction)
    return x_str

def get_mesh(chgcar, data_tag='total', isolvl=2.0, step_size = 4):
    '''
    Return the charge density isolevel represented as a set of vertices and face
    :param chgcar:  Pymatgen charge density object
    :param data_tag:  The key value to take: (ie chgcar.data[data_tag])
    :param isolvl: iso-level
    :param step_size: stepping parameter for the marching cubes algorithm
    :return:
    vertices and faces from the marching cube algorithm
    '''
    tmp_chg=chgcar.data[data_tag]
    # padding the periodic ends
    tmp_chg=np.concatenate((tmp_chg,tmp_chg[:1,:,:]), axis=0)
    tmp_chg=np.concatenate((tmp_chg,tmp_chg[:,:1,:]), axis=1)
    tmp_chg=np.concatenate((tmp_chg,tmp_chg[:,:,:1]), axis=2)
    vertices, faces, normals, values = measure.marching_cubes_lewiner(tmp_chg,
                                                                      level=isolvl,
                                                                      step_size=step_size)
    vertices = vertices/(tmp_chg.shape - np.array([1,1,1]))  # transform to fractional coordinates
    vertices = np.dot(vertices-0.5, cc.structure.lattice.matrix) # transform to cartesian
    return vertices, faces

def get_pos(struct, pos):
    # TODO make this return a list of lists
    ans = np.dot(np.array(pos) - 0.5*np.ones_like(pos), struct.lattice.matrix) # transform to cartesian
    for itr in ans:
        yield itr.tolist()
