# coding: utf-8

from __future__ import division, unicode_literals

"""
This module is intended to export a Structure to a scene graph,
such as that used by Three.js, for visualization purposes.

It is intended to be added to pymatgen at a later date.
"""

__author__ = "Matthew Horton"
__email__ = "mkhorton@lbl.gov"
__date__ = "Feb 28, 2018"

import os
import numpy as np

from enum import Enum
from collections import namedtuple, defaultdict, OrderedDict
from monty.serialization import loadfn
from matplotlib.cm import get_cmap
import warnings
import itertools

from pymatgen.analysis.graphs import StructureGraph
from pymatgen.analysis.local_env import NearNeighbors
from pymatgen.transformations.standard_transformations import AutoOxiStateDecorationTransformation
from pymatgen.core.periodic_table import Specie
from pymatgen.analysis.molecule_structure_comparator import CovalentRadius
from pymatgen.vis.structure_vtk import EL_COLORS
from pymatgen.core.structure import Structure

from scipy.spatial import Delaunay

class PymatgenVisualizationIntermediateFormat:
    """
    Class takes a Structure or StructureGraph and outputs a
    list of primitives (spheres, cylinders, etc.) for drawing purposes.
    """

    available_bonding_strategies = {subclass.__name__:subclass
                                    for subclass in NearNeighbors.__subclasses__()}

    available_radius_strategies = ('atomic', 'bvanalyzer_ionic', 'average_ionic',
                                   'covalent', 'van_der_waals', 'atomic_calculated')

    def __init__(self, structure, bonding_strategy='MinimumDistanceNN',
                 bonding_strategy_kwargs=None,
                 color_scheme="VESTA", color_scale=None,
                 radius_strategy="average_ionic",
                 draw_image_atoms=True,
                 repeat_of_atoms_on_boundaries=True,
                 bonded_sites_outside_display_area=True,
                 symmetrize=True,  # TODO
                 display_repeats=((0, 2), (0, 2), (0, 2))):
        """
        This class is used to generate a generic JSON of geometric primitives
        that can be parsed by a 3D rendering tool such as Three.js or Blender.

        The intent is that any crystallographic knowledge is handled by pymatgen
        (e.g. finding Cartesian co-ordinates of atoms, suggesting colors and radii
        for the atoms, detecting whether andw here bonds should be present, detecting
        oxidation environments, calculating coordination polyhedra, etc.) Therefore,
        the 3D rendering code does not need to have any knowledge of crystallography,
        but just has to parse the JSON and draw the corresponding geometric primitives.

        The resulting JSON should be self-explanatory and constructed such that
        an appropriate scene graph can be made without difficulty. The 'type'
        keys can be either 'sphere', 'cylinder', 'geometry' or 'text', the 'position'
        key is always a vector with respect to global Cartesian co-ordinates.

        Bonds and co-ordination polyhedra reference the index of the appropriate
        atom, rather than duplicating position vectors.

        Args:
            structure: an instance of Structure or StructureGraph (the latter
            for when bonding information is already known)
            bonding_strategy: a name of a NearNeighbor subclass to calculate
            bonding, will only be used if bonding not already defined (at time
            of writing, options are 'JMolNN', 'MinimumDistanceNN', 'MinimumOKeeffeeNN',
            'MinimumVIRENN', 'VoronoiNN', but see pymatgen.analysis.local_env for
            latest options)
            bonding_strategy_kwargs: kwargs to be passed to the NearNeighbor
            subclass
            color_scheme: can be "VESTA", "Jmol" or a name of a site property
            to color-code by that site property
            color_scale: only relevant if color-coding by site property, by default
            will use viridis, but all matplotlib color scales are supported (see
            matplotlib documentation)
            radius_strategy: options are "ionic" or "van_der_Waals":
            by default, will use ionic radii if oxidation states are supplied or if BVAnalyzer
            can supply oxidation states, otherwise will use average ionic radius
        """
        # TODO: update docstring

        # ensure fractional co-ordinates are normalized to be in [0,1)
        # (this is actually not guaranteed by Structure)
        if isinstance(structure, Structure):
            structure = structure.as_dict(verbosity=0)
            for site in structure['sites']:
                site['abc'] = np.mod(site['abc'], 1)
            structure = Structure.from_dict(structure)

        # we assume most uses of this class will give a structure as an input argument,
        # meaning we have to calculate the graph for bonding information, however if
        # the graph is already known and supplied, we will use that
        if not isinstance(structure, StructureGraph):
            if bonding_strategy not in self.available_bonding_strategies.keys():
                raise ValueError("Bonding strategy not supported. Please supply a name "
                                 "of a NearNeighbor subclass, choose from: {}"
                                 .format(", ".join(self.available_bonding_strategies.keys())))
            else:
                bonding_strategy_kwargs = bonding_strategy_kwargs or {}
                bonding_strategy = self.available_bonding_strategies[bonding_strategy](**bonding_strategy_kwargs)
                self.structure_graph = StructureGraph.with_local_env_strategy(structure,
                                                                              bonding_strategy)
                cns = [self.structure_graph.get_coordination_of_site(i)
                       for i in range(len(structure))]
                self.structure_graph.structure.add_site_property('coordination_no', cns)
        else:
            self.structure_graph = structure

        self.structure = self.structure_graph.structure
        self.lattice = self.structure_graph.structure.lattice

        self.color_scheme = color_scheme  # TODO: add coord as option
        self.color_scale = color_scale
        self.radius_strategy = radius_strategy
        self.draw_image_atoms = draw_image_atoms
        self.bonded_sites_outside_display_area = bonded_sites_outside_display_area
        self.display_range = display_repeats

        # categorize site properties so we know which can be used for color schemes etc.
        self.site_prop_names = self._analyze_site_props()

        self.color_legend = self._generate_colors()  # adds 'display_color' site prop
        self._generate_radii()  # adds 'display_radius' site prop

    @property
    def json(self):

        atoms = self._generate_atoms()
        bonds = self._generate_bonds(atoms)
        polyhedra_json = self._generate_polyhedra(atoms, bonds)
        unit_cell_json = self._generate_unit_cell()

        json = {
            'atoms': list(atoms.values()),
            'bonds': list(bonds.values()),
            'polyhedra': polyhedra_json,
            'unit_cell': unit_cell_json,
            'color_legend': self.color_legend,
            'site_props': self.site_prop_names
        }

        return json

    @property
    def graph_json(self):

        nodes = []
        edges = []

        for node in self.structure_graph.graph.nodes():

            r, g, b = self.structure_graph.structure[node].properties['display_color'][0]
            color = "#{:02x}{:02x}{:02x}".format(r, g, b)

            nodes.append({
                'id': node,
                'label': node,
                'color': color
            })

        for u, v, d in self.structure_graph.graph.edges(data=True):

            edge = {'from': u, 'to': v, 'arrows': ''}

            to_jimage = d['to_jimage']

            # TODO: check these edge weights
            dist = self.structure.get_distance(u, v, to_jimage)
            edge['length'] = 50*dist
            if to_jimage != (0, 0, 0):
                edge['arrows'] = 'to'
                edge['label'] = str(to_jimage)

            edges.append(edge)

        return {'nodes': nodes, 'edges': edges}

    def _analyze_site_props(self):

        # store list of site props that are vectors, so these can be displayed as arrows
        # (implicitly assumes all site props for a given key are same type)
        site_prop_names = defaultdict(list)
        for name, props in self.structure_graph.structure.site_properties.items():
            if isinstance(props[0], float) or isinstance(props[0], int):
                site_prop_names['scalar'].append(name)
            elif isinstance(props[0], list) and len(props[0]) == 3:
                if isinstance(props[0][0], list) and len(props[0][0]) == 3:
                    site_prop_names['matrix'].append(name)
                else:
                    site_prop_names['vector'].append(name)
            elif isinstance(props[0], str):
                site_prop_names['categorical'].append(name)

        return dict(site_prop_names)

    def _generate_atoms(self):

        # to translate atoms so that geometric center at (0, 0, 0)
        # in global co-ordinate system
        x_center = 0.5 * (max(self.display_range[0]) - min(self.display_range[0]))
        y_center = 0.5 * (max(self.display_range[1]) - min(self.display_range[1]))
        z_center = 0.5 * (max(self.display_range[2]) - min(self.display_range[2]))
        self.geometric_center = self.lattice.get_cartesian_coords((x_center, y_center, z_center))

        ranges = [range(int(np.sign(r[0])*np.ceil(np.abs(r[0]))),
                        1+int(np.sign(r[1])*np.ceil(np.abs(r[1])))) for r in self.display_range]
        possible_images = list(itertools.product(*ranges))

        site_images_to_draw = defaultdict(list)

        lower_corner = np.array([min(r) for r in self.display_range])
        upper_corner = np.array([max(r) for r in self.display_range])
        for idx, site in enumerate(self.structure):
            for image in possible_images:
                frac_coords = np.add(image, site.frac_coords)
                if np.all(np.less_equal(lower_corner, frac_coords)) \
                        and np.all(np.less_equal(frac_coords, upper_corner)):
                    site_images_to_draw[idx].append(image)

        images_to_add = defaultdict(list)
        if self.bonded_sites_outside_display_area:
            for site_idx, images in site_images_to_draw.items():
                for u, v, d in self.structure_graph.graph.edges(nbunch=site_idx, data=True):

                    for image in images:
                        # check bonds going in both directions, i.e. from u or from v
                        # to_image is defined from u going to v
                        to_image = tuple(np.add(d['to_jimage'], image).astype(int))

                        # make sure we're drawing the site the bond is going to
                        if to_image not in site_images_to_draw[v]:
                            images_to_add[v].append(to_image)

                        # and also the site the bond is coming from
                        from_image_complement = tuple(np.multiply(-1, to_image))
                        if from_image_complement not in site_images_to_draw[u]:
                            images_to_add[u].append(from_image_complement)

        atoms = OrderedDict()
        for site_idx, images in site_images_to_draw.items():

            site = self.structure[site_idx]

            # for disordered structures
            occu_start = 0.0
            fragments = []

            for comp_idx, (sp, occu) in enumerate(site.species_and_occu.items()):

                # in disordered structures, we fractionally color-code spheres,
                # drawing a sphere segment from phi_end to phi_start
                # (think a sphere pie chart)
                phi_frac_end = occu_start + occu
                phi_frac_start = occu_start
                occu_start = phi_frac_end

                radius = site.properties['display_radius'][comp_idx]
                color = site.properties['display_color'][comp_idx]

                name = "{}".format(sp)
                if occu != 1.0:
                    name += " ({}% occupancy)".format(occu)

                fragments.append(
                    {
                        'radius': radius,
                        'color': color,
                        'name': name,
                        'phi_start': phi_frac_start * np.pi * 2,
                        'phi_end': phi_frac_end * np.pi * 2
                    }
                )

            bond_color = fragments[0]['color'] if site.is_ordered else [55, 55, 55]

            # TODO: do some appropriate scaling here
            if 'vector' in self.site_prop_names:
                vectors = {name:site.properties[name] for name in self.site_prop_names['vector']}
            else:
                vectors = None

            if 'matrix' in self.site_prop_names:
                matrices = {name:site.properties[name] for name in self.site_prop_names['matrix']}
            else:
                matrices = None

            for image in images:

                position_cart = list(np.subtract(
                    self.lattice.get_cartesian_coords(np.add(site.frac_coords, image)),
                    self.geometric_center))

                atoms[(site_idx, image)] = {
                    'type': 'sphere',
                    'idx': len(atoms),
                    'position': position_cart,
                    'bond_color': bond_color,
                    'fragments': fragments,
                    'vectors': vectors,
                    'matrices': matrices
                }

        return atoms

    def _generate_bonds(self, atoms):

        bonds_set = set()
        atoms = list(atoms.keys())

        for site_idx, image in atoms:
            for u, v, d in self.structure_graph.graph.edges(nbunch=site_idx, data=True):

                to_image = tuple(np.add(d['to_jimage'], image).astype(int))

                bond = frozenset({(u, image), (v, to_image)})
                bonds_set.add(bond)

        bonds = OrderedDict()
        for bond in bonds_set:

            bond = tuple(bond)

            try:
                from_atom_idx = atoms.index(bond[0])
                to_atom_idx = atoms.index(bond[1])
            except ValueError:
                pass  # one of the atoms in the bond isn't being drawn
            else:
                bonds[bond] = {
                    'from_atom_index': from_atom_idx,
                    'to_atom_index': to_atom_idx
                }

        return bonds

    def _generate_radii(self):

        structure = self.structure_graph.structure

        # don't calculate radius if one is explicitly supplied
        if 'display_radius' in structure.site_properties:
            return

        if self.radius_strategy is 'bvanalyzer_ionic':

            trans = AutoOxiStateDecorationTransformation()
            try:
                structure = trans.apply_transformation(self.structure_graph.structure)
            except:
                # if we can't assign valences use average ionic
                self.radius_strategy = 'average_ionic'

        radii = []
        for site_idx, site in enumerate(structure):

            site_radii = []

            for comp_idx, (sp, occu) in enumerate(site.species_and_occu.items()):

                radius = None

                if self.radius_strategy not in self.available_radius_strategies:
                    raise ValueError("Unknown radius strategy {}, choose from: {}"
                                     .format(self.radius_strategy, self.available_radius_strategies))

                if self.radius_strategy is 'atomic':
                    radius = sp.atomic_radius
                elif self.radius_strategy is 'bvanalyzer_ionic' and isinstance(sp, Specie):
                    radius = sp.ionic_radius
                elif self.radius_strategy is 'average_ionic':
                    radius = sp.average_ionic_radius
                elif self.radius_strategy is 'covalent':
                    el = str(getattr(sp, 'element', sp))
                    radius = CovalentRadius.radius[el]
                elif self.radius_strategy is 'van_der_waals':
                    radius = sp.van_der_waals_radius
                elif self.radius_strategy is 'atomic_calculated':
                    radius = sp.atomic_radius_calculated

                if not radius:
                    warnings.warn('Radius unknown for {} and strategy {}, '
                                  'setting to 1.0.'.format(sp, self.radius_strategy))
                    radius = 1.0

                site_radii.append(radius)

            radii.append(site_radii)

        self.structure_graph.structure.add_site_property('display_radius', radii)


    def _generate_colors(self):

        structure = self.structure_graph.structure
        legend = {}

        # don't calculate color if one is explicitly supplied
        if 'display_color' in structure.site_properties:
            return legend  # don't know what the color legend (meaning) is, so return empty legend

        if self.color_scheme not in ('VESTA', 'Jmol'):

            if not structure.is_ordered:
                raise ValueError('Can only use VESTA or Jmol color schemes '
                                 'for disordered structures, color schemes based '
                                 'on site properties are ill-defined.')

            if self.color_scheme in self.site_prop_names.get('scalar', []):

                props = np.array(structure.site_properties[self.color_scheme])

                if min(props) < 0 and max(props) > 0:
                    # by default, use blue-grey-red color scheme,
                    # so that zero is ~ grey, and positive/negative
                    # are red/blue
                    color_scale = self.color_scale or 'coolwarm'
                    # try to keep color scheme symmetric around 0
                    color_max = max([abs(min(props)), max(props)])
                    color_min = -color_max
                else:
                    # but if all values are positive, use a
                    # perceptually-uniform color scale by default
                    # like viridis
                    color_scale = self.color_scale or 'viridis'
                    color_max = max(props)
                    color_min = min(props)

                cmap = get_cmap(color_scale)
                # normalize in [0, 1] range, as expected by cmap
                props = (props - min(props)) / (max(props) - min(props))

                def _get_color(x):
                    return [int(c*255) for c in cmap(x)[0:3]]

                colors = [[_get_color(x)] for x in props]

                # construct legend
                c = "#{:02x}{:02x}{:02x}".format(*_get_color(color_min))
                legend[c] = "{}".format(color_min)
                if color_max != color_min:

                    c = "#{:02x}{:02x}{:02x}".format(*_get_color(color_max))
                    legend[c] = "{}".format(color_max)

                    color_mid = (color_max-color_min)/2
                    if color_max%1 == 0 and color_min%1 == 0  and color_max-color_min > 1:
                        color_mid = int(color_mid)

                    c = "#{:02x}{:02x}{:02x}".format(*_get_color(color_mid))
                    legend[c] = "{}".format(color_mid)

            elif self.color_scheme in self.site_prop_names.get('categorical', []):
                raise NotImplementedError
                # iter() a palettable  palettable.colorbrewer.qualitative cmap.colors, check len, Set1_9 ?

            else:
                raise ValueError('Unsupported color scheme. Should be "VESTA", "Jmol" or '
                                 'a scalar or categorical site property.')
        else:

            colors = []
            for site in structure:
                elements = [sp.as_dict()['element'] for sp, _ in site.species_and_occu.items()]
                colors.append([EL_COLORS[self.color_scheme][element] for element in elements])

                # construct legend
                for element in elements:
                    color = "#{:02x}{:02x}{:02x}".format(*EL_COLORS[self.color_scheme][element])
                    legend[color] = element

        self.structure_graph.structure.add_site_property('display_color', colors)

        return legend

    def _generate_unit_cell(self):

        o = -self.geometric_center
        a, b, c = self.lattice.matrix[0], self.lattice.matrix[1], self.lattice.matrix[2]

        line_pairs = [
            o, o+a, o, o+b, o, o+c,
            o+a, o+a+b, o+a, o+a+c,
            o+b, o+b+a, o+b, o+b+c,
            o+c, o+c+a, o+c, o+c+b,
            o+a+b, o+a+b+c, o+a+c, o+a+b+c, o+b+c, o+a+b+c
        ]

        line_pairs = [line.tolist() for line in line_pairs]

        unit_cell = {
            'type': 'lines',
            'lines': line_pairs
        }

        return unit_cell

    def _generate_polyhedra(self, atoms, bonds):

        # TODO: this function is a bit confusing
        # mostly due to number of similarly-named data structures ... rethink?

        potential_polyhedra_by_site = {}
        for idx, site in enumerate(self.structure):
            connected_sites = self.structure_graph.get_connected_sites(idx)
            neighbors_sp = [cn[0].species_string for cn in connected_sites]
            neighbors_idx = [cn.index for cn in connected_sites]
            # could enforce len(set(neighbors_sp)) == 1 here if we want to only
            # draw polyhedra when neighboring atoms are all the same
            if len(neighbors_sp) > 2:
                # store num expected vertices, we don't want to draw incomplete polyhedra
                potential_polyhedra_by_site[idx] = len(neighbors_sp)

        polyhedra = defaultdict(list)
        for ((from_site_idx, from_image), (to_site_idx, to_image)), d in bonds.items():
            if from_site_idx in potential_polyhedra_by_site:
                polyhedra[(from_site_idx, from_image)].append((to_site_idx, to_image))
            if to_site_idx in potential_polyhedra_by_site:
                polyhedra[(to_site_idx, to_image)].append((from_site_idx, from_image))

        # discard polyhedra with incorrect coordination (e.g. half the polyhedra's atoms are
        # not in the draw range so would be cut off)
        polyhedra = {k:v for k, v in polyhedra.items()
                     if len(v) == potential_polyhedra_by_site[k[0]]}

        polyhedra_by_species = defaultdict(list)
        for k in polyhedra.keys():
            polyhedra_by_species[self.structure[k[0]].species_string].append(k)

        polyhedra_json_by_species = {}
        polyhedra_by_species_vertices = {}
        polyhedra_by_species_centres = {}
        for sp, polyhedra_centres in polyhedra_by_species.items():
            polyhedra_json = []
            polyhedra_vertices = []
            for polyhedron_centre in polyhedra_centres:

                # book-keeping to prevent intersecting polyhedra
                polyhedron_vertices = polyhedra[polyhedron_centre]
                polyhedra_vertices += polyhedron_vertices

                polyhedron_points_cart = [atoms[vert]['position']
                                          for vert in polyhedron_vertices]
                polyhedron_points_idx = [atoms[vert]['idx']
                                         for vert in polyhedron_vertices]
                polyhedron_center_idx = atoms[polyhedron_centre]['idx']

                # Delaunay can fail in some edge cases
                try:

                    hull = Delaunay(polyhedron_points_cart).convex_hull.tolist()

                    # TODO: storing duplicate info here ... ?
                    polyhedra_json.append({
                        'type': 'convex',
                        'points_idx': polyhedron_points_idx,
                        'points': polyhedron_points_cart,
                        'hull': hull,
                        'center': polyhedron_center_idx
                    })

                except Exception as e:
                    print(e)

            polyhedron_centres = set(polyhedra_centres)
            polyhedron_vertices = set(polyhedra_vertices)

            if (not polyhedron_vertices.intersection(polyhedra_centres)) \
                    and len(polyhedra_json) > 0 :
                name = "{}-centered".format(sp)
                polyhedra_json_by_species[name] = polyhedra_json
                polyhedra_by_species_centres[name] = polyhedron_centres
                polyhedra_by_species_vertices[name] = polyhedron_vertices

        if polyhedra_json_by_species:

            # get compatible sets of polyhedra
            compatible_subsets = {(k, ): len(v) for k, v in polyhedra_json_by_species.items()}
            for r in range(2, len(polyhedra_json_by_species)+1):
                for subset in itertools.combinations(polyhedra_json_by_species.keys(), r):
                    compatible = True
                    all_centres = set.union(*[polyhedra_by_species_vertices[sp] for sp in subset])
                    all_verts = set.union(*[polyhedra_by_species_centres[sp] for sp in subset])
                    if not all_verts.intersection(all_centres):
                        compatible_subsets[tuple(subset)] = len(all_centres)

            # sort by longest subset, secondary sort by radius
            compatible_subsets = sorted(compatible_subsets.items(), key=lambda s: -s[1])
            default_polyhedra = list(compatible_subsets[0][0])

        else:

            default_polyhedra = []

        return {
            'polyhedra_by_type': polyhedra_json_by_species,
            'polyhedra_types': list(polyhedra_json_by_species.keys()),
            'default_polyhedra_types': default_polyhedra
        }