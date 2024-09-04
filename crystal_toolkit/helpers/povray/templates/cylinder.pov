// Draw bonds between atoms in the scene

#declare bond_texture = texture { pigment { {{color}} } finish { plastic_atom_finish } };

{% for ipos, fpos in posPairs -%}
cylinder { <{{ipos}}>, <{{fpos}}>, 0.1 texture { bond_texture } no_shadow }
{% endfor %}
