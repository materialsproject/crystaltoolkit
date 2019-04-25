"""
Export wrapper for asymptote
For creating publication quality plots
"""
from jinja2 import Environment
from crystal_toolkit.components.structure import StructureMoleculeComponent

HEAD = """
size(300);
import solids;
// Camera information
currentprojection=orthographic (
camera=(8,5,4),
up=(0,0,1),
target=(0,0,0),
zoom=0.5
);

// Plot appearance parameters
real cylR=0.1;

// Basic function for drawing spheres
void drawSpheres(triple[] C, real R, pen p=currentpen){
  for(int i=0;i<C.length;++i){
    draw(sphere(C[i],R).surface(
                        new pen(int i, real j){return p;}
                        )
    );
  }
}

// Draw a cylinder
void Draw(guide3 g,pen p=currentpen){
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

TEMP_CYLINDER = """
pen connectPen=rgb('{{color}}');
{% for ipos, fpos in posPairs %}
triple IPOS = {{ipos}};
triple FPOS = {{fpos}};
Draw(IPOS--FPOS, connectPen);
{% endfor %}
"""

TEMP_LINE = """
{% for ipos, fpos in posPairs %}
triple IPOS = {{ipos}};
triple FPOS = {{fpos}};
draw(IPOS--FPOS, dashed);
{% endfor %}
"""

def asy_write_data(input_scene_comp, fstream):
    """
    parse a primitive display object in crystaltoolkit and print it to asymptote
    input_scene_comp
    fstream
    """
    if input_scene_comp['type'] == 'spheres':
        positions = input_scene_comp['positions']
        positions = [tuple(pos) for pos in positions]
         
        fstream.write(Environment().from_string(TEMP_SPHERE).render(
            positions=positions,
            radius=input_scene_comp['radius'],
            color=input_scene_comp['color'].replace('#', '')))
        
    if input_scene_comp['type'] == 'cylinders':
        # need to transforme all the cylinders to vector
        posPairs = [
           [tuple(ipos), tuple(fpos)] for ipos, fpos in input_scene_comp['positionPairs']
        ]
        fstream.write(Environment().from_string(TEMP_CYLINDER).render(
            posPairs=posPairs, color=input_scene_comp['color'].replace('#', '')))
        
    if input_scene_comp['type'] == 'lines':
        # need to transforme all the cylinders to vector
        pos1, pos2 = input_scene_comp['positions'][0::2], input_scene_comp['positions'][1::2]
        posPairs = [
           [tuple(ipos), tuple(fpos)] for ipos, fpos in zip(pos1, pos2)
        ]
        fstream.write(Environment().from_string(TEMP_LINE).render(
            posPairs=posPairs))

    # TODO Leaving out polyhedra for now since asymptote 
    # does not have an easy way to generate convex polyhedra from the points
    # Need to write a python conversion between Convex type and surfaces to make this work.

    # TODO we can make the line solide for the forground and dashed for the background
    # This will require use to modify the way the line objects are generated
    # at each vertex in the unit cell, we can evaluate the sum of all three lattice vectors from the point
    # then the <vec_sum | vec_to_camera> for each vertex.  The smallest normalized vertex contians the three lines that should be dashed

def filter_data(scene_data, fstream):
    """
    Recursively traverse the scene_data dictionary to find objects to draw
    """
    if 'type' in scene_data.keys():
        asy_write_data(scene_data, fstream)
    else:
        for itr in scene_data['contents']:
            filter_data(itr, fstream)

def write_asy_file(smc , file_name):
    """
    smc : (StructureMoleculeComponent)
    """
    fstream = open(file_name, 'w')
    fstream.write(HEAD)
    filter_data(smc.initial_scene_data, fstream)
    fstream.close()
