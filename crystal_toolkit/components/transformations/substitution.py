from __future__ import annotations

from pymatgen.transformations.standard_transformations import SubstitutionTransformation

from crystal_toolkit.components.transformations.core import TransformationComponent


class SubstitutionTransformationComponent(TransformationComponent):
    @property
    def title(self) -> str:
        return "Substitute one species for another"

    @property
    def description(self) -> str:
        return """Replace one species in your structure (\"Previous Species\")
with another species (\"New Species\"). The new species can be specified as an
element (for example, O), as an element with an oxidation state (for example, O2-)
or as a composition (for example, {"Au":0.5, "Cu":0.5} for a 50/50 mixture of gold
and copper). Please consult the pymatgen documentation for more information.
"""

    @property
    def transformation(self):
        return SubstitutionTransformation

    def options_layouts(self, state=None, structure=None):
        if structure and structure.is_ordered:
            species_mapping = {el: el for el in map(str, structure.types_of_specie)}
        else:
            species_mapping = {}

        state = state or {"species_map": species_mapping}

        species_mapping = self.get_dict_input(
            label="Species Mapping",
            kwarg_label="species_map",
            state=state,
            help_str="A mapping from an original species (element or element with oxidation state, e.g. O or O2-) "
            "to a new species (element, element with oxidation state, or a composition, e.g. O or O2- or "
            '{"Au": 0.5, "Cu": 0.5}). In pymatgen, these are Element, Species and Composition classes '
            "respectively.",
            key_name="Original Species",
            value_name="New Species",
        )

        return [species_mapping]

    def generate_callbacks(self, app, cache) -> None:
        super().generate_callbacks(app, cache)
        #
        # @app.callback(
        #     Output(self.id("transformation_args_kwargs"), "data"),
        #     Input(self.id("species_mapping"), "data"),
        # )
        # def update_transformation_kwargs(rows):
        #     def get_el_occu(string):
        #         try:
        #             el_occu = literal_eval(string)
        #         except ValueError:
        #             el_occu = string
        #         return el_occu
        #
        #     species_map = {
        #         get_el_occu(row["prev"]): get_el_occu(row["new"])
        #         for row in rows
        #         if (row["prev"] and row["new"])
        #     }
        #
        #     print(species_map)
        #
        #     return {"args": [species_map], "kwargs": {}}
