from crystal_toolkit.core.scene import (
    Primitive,
    Scene,
    Spheres,
    Ellipsoids,
    Cylinders,Cubes,
    Lines,
    Surface,
    Convex,
    Arrows,
)
import pytest


def test_primitive():
    # Ensure abstract properties raise errors
    with pytest.raises(NotImplementedError) as expception_info:
        prim = Primitive()
        prim.key

    with pytest.raises(NotImplementedError) as expception_info:
        Primitive.merge([])

    # Can't test bounding_box since this is a mixin class


def test_spheres():

    sphere = Spheres(positions=[[0, 0, 0]], color="ff0000", radius=1.0)
    sphere2 = Spheres(positions=[[1.0, 0, 0]], color="ff0000", radius=1.0)

    assert sphere.key == "sphere_ff0000_1.0_None_None_None"
    assert sphere2.key == "sphere_ff0000_1.0_None_None_None"

    merged_spheres = Spheres.merge([sphere, sphere2])
    assert merged_spheres.key == "sphere_ff0000_1.0_None_None_None"
    assert len(merged_spheres.positions) == 2

    assert sphere.bounding_box == [[0, 0, 0], [0, 0, 0]]
    assert sphere2.bounding_box == [[1.0, 0, 0], [1.0, 0, 0]]
    assert merged_spheres.bounding_box == [[0, 0, 0], [1.0, 0, 0]]


def test_ellipsoids():

    ellipsoid = Ellipsoids(
        scale=[1, 1, 1], positions=[[0, 0, 0]], rotate_to=[1, 0, 0], color="ff0000"
    )
    ellipsoid2 = Ellipsoids(
        scale=[1, 1, 1], positions=[[1.0, 0, 0]], rotate_to=[1, 1, 0], color="ff0000"
    )

    assert ellipsoid.key == "ellipsoid_ff0000_[1, 1, 1]_None_None_None"
    assert ellipsoid2.key == "ellipsoid_ff0000_[1, 1, 1]_None_None_None"

    merged_ellipsoids = Ellipsoids.merge([ellipsoid, ellipsoid2])
    assert merged_ellipsoids.key == "ellipsoid_ff0000_[1, 1, 1]_None_None_None"
    assert len(merged_ellipsoids.positions) == 2

    assert ellipsoid.bounding_box == [[0, 0, 0], [0, 0, 0]]
    assert ellipsoid2.bounding_box == [[1.0, 0, 0], [1.0, 0, 0]]
    assert merged_ellipsoids.bounding_box == [[0, 0, 0], [1.0, 0, 0]]


def test_cyclinderss():

    cyclinders = Cylinders(
        positionPairs=[[[0, 0, 0], [1.0, 0, 0]]], color="ff0000", radius=1.0
    )
    cyclinders2 = Cylinders(
        positionPairs=[[[1.0, 0, 0], [0, 2.0, 0]]], color="ff0000", radius=1.0
    )

    assert cyclinders.key == "cyclinder_ff0000_1.0_None"
    assert cyclinders2.key == "cyclinder_ff0000_1.0_None"

    merged_cyclinderss = Cylinders.merge([cyclinders, cyclinders2])
    assert merged_cyclinderss.key == "cyclinder_ff0000_1.0_None"
    assert len(merged_cyclinderss.positionPairs) == 2

    assert cyclinders.bounding_box == [[0, 0, 0], [1.0, 0, 0]]
    assert cyclinders2.bounding_box == [[0, 0, 0], [1.0, 2.00, 0]]
    assert merged_cyclinderss.bounding_box == [[0, 0, 0], [1.0, 2.0, 0]]

def test_cubes():

    cube = Cubes(positions=[[0, 0, 0]], color="ff0000", width=1.0)
    cube2 = Cubes(positions=[[1.0, 0, 0]], color="ff0000", width=1.0)

    assert cube.key == "cube_ff0000_1.0_None"
    assert cube2.key == "cube_ff0000_1.0_None"

    merged_cubes = Cubes.merge([cube, cube2])
    assert merged_cubes.key == "cube_ff0000_1.0_None"
    assert len(merged_cubes.positions) == 2

    assert cube.bounding_box == [[0, 0, 0], [0, 0, 0]]
    assert cube2.bounding_box == [[1.0, 0, 0], [1.0, 0, 0]]
    assert merged_cubes.bounding_box == [[0, 0, 0], [1.0, 0, 0]]
