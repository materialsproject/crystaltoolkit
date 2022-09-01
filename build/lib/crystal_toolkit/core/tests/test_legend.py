from crystal_toolkit.core.legend import Legend

from pymatgen.core.structure import Structure
from pymatgen.core.lattice import Lattice


class TestLegend:
    def setup_method(self, method):

        self.struct = Structure(
            Lattice.cubic(5),
            ["H", "O", "In"],
            [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0, 0]],
            site_properties={
                "example_site_prop": [5, 0, -3],
                "example_categorical_site_prop": ["4a", "4a", "8b"],
            },
        )

        self.site0 = self.struct[0]
        self.sp0 = list(self.site0.species.keys())[0]

        self.site1 = self.struct[1]
        self.sp1 = list(self.site1.species.keys())[0]

        self.site2 = self.struct[2]
        self.sp2 = list(self.site2.species.keys())[0]

        self.struct_disordered = Structure(
            Lattice.cubic(5),
            ["H", "O", {"In": 0.5, "Al": 0.5}],
            [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0, 0]],
            site_properties={"example_site_prop": [5, 0, -3]},
        )

        self.site_d = self.struct_disordered[2]
        self.site_d_sp0 = list(self.site_d.species.keys())[0]
        self.site_d_sp1 = list(self.site_d.species.keys())[1]

        self.struct_manual = Structure(
            Lattice.cubic(5),
            ["H", "O2-", "In"],
            [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0, 0]],
            site_properties={"display_color": [[255, 0, 0], "blue", "#00ff00"]},
        )

    def test_get_color(self):

        # test default

        legend = Legend(self.struct, color_scheme="VESTA")

        color = legend.get_color(self.sp0)
        assert color == "#ffcccc"

        # element-based color schemes shouldn't change if you supply a site
        color = legend.get_color(self.sp0, site=self.site0)
        assert color == "#ffcccc"

        color = legend.get_color(self.sp2)
        assert color == "#a67573"

        assert legend.get_legend()["colors"] == {
            "#a67573": "In",
            "#fe0300": "O",
            "#ffcccc": "H",
        }

        # test alternate

        legend = Legend(self.struct, color_scheme="Jmol")

        color = legend.get_color(self.sp0)
        assert color == "#ffffff"

        assert legend.get_legend()["colors"] == {
            "#a67573": "In",
            "#ff0d0d": "O",
            "#ffffff": "H",
        }

        # test coloring by site properties

        legend = Legend(self.struct, color_scheme="example_site_prop")

        color = legend.get_color(self.sp0, site=self.site0)
        assert color == "#b30326"

        color = legend.get_color(self.sp1, site=self.site1)
        assert color == "#dddcdb"

        color = legend.get_color(self.sp2, site=self.site2)
        assert color == "#7b9ef8"

        assert legend.get_legend()["colors"] == {
            "#7b9ef8": "-3.00",
            "#b30326": "5.00",
            "#dddcdb": "0.00",
        }

        # test accessible

        legend = Legend(self.struct, color_scheme="accessible")

        color = legend.get_color(self.sp0, site=self.site0)
        assert color == "#ffffff"

        color = legend.get_color(self.sp1, site=self.site1)
        assert color == "#d55e00"

        color = legend.get_color(self.sp2, site=self.site2)
        assert color == "#cc79a7"

        assert legend.get_legend()["colors"] == {
            "#cc79a7": "In",
            "#d55e00": "O",
            "#ffffff": "H",
        }

        # test disordered

        legend = Legend(self.struct_disordered)

        color = legend.get_color(self.site_d_sp0, site=self.site_d)
        assert color == "#a67573"

        color = legend.get_color(self.site_d_sp1, site=self.site_d)
        assert color == "#bfa6a6"

        assert legend.get_legend()["colors"] == {
            "#a67573": "In",
            "#bfa6a6": "Al",
            "#ff0d0d": "O",
            "#ffffff": "H",
        }

        # test categorical

        legend = Legend(self.struct, color_scheme="example_categorical_site_prop")

        assert legend.get_legend()["colors"] == {"#377eb8": "8b", "#e41a1c": "4a"}

        # test pre-defined

        legend = Legend(self.struct_manual)

        assert legend.get_legend()["colors"] == {
            "#0000ff": "O2-",
            "#00ff00": "In",
            "#ff0000": "H",
        }

    def test_get_radius(self):

        legend = Legend(self.struct, radius_scheme="uniform")

        assert legend.get_radius(sp=self.sp0) == 0.5

        legend = Legend(self.struct, radius_scheme="covalent")

        assert legend.get_radius(sp=self.sp1) == 0.66

        legend = Legend(self.struct, radius_scheme="specified_or_average_ionic")

        assert legend.get_radius(sp=self.sp2) == 0.94

    def test_msonable(self):

        legend = Legend(self.struct)
        legend_dict = legend.as_dict()
        legend_from_dict = Legend.from_dict(legend_dict)

        assert legend.get_legend() == legend_from_dict.get_legend()
