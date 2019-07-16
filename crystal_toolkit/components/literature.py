import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import Label, Tag

from pymatgen import Structure, MPRester

import re

from pybtex.database.input.bibtex import Parser
from pybtex.plugin import find_plugin
from pybtex.style.formatting.unsrt import sentence, field
from io import StringIO

from bibtexparser import loads

from habanero import Crossref
from habanero.cn import content_negotiation

import codecs
import latexcodec

import os

CROSSREF_MAILTO = os.environ.get("CROSSREF_MAILTO", None)


class LiteratureComponent(PanelComponent):
    def __init__(
        self, *args, use_crossref=True, use_crossref_formatting=True, **kwargs
    ):
        self.use_crossref = use_crossref
        self.use_crossref_formatting = use_crossref_formatting
        super().__init__(*args, **kwargs)

        @MPComponent.cache.memoize()
        def get_materials_id_references(mpid):
            with MPRester() as mpr:
                references = mpr.get_materials_id_references(mpid)
            return references

        self.get_materials_id_references = get_materials_id_references

        @MPComponent.cache.memoize(timeout=0)
        def format_bibtex_references(
            references, use_crossref=True, custom_formatting=True
        ):
            self._format_bibtex_references(
                references,
                use_crossref=use_crossref,
                custom_formatting=custom_formatting,
            )

        self.format_bibtex_references = format_bibtex_references
        self.format_bibtex_references = format_bibtex_references

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

    @property
    def loading_text(self):
        return "Looking up journal entries. This is not currently pre-cached so may take up to a minute"

    @staticmethod
    def _pybtex_entries_to_markdown(entries):
        """Utility function to convert a BibTeX entries containing
        references into a Markdown string. Borrowed from propnet.
        """

        # TODO: replace this, very messy

        Pybtex_style = find_plugin("pybtex.style.formatting", "plain")()

        # hack so as to avoid messing with capitalization of formulae
        def format_title(self, e, which_field, as_sentence=True):
            formatted_title = field(which_field)
            if as_sentence:
                return sentence[formatted_title]
            else:
                return formatted_title

        Pybtex_style.format_title = format_title
        pybtex_style = Pybtex_style()

        Pybtex_md_backend = find_plugin("pybtex.backends", "markdown")

        # hack to not print labels (may remove this later)
        def write_entry(self, key, label, text):
            self.output("%s<splitkey>" % text)

        Pybtex_md_backend.write_entry = write_entry
        Pybtex_md_backend.symbols["newblock"] = "  \n>"
        pybtex_md_backend = Pybtex_md_backend()

        entries_formatted = pybtex_style.format_entries(entries.values())
        output = StringIO()
        pybtex_md_backend.write_to_stream(entries_formatted, output)

        # add blockquote style
        references_md = "  \n  \n".join(
            [f"> {md}  " for md in output.getvalue().split("<splitkey>")]
        )

        return references_md

    @staticmethod
    def _bibtex_entry_to_author_text(entry, et_al_cutoff=3):
        entry = loads(entry).entries[0]
        if "author" not in entry:
            return ""
        authors = codecs.decode(entry["author"], "ulatex")
        authors = re.sub(r"\s*{.*}\s*", " ", authors).replace("{}", "")
        authors = authors.split(" and ")
        if len(authors) > et_al_cutoff:
            authors = authors[0:et_al_cutoff]
        if len(authors) > 1:
            return ", ".join(authors[0:-1]) + " and " + authors[-1]
        else:
            return ""

    @staticmethod
    def _item_to_journal_div(item):
        # journal, issue, volume, date-parts (year), pages

        contents = []

        if item["journal"]:
            contents.append(html.I(item["journal"]))
        else:
            return html.Div()

        if item["volume"]:
            contents.append(html.Span(", "))
            contents.append(html.B(item["volume"]))

        if item["issue"]:
            contents.append(html.Span(f" ({item['issue']})"))

        if item["pages"]:
            contents.append(html.Span(f", {item['pages']}."))
        else:
            contents.append(html.Span(f"."))

        if item["date-parts"][0]:
            contents.append(html.Span(f" {item['date-parts'][0][0] }."))

        return html.Div(contents, style={"display": "inline-block"})

    def _get_references_for_mpid(self, use_crossref=True, custom_formatting=True):
        return ...

    def update_contents(self, new_store_contents):
        """
        Structure -> mpid -> BibTeX references from MP -> (optional doi lookup
        via Crossref) -> formatting.
        Formatting is very messy right now.
        DOI lookup and (possibly) formatting should be cached in a builder.
        """

        struct = self.from_data(new_store_contents)

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

            all_references = []
            for mpid in mpids:
                all_references.append(mpr.get_materials_id_references(mpid))
                self.logger.debug(f"Retrieved references for {mpid}.")

        if self.use_crossref:

            cr = Crossref(mailto=CROSSREF_MAILTO)
            individual_references = set()
            for references in all_references:
                individual_references.update(set(references.split("\n\n")))

            # exclude Materials Proect references (these are intended to be
            # references for the structure specifically)
            refs_to_remove = set()
            for ref in individual_references:
                if "Jain2013" in ref:
                    refs_to_remove.add(ref)
            individual_references -= refs_to_remove

            works = [cr.works(query=ref, limit=1) for ref in individual_references]
            self.logger.debug(f"Retrieved {len(works)} works from Crossref.")

            items = [
                work["message"]["items"][0]
                for work in works
                if len(work["message"]["items"]) > 0
            ]

            dois_to_item = {
                item["DOI"]: {
                    "cited-by": item.get("is-referenced-by-count", 0),
                    "score": item["score"],
                    "title": item.get("title", None),
                    "authors": item.get("author", []),
                    "journal": item.get("container-title", [None])[0],
                    "issue": item.get("issue", None),
                    "volume": item.get("volume", None),
                    "pages": item.get("page", None),
                    "date-parts": item.get("issued", {}).get("date-parts", [[None]]),
                }
                for item in items
                if item["score"] > 40
            }

            num_refs = len(dois_to_item)
            sorted_dois = sorted(
                list(dois_to_item.keys()),
                key=lambda doi: -dois_to_item[doi]["cited-by"],
            )

            if self.use_crossref_formatting:
                # use Crossref to retrieve pre-formatted text

                # remove leading "1. " from Science CSL style
                refs = {
                    doi: content_negotiation(ids=doi, format="text", style="science")[
                        3:
                    ]
                    for doi in dois_to_item.keys()
                }
                self.logger.debug(
                    f"Retrieved {len(refs)} formatted references from Crossref."
                )
                md = "  \n\n".join(
                    f"> [{refs[doi]}](https://dx.doi.org/{doi}) "
                    f"Cited by {dois_to_item[doi]['cited-by']}."
                    for doi in sorted_dois
                )
                formatted_references = dcc.Markdown(md, className="mpc-markdown")

            else:
                # else retrieve BibTeX entries to extract a nice author list
                # and perform our own formatting

                entries = {
                    doi: content_negotiation(ids=doi, format="bibtex")
                    for doi in sorted_dois
                }

                formatted_entries = []
                for doi, entry in entries.items():
                    author_string = self._bibtex_entry_to_author_text(entry)
                    journal_div = self._item_to_journal_div(dois_to_item[doi])

                    formatted_entries.append(
                        html.Blockquote(
                            [
                                html.A(
                                    [
                                        html.Div(
                                            [
                                                html.I(
                                                    # necessary since titles can contain HTML for superscripts etc.
                                                    dcc.Markdown(
                                                        dois_to_item[doi]["title"],
                                                        dangerously_allow_html=True,
                                                    )
                                                )
                                            ]
                                        ),
                                        html.Div([author_string]),
                                        html.Div(
                                            [
                                                journal_div,
                                                html.Span(
                                                    f" Cited by {dois_to_item[doi]['cited-by']}."
                                                ),
                                            ]
                                        ),
                                    ],
                                    href=f"https://dx.doi.org/{doi}",
                                )
                            ],
                            className="mpc",
                            style={"padding-left": "1rem", "margin-bottom": "1rem"},
                        )
                    )

                formatted_references = html.Div(formatted_entries)
        else:
            # this uses pybtex directly on stored BibTeX entries from MP
            # most-accurate references and faster since no Crossref lookup
            # is required but no dois/hyperlinks available
            all_entries = {}
            for references in all_references:
                all_entries.update(Parser().parse_string(references).entries)
            md = self._pybtex_entries_to_markdown(all_entries)
            formatted_references = dcc.Markdown(md, className="mpc-markdown")
            num_refs = len(all_entries)

        return html.Div(
            [
                Label(f"{num_refs} references found{':' if num_refs>0 else '.'}"),
                formatted_references,
            ],
            style={"max-height": "20rem", "overflow-y": "scroll"},
        )
