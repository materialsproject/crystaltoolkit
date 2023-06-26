"""Export wrapper for asymptote (ASY). For creating publication quality plots. Since ASY does not
have the nested tree structure of threejs, we just have to traverse the tree and draw each material
as we see them.

TODO The code should also append a set of special points at the end in case the user wants to add
more "hand drawn" features to the plot.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import chain
from typing import IO, TYPE_CHECKING, Any

from jinja2 import Environment
from pymatgen.analysis.graphs import StructureGraph
from pymatgen.core import Structure

from crystal_toolkit.defaults import _DEFAULTS

if TYPE_CHECKING:
    from crystal_toolkit.core.scene import Scene

logger = logging.getLogger(__name__)

HEADER = """
import settings;
import solids;
size(300);
outformat="png";
defaultshininess = 0.8;
currentlight = light(0,0,400);

// Camera information
currentprojection=orthographic (
camera=(8,5,4),
up=(0,0,1),
target={{target}},
zoom=0.5
);

// Basic function for drawing spheres
void drawSpheres(triple[] C, real R, pen p=currentpen){
  for(int i=0;i<C.length;++i){
    draw(sphere(C[i],R).surface(
                        new pen(int i, real j){return p;}
                        )
    );
  }
}

// Draw a sphere without light
void drawSpheres_nolight(triple[] C, real R, pen p=currentpen){
  material nlpen = material(diffusepen=opacity(1.0), emissivepen=p, shininess=0);
  for(int i=0;i<C.length;++i){
    revolution s_rev = sphere(C[i],R);
    surface s_surf = surface(s_rev);
    draw(s_surf, nlpen);
    draw(s_rev.silhouette(100), black+linewidth(3));
  }
}

// Draw a cylinder
void Draw(guide3 g,pen p=currentpen, real cylR=0.2){
  draw(
    cylinder(
      point(g,0),cylR,arclength(g),point(g,1)-point(g,0)
    ).surface(
               new pen(int i, real j){
                 return p;
               }
             )
  );
}

// Draw a cylinder without light
void Draw_nolight(guide3 g,pen p=currentpen, real cylR=0.2){
  material nlpen = material(diffusepen=opacity(1.0), emissivepen=p, shininess=0);
  revolution s_rev = cylinder(point(g,0),cylR,arclength(g),point(g,1)-point(g,0));
  surface s_surf = surface(s_rev);
  draw(s_surf, nlpen);
  draw(s_rev.silhouette(100), black+linewidth(3));
}
"""

TEMP_SPHERE = """
{% for val in positions %}
triple sphere{{loop.index}}={{val}};
{% endfor %}

triple[] spheres = {
{%- for val in positions -%}
sphere{{loop.index}}
{%- if not loop.last %},{% endif %}
{%- endfor -%}
};
drawSpheres(spheres, {{radius}}, rgb('{{color}}')+opacity({{opac}}));
"""

TEMP_SPHERE_NOLIGHT = """
{% for val in positions %}
triple sphere{{loop.index}}={{val}};
{% endfor %}

triple[] spheres = {
{%- for val in positions -%}
sphere{{loop.index}}
{%- if not loop.last %},{% endif %}
{%- endfor -%}
};
drawSpheres_nolight(spheres, {{radius}}, rgb('{{color}}')+opacity({{opac}}));
"""

TEMP_LINE = """
pen connectPen=rgb('{{color}}') + linewidth({{linewidth}});
{% for ipos, fpos in posPairs %}
triple IPOS = {{ipos}};
triple FPOS = {{fpos}};
draw(IPOS--FPOS, connectPen);
{% endfor %}
"""

TEMP_CYLINDER = """
pen connectPen=rgb('{{color}}') + opacity({{opac}});
{% for ipos, fpos in posPairs %}
triple IPOS = {{ipos}};
triple FPOS = {{fpos}};
Draw(IPOS--FPOS, connectPen, {{radius}});
{% endfor %}
"""

TEMP_CYLINDER_NOLIGHT = """
pen connectPen=rgb('{{color}}')+opacity({{opac}});
{% for ipos, fpos in posPairs %}
triple IPOS = {{ipos}};
triple FPOS = {{fpos}};
Draw_nolight(IPOS--FPOS, connectPen, {{radius}});
{% endfor %}
"""

TEMP_SURF = """
real[][] A = {
{% for ipos in positions -%}
    {{ipos}},
{% endfor %}
};
A = transpose(A);

material m = rgb('{{color}}') + opacity({{opac}});
triple a,b,c;
for(int i=0; i < A[0].length/3; ++i) {
  a=(A[0][i*3],A[1][i*3],A[2][i*3]);
  b=(A[0][i*3+1],A[1][i*3+1],A[2][i*3+1]);
  c=(A[0][i*3+2],A[1][i*3+2],A[2][i*3+2]);
  draw(surface(a--b--c--cycle),surfacepen = m);        // draw i-th triangle
}
path3 no_show = path3(scale(0) * box((-1,-1),(1,1)));
draw(surface(no_show), surfacepen=m);        // draw i-th triangle
"""

TEMP_SURF_NOLIGHT = """
real[][] A = {
{% for ipos in positions -%}
    {{ipos}},
{% endfor %}
};
A = transpose(A);

material m = material(diffusepen=opacity({{opac}}), emissivepen=rgb("{{color}}"), shininess=0);
triple a,b,c;
for(int i=0; i < A[0].length/3; ++i) {
  a=(A[0][i*3],A[1][i*3],A[2][i*3]);
  b=(A[0][i*3+1],A[1][i*3+1],A[2][i*3+1]);
  c=(A[0][i*3+2],A[1][i*3+2],A[2][i*3+2]);
  draw(surface(a--b--c--cycle),surfacepen = m);        // draw i-th triangle
}
path3 no_show = path3(scale(0) * box((-1,-1),(1,1)));
draw(surface(no_show), surfacepen=m);        // draw i-th triangle
"""


# meta class for all Asy objects require a from_ctk method
# and a __str__ method
class AsyObject(ABC):
    """Abstract base class for all Asy objects."""

    @abstractmethod
    def __str__(self):
        pass

    @classmethod
    @abstractmethod
    def from_ctk(
        cls,
        ctk_scene: Scene,
        user_settings: dict | None = None,
    ) -> AsyObject:
        pass


# Make classes out of the templates
@dataclass
class AsyLine(AsyObject):
    pos_pairs: list
    color: str
    linewidth: float

    def __str__(self):
        return (
            Environment()
            .from_string(TEMP_LINE)
            .render(
                posPairs=self.pos_pairs,
                color=self.color,
            )
        )

    @classmethod
    def from_ctk(
        cls,
        ctk_scene: Scene,
        user_settings: dict | None = None,
    ) -> AsyLine:
        """Create an AsyLine object from a ctk scene object.

        Args:
            ctk_scene (Scene): The ctk scene object to convert.
            user_settings (dict, optional): User settings for different
                objects, keyed by the ctk object type.

        Returns:
            AsyLine: The AsyLine object.
        """
        ipos = map(tuple, ctk_scene.positions[0::2])
        fpos = map(tuple, ctk_scene.positions[1::2])
        posPairs = [*zip(ipos, fpos)]

        linewidth = _read_properties(
            ctk_scene, property="linewidth", user_settings=user_settings
        )
        color = _read_color(ctk_scene, user_settings=user_settings)
        return cls(pos_pairs=posPairs, color=color, linewidth=linewidth)


@dataclass
class AsySphere(AsyObject):
    positions: list
    radius: float
    color: str
    opac: float
    light: bool

    def __str__(self):
        if self.light:
            return (
                Environment()
                .from_string(TEMP_SPHERE)
                .render(
                    positions=self.positions,
                    radius=self.radius,
                    color=self.color,
                    opac=self.opac,
                )
            )
        return (
            Environment()
            .from_string(TEMP_SPHERE_NOLIGHT)
            .render(positions=self.positions, radius=self.radius, color=self.color)
        )

    @classmethod
    def from_ctk(
        cls,
        ctk_scene: Scene,
        user_settings: dict | None = None,
    ) -> AsySphere:
        """Create an AsyLine object from a ctk scene object.

        Args:
            ctk_scene (Scene): The ctk scene object to convert.
            user_settings (dict, optional): User settings for different
                objects, keyed by the ctk object type.

        Returns:
            AsySphere: The AsySphere object.
        """
        positions = [tuple(pos) for pos in ctk_scene.positions]
        radius = _read_properties(
            ctk_scene, property="radius", user_settings=user_settings
        )
        color = _read_color(ctk_scene, user_settings=user_settings)
        opacity = _read_properties(
            ctk_scene, property="opacity", user_settings=user_settings
        )
        light = _read_properties(
            ctk_scene, property="light", user_settings=user_settings
        )

        # TODO: Implement partial spheres later
        if ctk_scene.phiStart or ctk_scene.phiEnd:
            raise NotImplementedError

        # phiStart = ctk_scene.phiStart or 0 # not yet implemented
        # phiEnd = ctk_scene.phiEnd or 2*pi

        return cls(
            positions=positions,
            radius=radius,
            color=color,
            opac=opacity,
            light=light,
        )


@dataclass
class AsyCylinder(AsyObject):
    pos_pairs: list
    radius: float
    color: str
    opac: float
    light: bool

    def __str__(self):
        if self.light:
            return (
                Environment()
                .from_string(TEMP_CYLINDER)
                .render(
                    posPairs=self.pos_pairs,
                    radius=self.radius,
                    color=self.color,
                    opac=self.opac,
                )
            )
        return (
            Environment()
            .from_string(TEMP_CYLINDER_NOLIGHT)
            .render(posPairs=self.pos_pairs, radius=self.radius, color=self.color)
        )

    @classmethod
    def from_ctk(
        cls,
        ctk_scene: Scene,
        user_settings: dict | None = None,
    ) -> AsyCylinder:
        """Create an AsyLine object from a ctk scene object.

        Args:
            ctk_scene (Scene): The ctk scene object to convert.
            user_settings (dict, optional): User settings for different
                objects, keyed by the ctk object type.

        Returns:
            AsyCylinder: The AsyCylinder object.
        """
        posPairs = [
            [tuple(ipos), tuple(fpos)] for ipos, fpos in ctk_scene.positionPairs
        ]
        radius = _read_properties(
            ctk_scene, property="radius", user_settings=user_settings
        )
        color = _read_color(ctk_scene, user_settings=user_settings)
        opacity = _read_properties(
            ctk_scene, property="opacity", user_settings=user_settings
        )
        light = _read_properties(
            ctk_scene, property="light", user_settings=user_settings
        )
        return cls(
            pos_pairs=posPairs,
            radius=radius,
            color=color,
            opac=opacity,
            light=light,
        )


@dataclass
class AsySurface(AsyObject):
    positions: list
    color: str
    opac: float
    light: bool

    def __str__(self):
        if self.light:
            return (
                Environment()
                .from_string(TEMP_SURF)
                .render(positions=self.positions, color=self.color, opac=self.opac)
            )
        return (
            Environment()
            .from_string(TEMP_SURF_NOLIGHT)
            .render(positions=self.positions, color=self.color)
        )

    @classmethod
    def from_ctk(
        cls,
        ctk_scene: Scene,
        user_settings: dict | None = None,
    ) -> AsySurface | None:
        """Create an AsyLine object from a ctk scene object.

        Args:
            ctk_scene (Scene): The ctk scene object to convert.
            user_settings (dict, optional): User settings for different
                objects, keyed by the ctk object type.

        Returns:
            AsySurface: The AsySurface object.
        """
        if len(ctk_scene.positions) < 1:
            return None

        num_triangle = len(ctk_scene.positions) / 3.0
        # sanity check the mesh must be triangles
        if not num_triangle.is_integer():
            raise ValueError("Surface mesh must be triangles")
        positions = tuple(f"{{{x[0]}, {x[1]}, {x[2]}}}" for x in ctk_scene.positions)

        # asymptote just needs the xyz positions
        num_triangle = int(num_triangle)
        pos_xyz = tuple(
            chain.from_iterable(
                [
                    (positions[itr * 3], positions[itr * 3 + 1], positions[itr * 3 + 2])
                    for itr in range(num_triangle)
                ]
            )
        )

        color = _read_color(ctk_scene, user_settings=user_settings)
        opacity = _read_properties(
            ctk_scene, property="opacity", user_settings=user_settings
        )
        light = _read_properties(
            ctk_scene, property="light", user_settings=user_settings
        )
        return cls(positions=pos_xyz, color=color, opac=opacity, light=light)


ASY_OBJS = {
    "lines": AsyLine,
    "spheres": AsySphere,
    "cylinders": AsyCylinder,
    "surface": AsySurface,
}


def _read_properties(
    ctk_scene: Scene,
    property: str,
    user_settings: dict | None = None,
) -> Any:
    """Read the settings for the Asy object from the ctk scene or the user settings.

    The order of preference is when looking for a property:
        1. User settings `{scene_name: {property: value}`
        2. CTK `Scene._meta["asy"][property]` attribute.
        3. CTK `Scene.property` attribute.
        4. Default settings.

    Args:
        ctk_scene (Scene): The CTK scene.
        property (str): The property to read from the CTK scene.
        user_settings (dict, optional): User settings for different
            objects, keyed by the CTK object type.
    """
    # prefer the user settings over the CTK scene settings
    scene_name = ctk_scene.type

    # user settings
    if user_settings is not None:
        setting = user_settings.get(scene_name, {}).get(property)
        if setting is not None:
            return setting

    # meta attribute
    ctk_meta = ctk_scene._meta
    if ctk_meta is not None:
        setting = ctk_meta.get("asy", {}).get(property)
        if setting is not None:
            return setting
    # property attribute
    try:
        ctk_att = getattr(ctk_scene, property)
    except AttributeError:
        ctk_att = None
    if ctk_att is not None:
        return ctk_att

    # default settings
    return _DEFAULTS["scene"].get(scene_name, {}).get(property)


def _read_color(ctk_scene: Scene, user_settings: dict | None = None) -> str | None:
    """Read the color from the ctk scene or the user settings.

    Args:
        ctk_scene (Scene): The ctk scene.
        user_settings (AsySetting, optional): The user settings. Defaults to None.
    """
    color = _read_properties(ctk_scene, "color", user_settings)
    # strip the # from the color if it exists
    if color is None:
        return None

    # if is string
    if isinstance(color, str):
        if color.startswith("#"):
            return color[1:]
        return color

    raise ValueError(
        f"Color {color} is not a valid color. Please use a hex color string."
    )


def update_scene_asy_settings(ctk_scene: Scene, user_settings: dict) -> Scene:
    """Update the scene's asy settings with the user settings.

    Update the scene's _meta attribute recursively with the user settings.
    Used to update properties of a sub-scene.

    Args:
        ctk_scene (Scene): The ctk scene.
        user_settings (dict): The user settings.

    Returns:
        Scene: The updated scene.
    """
    ctk_scene._meta = ctk_scene._meta or {}
    ctk_scene._meta["asy"] = user_settings
    if hasattr(ctk_scene, "contents"):
        [
            update_scene_asy_settings(child, user_settings)
            for child in ctk_scene.contents
        ]


def asy_write_data(
    input_scene_comp: Scene,
    fstream: IO,
    user_settings: dict | None = None,
):
    """Write the Asy code to file.

    Parse a primitive display object in crystaltoolkit and print it to
    asymptote file.

    Args:
        input_scene_comp (Scene): CTK Scene Object
        fstream (IO): File stream to write to
    """
    scene_obj_type = input_scene_comp.type
    if ASY_OBJS.get(scene_obj_type) is None:
        print(scene_obj_type)
        return

    asy_obj = ASY_OBJS[scene_obj_type]
    asy_out = asy_obj.from_ctk(ctk_scene=input_scene_comp, user_settings=user_settings)
    fstream.write(str(asy_out))

    # TODO we can make the line solid for the foreground and dashed for the background
    # This will require use to modify the way the line objects are generated
    # at each vertex in the unit cell, we can evaluate the sum of all three lattice vectors from the point
    # then the <vec_sum | vec_to_camera> for each vertex.  The smallest
    # normalized vertex contains the three lines that should be dashed


def traverse_scene_object(scene_data, fstream, user_settings=None) -> None:
    """Traverse object."""
    for sub_object in scene_data.contents:
        if isinstance(sub_object, list):
            for iobj in sub_object:
                traverse_scene_object(iobj)
            continue
        if hasattr(sub_object, "type"):
            asy_write_data(sub_object, fstream, user_settings=user_settings)
        else:
            traverse_scene_object(sub_object, fstream, user_settings=user_settings)


def write_ctk_scene_to_file(ctk_scene, file_name, **kwargs):
    """Write the ctk scene to file.

    Args:
        ctk_scene: Scene object from crystaltoolkit
        file_name: Output asymptote file and location
    """
    target = tuple(-ii for ii in ctk_scene.origin)
    header = Environment().from_string(HEADER).render(target=target)

    with open(file_name, "w") as fstream:
        fstream.write(header)
        traverse_scene_object(ctk_scene, fstream, **kwargs)


def write_asy_file(renderable_object, file_name, **kwargs):
    """Generate the scene object and write it to file.

    Args:
        renderable_object: Object to be rendered
        file_name: name of file
    """
    if isinstance(renderable_object, (Structure, StructureGraph)):
        kwargs["explicitly_calculate_polyhedra_hull"] = True
    write_ctk_scene_to_file(renderable_object.get_scene(**kwargs), file_name)
