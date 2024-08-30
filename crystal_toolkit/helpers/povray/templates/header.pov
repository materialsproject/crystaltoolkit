#version 3.7 ;
global_settings { assumed_gamma 1.8
                  ambient_light rgb<1, 1, 1>
}
background { colour srgbt <0.0, 0.0, 0.0, 1.0> } // Set the background to transparent

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