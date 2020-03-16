"""
Export wrapper for asymptote (ASY)
For creating publication quality plots
Since ASY does not have the nested tree structure of threejs,
we just have to traverse the tree and draw each material as we see them.

TODO The code should also appends a set of special points at the end in case the user wants to add more "hand drawn" features to the plot

"""
import logging
from itertools import chain

from jinja2 import Environment

from pymatgen import Structure, Molecule
from pymatgen.analysis.graphs import StructureGraph
from crystal_toolkit.helpers.utils import update_object_args

logger = logging.getLogger(__name__)

HEAD = """
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
drawSpheres(spheres, {{radius}}, rgb('{{color}}'));
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
drawSpheres_nolight(spheres, {{radius}}, rgb('{{color}}'));
"""



TEMP_CYLINDER = """
pen connectPen=rgb('{{color}}');
{% for ipos, fpos in posPairs %}
triple IPOS = {{ipos}};
triple FPOS = {{fpos}};
Draw(IPOS--FPOS, connectPen, {{radius}});
{% endfor %}
"""

TEMP_LINE = """
pen connectPen=rgb('{{color}}');
{% for ipos, fpos in posPairs %}
triple IPOS = {{ipos}};
triple FPOS = {{fpos}};
draw(IPOS--FPOS, connectPen);
{% endfor %}
"""

TEMP_CYLINDER = """
pen connectPen=rgb('{{color}}');
{% for ipos, fpos in posPairs %}
triple IPOS = {{ipos}};
triple FPOS = {{fpos}};
Draw(IPOS--FPOS, connectPen, {{radius}});
{% endfor %}
"""

TEMP_SURF = """
real[][] A = {
{% for ipos in positions -%}
    {{ipos}},
{% endfor %}
};
A = transpose(A);

material m = rgb('{{face_color}}') + opacity({{opac}});
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

material m = material(diffusepen=opacity({{opac}}), emissivepen=rgb("{{face_color}}"), shininess=0);
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

# Functions for parsing specific shapes
# Each function should only take in the CTK object and the changes to the
# default display parameters


def _get_lines(ctk_scene, d_args=None):
    """return the ASY string output to draw cylinders

    Arguments:
        ctk_scene {Scene} -- CTK Scene Object with ctk_scene.type == 'cylinders'

    Keyword Arguments:
        d_args {dict} -- User defined defaults of the plot (default: {None})
    """
    assert ctk_scene.type == "lines"
    updated_defaults = update_object_args(
        d_args, object_name="Lines", allowed_args=["linewidth", "color"]
    )
    ipos = map(tuple, ctk_scene.positions[0::2])
    fpos = map(tuple, ctk_scene.positions[1::2])
    posPairs = [*zip(ipos, fpos)]

    linewidth = ctk_scene.linewidth or updated_defaults["linewidth"]
    color = ctk_scene.color or updated_defaults["color"]
    color = color.replace("#", "")
    return (
        Environment()
        .from_string(TEMP_LINE)
        .render(posPairs=posPairs, color=color, linewidth=linewidth)
    )


def _get_spheres(ctk_scene, d_args=None):
    """return the ASY string output to draw the spheres

    Arguments:
        ctk_scene {Scene} -- CTK Scene Object with ctk_scene.type == 'spheres'

    Keyword Arguments:
        d_args {dict} -- User defined defaults of the plot (default: {None})
    """
    assert ctk_scene.type == "spheres"
    updated_defaults = update_object_args(
        d_args, object_name="Spheres", allowed_args=["radius", "color"]
    )

    positions = [tuple(pos) for pos in ctk_scene.positions]
    radius = ctk_scene.radius or updated_defaults["radius"]
    color = ctk_scene.color or updated_defaults["color"]
    color = color.replace("#", "")
    if ctk_scene.phiStart or ctk_scene.phiEnd:
        raise NotImplementedError

    # phiStart = ctk_scene.phiStart or 0 # not yet implemented
    # phiEnd = ctk_scene.phiEnd or 2*pi

    return (
        Environment()
        .from_string(TEMP_SPHERE)
        .render(positions=positions, radius=radius, color=color)
    )


def _get_cylinders(ctk_scene, d_args=None):
    """return the ASY string output to draw cylinders

    Arguments:
        ctk_scene {Scene} -- CTK Scene Object with ctk_scene.type == 'cylinders'

    Keyword Arguments:
        d_args {dict} -- User defined defaults of the plot (default: {None})
    """
    assert ctk_scene.type == "cylinders"
    updated_defaults = update_object_args(
        d_args, object_name="Cylinders", allowed_args=["radius", "color"]
    )

    posPairs = [[tuple(ipos), tuple(fpos)] for ipos, fpos in ctk_scene.positionPairs]
    radius = ctk_scene.radius or updated_defaults["radius"]
    color = ctk_scene.color or updated_defaults["color"]
    color = color.replace("#", "")
    return (
        Environment()
        .from_string(TEMP_CYLINDER)
        .render(posPairs=posPairs, color=color, radius=radius)
    )


def _get_surface(ctk_scene, d_args=None):
    """return the ASY string output to draw cylinders

    Arguments:
        ctk_scene {Scene} -- CTK Scene Object with ctk_scene.type == 'surface'

    Keyword Arguments:
        d_args {dict} -- User defined defaults of the plot (default: {None})
    """
    assert (ctk_scene.type == 'surface')
    if len(ctk_scene.positions) == 0:
        return "" # print nothing
    updated_defaults = update_object_args(
        d_args, object_name="Surfaces", allowed_args=["opacity", "color", "edge_width"]
    )
    color = ctk_scene.color or updated_defaults["color"]
    color = color.replace("#", "")
    opacity = ctk_scene.opacity or updated_defaults["opacity"]

    positions = tuple(
        map(lambda x: "{" + f"{x[0]}, {x[1]}, {x[2]}" + "}", ctk_scene.positions)
    )
    num_triangle = len(ctk_scene.positions) / 3.0
    # sanity check the mesh must be triangles
    assert num_triangle.is_integer()

    # # make decision on transparency
    # transparent = if obj_args['opacity'] < 0.99
    #
    # # asymptote just needs the xyz positions
    num_triangle = int(num_triangle)
    pos_xyz = tuple(
        chain.from_iterable(
            [
                (positions[itr * 3], positions[itr * 3 + 1], positions[itr * 3 + 2])
                for itr in range(num_triangle)
            ]
        )
    )
    #
    # # write the data array
    data_array_asy = (
        Environment()
        .from_string(TEMP_SURF)
        .render(positions=pos_xyz, face_color=color, opac=opacity)
    )

    return data_array_asy

    # write the


def asy_write_data(input_scene_comp, fstream):
    """
    parse a primitive display object in crystaltoolkit and print it to asymptote
    input_scene_comp
    fstream
    """
    if input_scene_comp.type == "spheres":
        asy_out = _get_spheres(input_scene_comp)
        fstream.write(asy_out)

    if input_scene_comp.type == "cylinders":
        asy_out = _get_cylinders(input_scene_comp)
        fstream.write(asy_out)

    if input_scene_comp.type == "lines":
        asy_out = _get_lines(input_scene_comp)
        fstream.write(asy_out)

    if input_scene_comp.type == "surface":
        asy_out = _get_surface(input_scene_comp)
        fstream.write(asy_out)

    return

    # TODO we can make the line solide for the forground and dashed for the background
    # This will require use to modify the way the line objects are generated
    # at each vertex in the unit cell, we can evaluate the sum of all three lattice vectors from the point
    # then the <vec_sum | vec_to_camera> for each vertex.  The smallest
    # normalized vertex contians the three lines that should be dashed


def filter_data(scene_data, fstream):
    """
    Recursively traverse the scene_data dictionary to find objects to draw
    """
    if "type" in scene_data.keys():
        asy_write_data(scene_data, fstream)
    else:
        for itr in scene_data["contents"]:
            filter_data(itr, fstream)


def traverse_scene_object(scene_data, fstream):
    """
    Traverse object
    """
    for sub_object in scene_data.contents:
        if isinstance(sub_object, list):
            for iobj in sub_object:
                traverse_scene_object(iobj)
            continue
        elif hasattr(sub_object, "type"):
            asy_write_data(sub_object, fstream)
        else:
            traverse_scene_object(sub_object, fstream)


def write_ctk_scene_to_file(ctk_scene, file_name):
    """
    ctk_scene : Scene object from crystaltoolkit
    filename : Output asymptote file and location
    """
    fstream = open(file_name, "w")
    target = tuple(-ii for ii in ctk_scene.origin)
    header = Environment().from_string(HEAD).render(target=target)
    fstream.write(header)
    traverse_scene_object(ctk_scene, fstream)
    fstream.close()


def write_asy_file(renderable_object, file_name, **kwargs):
    """
    Generate the scene object and write it to file

    Args:
        renderable_object: Object to be rendered
        file_name: name of file
    """
    if isinstance(renderable_object, Structure) or isinstance(
            renderable_object, StructureGraph):
        kwargs['explicitly_calculate_polyhedra_hull'] = True
    write_ctk_scene_to_file(renderable_object.get_scene(**kwargs), file_name)
