// Draw Spheres

{% for val in positions -%}
Atom(<{{val}}>, {{radius}}, {{color}}, plastic_atom_finish)
{% endfor %}
