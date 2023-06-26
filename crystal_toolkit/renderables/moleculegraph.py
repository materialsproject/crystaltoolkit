from __future__ import annotations

from collections import defaultdict

from pymatgen.analysis.graphs import MoleculeGraph
from pymatgen.analysis.local_env import OpenBabelNN

from crystal_toolkit.core.legend import Legend
from crystal_toolkit.core.scene import Scene

# TODO: fix Sam's bug (reorder)


def get_molecule_graph_scene(
    self,
    origin=None,
    explicitly_calculate_polyhedra_hull=False,
    legend=None,
    draw_polyhedra=False,
    show_atom_idx=True,
    show_atom_coord=True,
    show_bond_order=True,
    show_bond_length=False,
    visualize_bond_orders=False,
) -> Scene:
    """Create a Molecule Graph scene.

    Args:
        show_atom_idx: Defaults to True, shows the site index of each atom in the molecule
        show_atom_coord: Defaults to True, shows the 3D coordinates of each atom in the molecule
        show_bond_order: Defaults to True, shows the calculated bond order in the chosen local
            environment strategy
        show_bond_length: Defaults to False, shows the calculated length between two connected atoms
        visualize_bpnd_orders: Defaults False, will show the 'integral' number of bonds calculated
            from the OpenBabelNN strategy in the Molecule Graph

    Returns:
        A Molecule Graph scene.
    """
    if visualize_bond_orders:
        vis_mol_graph = MoleculeGraph.with_local_env_strategy(
            self.molecule, OpenBabelNN()
        )
    else:
        vis_mol_graph = self
    legend = legend or Legend(self.molecule)

    primitives: dict[str, list] = defaultdict(list)

    for idx, site in enumerate(self.molecule):
        connected_sites = vis_mol_graph.get_connected_sites(idx)

        site_scene = site.get_scene(
            site_idx=idx,
            connected_sites=connected_sites,
            origin=origin,
            explicitly_calculate_polyhedra_hull=explicitly_calculate_polyhedra_hull,
            legend=legend,
            show_atom_idx=show_atom_idx,
            show_atom_coord=show_atom_coord,
            show_bond_order=show_bond_order,
            show_bond_length=show_bond_length,
            visualize_bond_orders=visualize_bond_orders,
            draw_polyhedra=draw_polyhedra,
        )
        for scene in site_scene.contents:
            primitives[scene.name] += scene.contents

    return Scene(
        name=self.molecule.composition.reduced_formula,
        contents=[Scene(name=key, contents=val) for key, val in primitives.items()],
        origin=origin if origin else (0, 0, 0),
    )


MoleculeGraph.get_scene = get_molecule_graph_scene
