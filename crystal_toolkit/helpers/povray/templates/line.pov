// Draw the edges of the supercell in the scene

#declare bbox = texture { pigment { rgb <1,1,1> } }

{% for ipos, fpos in posPairs -%}
cylinder {<{{ipos}}>, <{{fpos}}>, 0.02 texture {bbox} no_shadow}
{% endfor %}

{% for val in cylCaps -%}
sphere {<{{val}}>, 0.02 texture {bbox} no_shadow}
{% endfor %}