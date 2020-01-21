from pymatgen import Structure, Lattice
from crystal_toolkit.core.scene import Spheres, Surface, Cylinders
from crystal_toolkit.helpers.pythreejs_renderer import (
    _convert_object_to_pythreejs,
    _traverse_scene_object,
)
import unittest


class TestPythreejsRenderer(unittest.TestCase):
    def setUp(self):
        self.struct = Structure(
            Lattice.cubic(5),
            ["H", "O", "In"],
            [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0, 0]],
            site_properties={
                "example_site_prop": [5, 0, -3],
                "example_categorical_site_prop": ["4a", "4a", "8b"],
            },
        )

    def test_convert_object_to_pythreejs(self):
        # take different crystal toolkit objects and convert them into pythreejs objects
        sphere = Spheres(positions=[[0, 0, 0]], color="#00ab24", radius=1.0)
        assert (
            "SphereBufferGeometry"
            in _convert_object_to_pythreejs(scene_obj=sphere)[0].__repr__()
        )

        cylinder = Cylinders(
            positionPairs=[[[0, 0, 0], [0, 1, 1]]], color="#00ab24", radius=1.0
        )
        assert (
            "CylinderBufferGeometry"
            in _convert_object_to_pythreejs(scene_obj=cylinder)[0].__repr__()
        )

        surface = Surface([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        _convert_object_to_pythreejs(scene_obj=surface)[0].__repr__()
        assert (
            "BufferGeometry"
            in _convert_object_to_pythreejs(scene_obj=surface)[0].__repr__()
        )

    def test_traverse_scene_object(self):
        kwargs = {}
        if isinstance(self.struct, Structure) or isinstance(
            self.struct, StructureGraph
        ):
            kwargs["explicitly_calculate_polyhedra_hull"] = True
        ctk_scene = self.struct.get_scene(**kwargs)
        py3_obj = _traverse_scene_object(ctk_scene)
        assert "atoms" in py3_obj.__repr__()
        assert "bonds" in py3_obj.__repr__()


if __name__ == "__main__":
    unittest.main()
