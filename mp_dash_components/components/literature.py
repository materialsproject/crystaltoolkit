import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from mp_dash_components.components.core import PanelComponent

from pymatgen import Structure, MPRester

from pybtex.database.input.bibtex import Parser
from pybtex.plugin import find_plugin
from io import StringIO

sample_struct = MPRester().get_structure_by_material_id("mp-5020")


class LiteratureComponent(PanelComponent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def title(self):
        return "Literature Mentions"

    @property
    def description(self):
        return (
            "The material loaded into Crystal Toolkit is matched against  "
            "materials and their associated references in the Material "
            "Project database."
        )

    @staticmethod
    def entries_to_markdown(entries):
        """Utility function to convert a BibTeX entries containing
        references into a Markdown string. Borrowed from propnet.
        """

        # TODO: replace this, very messy

        pybtex_style = find_plugin('pybtex.style.formatting', 'plain')()
        pybtex_md_backend = find_plugin('pybtex.backends', 'markdown')

        # hack to not print labels (may remove this later)
        def write_entry(self, key, label, text):
            self.output(u'%s<splitkey>' % text)

        pybtex_md_backend.write_entry = write_entry
        pybtex_md_backend.symbols['newblock'] = '  \n>'
        pybtex_md_backend = pybtex_md_backend()

        entries_formatted = pybtex_style.format_entries(entries.values())
        output = StringIO()
        pybtex_md_backend.write_to_stream(entries_formatted, output)

        # add blockquote style
        references_md = "  \n  \n".join([f"> {md}  "
                                     for md in output.getvalue().split('<splitkey>')])

        return references_md

    def update_contents(self, new_store_contents):

        #struct = self.from_data(new_store_contents)
        struct = MPRester().get_structure_by_material_id("mp-5020")
        if not isinstance(struct, Structure):
            raise PreventUpdate(
                "Literature mentions can only be retrieved for crystallographic "
                "structures at present and not molecules. Please make a feature "
                "request if this would be useful for you, and it will be "
                "prioritized."
            )

        with MPRester() as mpr:
            mpids = mpr.find_structure(struct)

            if len(mpids) == 0:
                raise PreventUpdate(
                    "No structures in the Materials Project database match this "
                    "crystal structure, so literature mentions cannot be retrieved. "
                    "Please submit this structure to Materials Project if you'd "
                    "like it to be added to the Materials Project database."
                )

            all_entries = {}
            for mpid in mpids:
                references = mpr.get_materials_id_references(mpid)
                all_entries.update(Parser().parse_string(references).entries)

        return dcc.Markdown(self.entries_to_markdown(all_entries), className="mpc-markdown")
