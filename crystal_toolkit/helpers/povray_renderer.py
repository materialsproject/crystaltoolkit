"""Export wrapper for POV-Ray.

For creating publication quality plots.
"""
from __future__ import annotations

from jinja2 import Environment

HEAD = """
#version 3.7 ;
global_settings { assumed_gamma 1.8
                  ambient_light rgb<1, 1, 1>
}
background { rgb 0. } // Set the background to black

/*
Create an Atom object along with some textures.
The arguments are: Atom( position, radius, color, finish )
*/

#declare plastic_atom_finish = finish {
                                specular 0.2
                                roughness 0.001
                                ambient 0.075
                                diffuse 0.55
                                brilliance 1.5
                                conserve_energy
                              }

#macro Atom (P1, R1, C1, F1)
  #local T = texture {
                       pigment { C1 }
                       finish { F1 }
                     }
  sphere { P1, R1 texture {T} no_shadow }
#end

"""

CAMERA = """
/*
Define the camera and the view of the atoms
*/

camera {
   orthographic
   location <i,  j,  k>
   look_at  <ii, jj, kk>
   sky <0, 0, 1>
}

"""

LIGHTS = """
/*
Define light sources to illuminate the atoms. For visualizing mediam
media_interaction and media_attenuation are set to "off" so voxel
data is rendered to be transparent. Lights are automatically oriented
with respect to the camera position.
*/

// Overhead light source
light_source {
    <0, 0, 10>
    color rgb <1,1,1>*0.5
    parallel
    point_at <ii, jj, kk>*0.5
    media_interaction off
    media_attenuation off
}

// Rear (forward-facing) light source
light_source {
    < (i-ii), (j-jj), (k-kk)>*4
    color rgb <1,1,1> * 0.5
    parallel
    point_at <ii, jj, kk>
    media_interaction off
    media_attenuation off
}

// Left light source
light_source {
    <( (i-ii)*cos(60*pi/180) - (j-jj)*sin(60*pi/180) ), ( (i-ii)*sin(60*pi/180) + (j-jj)*cos(60*pi/180) ), k>
    color rgb <1,1,1>*0.5
    parallel
    point_at <ii, jj, kk>
    media_interaction off
    media_attenuation off
}

// Right light source
light_source {
    <( (i-ii)*cos(-60*pi/180) - (j-jj)*sin(-60*pi/180) ), ( (i-ii)*sin(-60*pi/180) + (j-jj)*cos(-60*pi/180) ), k>
    color rgb <1,1,1>*0.5
    parallel
    point_at <ii, jj, kk>
    media_interaction off
    media_attenuation off
}

"""

TEMP_SPHERE = """
// Draw atoms in the scene

{% for val in positions -%}
Atom(<{{val}}>, {{radius}}, {{color}}, plastic_atom_finish)
{% endfor %}
"""

TEMP_CYLINDER = """
// Draw bonds between atoms in the scene

#declare bond_texture = texture { pigment { {{color}} } finish { plastic_atom_finish } };

{% for ipos, fpos in posPairs -%}
cylinder { <{{ipos}}>, <{{fpos}}>, 0.1 texture { bond_texture } no_shadow }
{% endfor %}
"""

TEMP_LINE = """
// Draw the edges of the supercell in the scene

#declare bbox = texture { pigment { rgb <1,1,1> } }

{% for ipos, fpos in posPairs -%}
cylinder {<{{ipos}}>, <{{fpos}}>, 0.02 texture {bbox} no_shadow}
{% endfor %}

{% for val in cylCaps -%}
sphere {<{{val}}>, 0.02 texture {bbox} no_shadow}
{% endfor %}
"""


def pov_write_data(input_scene_comp, fstream):
    """Parse a primitive display object in crystaltoolkit and print it to POV-Ray
    input_scene_comp fstream.
    """
    vect = "{:.4f},{:.4f},{:.4f}"

    if input_scene_comp["type"] == "spheres":
        # Render atoms
        positions = input_scene_comp["positions"]
        positions = [vect.format(*pos) for pos in positions]
        color = input_scene_comp["color"].replace("#", "")
        color = tuple(int(color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
        color = f"rgb<{vect.format(*color)}>"

        fstream.write(
            Environment()
            .from_string(TEMP_SPHERE)
            .render(
                positions=positions,
                radius=input_scene_comp["radius"],
                color=color,
            )
        )

    if input_scene_comp["type"] == "cylinders":
        # Render bonds between atoms
        posPairs = [
            [vect.format(*ipos), vect.format(*fpos)]
            for ipos, fpos in input_scene_comp["positionPairs"]
        ]
        color = input_scene_comp["color"].replace("#", "")
        color = tuple(int(color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
        color = f"rgb<{vect.format(*color)}>"
        fstream.write(
            Environment()
            .from_string(TEMP_CYLINDER)
            .render(posPairs=posPairs, color=color)
        )

    if input_scene_comp["type"] == "lines":
        # Render the cell
        pos1, pos2 = (
            input_scene_comp["positions"][0::2],
            input_scene_comp["positions"][1::2],
        )
        cylCaps = {tuple(pos) for pos in input_scene_comp["positions"]}
        cylCaps = [vect.format(*pos) for pos in cylCaps]
        posPairs = [
            [vect.format(*ipos), vect.format(*fpos)] for ipos, fpos in zip(pos1, pos2)
        ]
        fstream.write(
            Environment()
            .from_string(TEMP_LINE)
            .render(posPairs=posPairs, cylCaps=cylCaps)
        )


def filter_data(scene_data, fstream):
    """Recursively traverse the scene_data dictionary to find objects to draw."""
    if "type" in scene_data:
        pov_write_data(scene_data, fstream)
    else:
        for itr in scene_data["contents"]:
            filter_data(itr, fstream)


def write_pov_file(smc, file_name):
    """Args:
    smc (StructureMoleculeComponent): Object containing the scene data.
    file_name (str): name of the file to write to.
    """
    with open(file_name, "w") as fstream:
        fstream.write(HEAD)
        fstream.write(CAMERA)
        fstream.write(LIGHTS)
        filter_data(smc.initial_scene_data, fstream)

    render_settings = get_render_settings()
    with open(file_name, "w") as file:
        file.write(render_settings)


def get_render_settings(file_name):
    """Creates a POV-Ray render.ini file."""
    image_name = f"{file_name[:-4]}.png"

    return f"""
Input_File_Name = {file_name}
Output_File_Name = {image_name}
Display = 1
# -- Option to switch on the density
Declare=render_density=0     # 0 = off, 1 = on
Quality = 9
Height = 1200
Width = 1600
# -- Uncomment below for higher quality rendering
Antialias = On
Antialias_Threshold = 0.01
Antialias_Depth = 4
Jitter_Amount = 1.0
# -- Set the camera position
Declare=i=8
Declare=j=5
Declare=k=4
# -- Set the look_at position
Declare=ii=0
Declare=jj=0
Declare=kk=0
"""
