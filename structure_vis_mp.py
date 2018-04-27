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
from collections import namedtuple
from monty.serialization import loadfn
from matplotlib.cm import get_cmap

from pymatgen.analysis.graphs import StructureGraph
from pymatgen.analysis.local_env import NearNeighbors
from pymatgen.transformations.standard_transformations import AutoOxiStateDecorationTransformation
from pymatgen.vis.structure_vtk import EL_COLORS

from scipy.spatial import Delaunay

class MPVisualizer:
    """
    Class takes a Structure or StructureGraph and outputs a
    list of primitives (spheres, cylinders, etc.) for drawing purposes.
    """

    allowed_bonding_strategies = {subclass.__name__:subclass
                                  for subclass in NearNeighbors.__subclasses__()}

    def __init__(self, structure, bonding_strategy='MinimumOKeeffeNN',
                 bonding_strategy_kwargs=None,
                 color_scheme="VESTA", color_scale=None,
                 radius_strategy="ionic",
                 coordination_polyhedra=False,
                 draw_image_atoms=True,
                 repeat_of_atoms_on_boundaries=True,
                 bonded_atoms_outside_unit_cell=True,
                 scale=None):
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
            coordination_polyhedra: if False, will not calculate coordination polyhedra,
            if True will calculate coordination polyhedra taking the smallest atoms as
            the vertices of the polyhedra, if a tuple of ints is supplied will only draw
            polyhedra with those number of vertices (e.g. supplying (4,6) will only draw
            tetrahedra and octahedra)
        """

        # draw periodic repeats if requested
        if scale:
            structure = structure * scale

        # we assume most uses of this class will give a structure as an input argument,
        # meaning we have to calculate the graph for bonding information, however if
        # the graph is already known and supplied, we will use that
        if not isinstance(structure, StructureGraph):
            if bonding_strategy not in self.allowed_bonding_strategies.keys():
                raise ValueError("Bonding strategy not supported. Please supply a name "
                                 "of a NearNeighbor subclass, choose from: {}"
                                 .format(", ".join(self.allowed_bonding_strategies.keys())))
            else:
                bonding_strategy_kwargs = bonding_strategy_kwargs or {}
                bonding_strategy = self.allowed_bonding_strategies[bonding_strategy](**bonding_strategy_kwargs)
                self.structure_graph = StructureGraph.with_local_env_strategy(structure,
                                                                              bonding_strategy,
                                                                              decorate=False)
            self.lattice = structure.lattice
        else:
            self.structure_graph = structure
            self.lattice = self.structure_graph.structure.lattice

        if coordination_polyhedra:
            # TODO: coming soon
            raise NotImplementedError

        self.color_scheme = color_scheme
        self.color_scale = color_scale
        self.radius_strategy = radius_strategy
        self.coordination_polyhedra = coordination_polyhedra
        self.draw_image_atoms = draw_image_atoms
        self.repeat_of_atoms_on_boundaries = repeat_of_atoms_on_boundaries
        self.bonded_atoms_outside_unit_cell = bonded_atoms_outside_unit_cell

    @property
    def json(self):

        json = {}

        # adds display colors as site properties
        self._generate_colors()

        # used to keep track of atoms outside periodic boundaries for bonding
        self._atom_indexes = {}
        self._site_images_to_draw = {}
        self._bonds = []
        self._polyhedra = []

        json.update(self._generate_atoms())
        json.update(self._generate_bonds())
        json.update(self._generate_polyhedra())
        json.update(self._generate_unit_cell())

        return json

    def _generate_atoms(self):

        # try to work out oxidation states
        trans = AutoOxiStateDecorationTransformation
        try:
            bv_structure = trans.apply_transformation(self.structure_graph.structure)
        except:
            # if we can't assign valences juse use original structure
            bv_structure = self.structure_graph.structure

        self._bonds = []

        # to translate atoms so that geometric center at (0, 0, 0)
        # in global co-ordinate system
        lattice = self.structure_graph.structure.lattice
        geometric_center = lattice.get_cartesian_coords((0.5, 0.5, 0.5))

        # used to easily find positions of atoms that lie on periodic boundaries
        adjacent_images = [
            (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
            (1, 1, 0), (1, -1, 0), (-1, 1, 0), (-1, -1, 0),
            (0, 1, 1), (0, 1, -1), (0, -1, 1), (0, -1, -1),
            (1, 0, 1), (1, 0, -1), (-1, 0, 1), (-1, 0, -1),
            (1, 1, 1), (1, 1, -1), (1, -1, 1), (-1, 1, 1),
            (1, -1, -1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1)
        ]

        self.site_images_to_draw = {i:[] for i in range(len(self.structure_graph))}
        for site_idx, site in enumerate(self.structure_graph.structure):

            images_to_draw = [(0, 0, 0)]
            if self.repeat_of_atoms_on_boundaries:
                possible_positions = [site.frac_coords + adjacent_image
                                      for adjacent_image in adjacent_images]
                # essentially find which atoms lie on periodic boundaries, and
                # draw their repeats
                images_to_draw += [image for image, p in zip(adjacent_images, possible_positions)
                                  if 0 <= p[0] <= 1 and 0 <= p[1] <= 1 and 0 <= p[2] <= 1]

            self.site_images_to_draw[site_idx] += images_to_draw

            # get bond information for site
            # why? to know if we want to draw an image atom,
            # we have to know what bonds are present
            for image in images_to_draw:

                for u, v, d in self.structure_graph.graph.edges(nbunch=site_idx, data=True):

                    to_jimage = tuple(np.add(d['to_jimage'], image))
                    self._bonds.append((site_idx, image, v, to_jimage))

                    if to_jimage not in self.site_images_to_draw[v]:
                        self.site_images_to_draw[v].append(to_jimage)

                    if self.bonded_atoms_outside_unit_cell and \
                                    to_jimage != (0, 0, 0) and image == (0, 0, 0):

                        from_image_complement = tuple(np.multiply(-1, to_jimage))
                        self._bonds.append((site_idx, from_image_complement, v, (0, 0, 0)))

                        if from_image_complement not in self.site_images_to_draw[site_idx]:
                            self.site_images_to_draw[site_idx].append(from_image_complement)

        atoms = []
        self._atoms_cart = {}
        for atom_idx, (site_idx, images) in enumerate(self.site_images_to_draw.items()):

            for image in images:

                self._atom_indexes[(site_idx, image)] = len(atoms)

                # for disordered structures
                occu_start = 0.0
                fragments = []

                site = self.structure_graph.structure[site_idx]
                position_cart = list(np.subtract(
                    lattice.get_cartesian_coords(np.add(site.frac_coords, image)),
                    geometric_center))

                self._atoms_cart[(site_idx, image)] = position_cart

                for comp_idx, (sp, occu) in enumerate(site.species_and_occu.items()):

                    # in disordered structures, we fractionally color-code spheres,
                    # drawing a sphere segment from phi_end to phi_start
                    # (think a sphere pie chart)
                    phi_frac_end = occu_start + occu
                    phi_frac_start = occu_start
                    occu_start = phi_frac_end

                    bv_site = bv_structure[site_idx]

                    # get radius of sphere we want to draw
                    if self.radius_strategy == 'ionic':
                        radius = getattr(bv_site.specie, "ionic_radius",
                                         bv_site.specie.average_ionic_radius)
                    else:
                        radius = site.species.van_der_waals_radius

                    color = site.properties['display_color'][comp_idx]

                    # generate a label (e.g. to use for mouse-over text)
                    if not bv_structure.is_ordered and sp != bv_structure[site_idx].specie:
                        # if we can guess what oxidation states are present,
                        # add them as a label ... we only attempt this for ordered structures
                        name = "{} (detected as likely {})".format(site.specie,
                                                                   bv_structure[site_idx].specie)
                    else:
                        name = "{}".format(sp)

                    if occu != 1.0:
                        name += " ({}% occupancy)".format(occu)

                    fragments.append(
                        {
                            'radius': radius,
                            'color': color,
                            'name': name,
                            'phi_start': phi_frac_start*np.pi*2,
                            'phi_end': phi_frac_end*np.pi*2
                        }
                    )


                atoms.append({
                    'type': 'sphere',
                    'position': position_cart,
                    'bond_color': fragments[0]['color'] if site.is_ordered else [55, 55, 55],
                    'fragments': fragments,
                    'ghost': True if image != (0, 0, 0) else False
                })

        return {
            'atoms': atoms
        }

    def _generate_bonds(self):

        # most of bonding logic is done inside _generate_atoms
        # why? because to decide which atoms we want to draw, we
        # first have to construct the bonds

        bonds = []

        for from_site_idx, from_image, to_site_idx, to_image in self._bonds:

            from_atom_idx = self._atom_indexes[(from_site_idx, from_image)]
            to_atom_idx = self._atom_indexes[(to_site_idx, to_image)]
            bond = {
                'from_atom_index': from_atom_idx,
                'to_atom_index': to_atom_idx
            }

            if bond not in bonds:
                bonds.append(bond)

        return {
            'bonds': bonds
        }

    def _generate_colors(self):

        structure = self.structure_graph.structure

        # TODO: get color scale object from matplotlib

        if self.color_scheme not in ('VESTA', 'Jmol'):

            if not structure.is_ordered:
                raise ValueError('Can only use VESTA or Jmol color schemes '
                                 'for disordered structures, color schemes based '
                                 'on site properties are ill-defined.')

            if self.color_scheme in structure.site_properties:

                props = np.array(structure.site_properties[self.color_scheme])

                if min(props) < 0:
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

                # TODO: reduce calls to cmap here
                colors = [[[int(cmap(x)[0]*255),
                            int(cmap(x)[1]*255),
                            int(cmap(x)[2]*255)]] for x in props]

            else:
                raise ValueError('Unsupported color scheme. Should be "VESTA", "Jmol" or '
                                 'a site property.')
        else:

            colors = []
            for site in structure:
                elements = [sp.as_dict()['element'] for sp, _ in site.species_and_occu.items()]
                colors.append([EL_COLORS[self.color_scheme][element] for element in elements])

        self.structure_graph.structure.add_site_property('display_color', colors)

    def _generate_unit_cell(self):

        frac_vertices = [
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1],
            [1, 1, 0], [0, 1, 1], [1, 0, 1], [1, 1, 1]
        ]

        cart_vertices = [list(self.lattice.get_cartesian_coords(np.subtract(vert, (0.5, 0.5, 0.5))))
                         for vert in frac_vertices]

        tri = Delaunay(cart_vertices)

        unit_cell = {
                'type': 'convex',
                'points': cart_vertices,
                'hull': tri.convex_hull.tolist(),
            }

        return {
            'unit_cell': unit_cell
        }

    def _generate_polyhedra(self):

        if not self.bonded_atoms_outside_unit_cell:
            raise ValueError("All bonds from unit cell must be drawn to be able to reliably "
                             "draw co-ordination polyhedra, please set "
                             "bonded_atoms_outside_unit_cell to True.")

        # this just creates a list of all bonded atoms from each site
        # (this isn't used for the bonding itself, otherwise we'd be
        # double counting bonds, but for polyhedra, in principle each
        # site has its own polyhedra defined)
        potential_polyhedra = {i:[] for i in range(len(self.structure_graph))}

        for from_site_idx, from_image, to_site_idx, to_image in self._bonds:
            if from_image == (0, 0, 0):
                potential_polyhedra[from_site_idx].append((to_site_idx, to_image))
            if to_image == (0, 0, 0):
                potential_polyhedra[to_site_idx].append((from_site_idx, from_image))

        # sort sites for which polyhedra we should prioritize: we don't want
        # polyhedra to intersect each other
        # TODO: placeholder
        sorted_sites_idxs = list(range(len(self.structure_graph)))

        # now we actually store the polyhedra we want!
        # a single polyhedron is simply a list of atom indexes that form
        # its vertices; a convex hull algorithm is necessary to actually
        # construct the faces
        polyhedra = []
        polyhedra_types = set()
        for site_idx in sorted_sites_idxs:
            if site_idx in potential_polyhedra:
                polyhedron_points = potential_polyhedra[site_idx]
                # remove the polyhedron's vertices from the list of potential polyhedra centers
                for (site, image) in polyhedron_points:
                    if image == (0, 0, 0) and site in potential_polyhedra:
                        del potential_polyhedra[site]
                # and look up the actual positions in the array of atoms we're drawing

                polyhedron_points_cart = [self._atoms_cart[(site, image)]
                                          for (site, image) in polyhedron_points]

                polyhedron_points_idx = [self._atom_indexes[(site, image)]
                                         for (site, image) in polyhedron_points]

                # calculate the hull
                tri = Delaunay(polyhedron_points_cart)

                # a pretty name, helps with filtering too
                site = self.structure_graph.structure[site_idx]
                species = ", ".join(map(str, list(site.species_and_occu.keys())))
                polyhedron_type = '{}-centered polyhedra'.format(species)
                polyhedra_types.add(polyhedron_type)

                polyhedra.append({
                    'type': 'convex',
                    'points_idx': polyhedron_points_idx,
                    'points': polyhedron_points_cart,
                    'hull': tri.convex_hull,
                    'name': polyhedron_type,
                    'center': site_idx
                })

        return {
            'polyhedra': {
                'polyhedra_list': polyhedra,
                'polyhedra_types': list(polyhedra_types)
            }
        }