import os

import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from monty.serialization import loadfn, dumpfn
from fuzzywuzzy import process
from pymatgen import MPRester
from pymatgen.core.composition import CompositionError
from pymatgen.util.string import unicodeify, latexify_spacegroup

from mp_dash_components.components.core import MPComponent
from mp_dash_components.helpers.layouts import Button, Icon, Warning
from mp_dash_components import __file__ as module_path

import numpy as np

from collections import defaultdict
from itertools import chain


class SearchComponent(MPComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_store("results")

    @staticmethod
    @MPComponent.cache.memoize()
    def _unicodeify_spacegroup(spacegroup_symbol):
        # TODO: move this to pymatgen

        subscript_unicode_map = {
            0: "₀",
            1: "₁",
            2: "₂",
            3: "₃",
            4: "₄",
            5: "₅",
            6: "₆",
            7: "₇",
            8: "₈",
            9: "₉",
        }

        symbol = latexify_spacegroup(spacegroup_symbol)

        for number, unicode_number in subscript_unicode_map.items():
            symbol = symbol.replace("$_{" + str(number) + "}$", unicode_number)

        overline = "\u0305"  # u"\u0304" (macron) is also an option

        symbol = symbol.replace("$\\overline{", overline)
        symbol = symbol.replace("$", "")
        symbol = symbol.replace("{", "")
        symbol = symbol.replace("}", "")

        return symbol

    def _get_tag_cache(self):

        path = os.path.join(os.path.dirname(module_path), "tag_cache.json")

        def _process_tag(tag):
            # remove information that is typically not helpful
            return tag.split(" (")[0]

        if os.path.isfile(path):
            tag_cache = loadfn(path)
        else:
            with MPRester() as mpr:
                entries = mpr.query(
                    {},
                    [
                        "exp.tags",
                        "task_id",
                        "e_above_hull",
                        "pretty_formula",
                        "spacegroup.symbol",
                    ],
                    chunk_size=0,
                    mp_decode=False,
                )
            tags = [
                [(_process_tag(tag), entry) for tag in entry["exp.tags"]]
                for entry in entries
            ]
            tag_cache = defaultdict(list)
            for tag, entry in chain.from_iterable(tags):
                tag_cache[tag].append(entry)
            dumpfn(tag_cache, path)

        self.tag_cache = tag_cache
        self.tag_cache_keys = list(tag_cache.keys())

    @MPComponent.cache.memoize(timeout=0)
    def search_tags(self, search_term):

        fuzzy_search_results = process.extract(
            search_term, self.tag_cache_keys, limit=5
        )

        print(fuzzy_search_results)
        score_cutoff = 80
        fuzzy_search_results = [
            result for result in fuzzy_search_results if result[1] >= score_cutoff
        ]

        tags = [item[0] for item in fuzzy_search_results]

        entries = [self.tag_cache[tag] for tag in tags]

        return list(chain.from_iterable(entries)), tags

    @property
    def all_layouts(self):

        search_field = dcc.Input(
            id=self.id("input"),
            className="input",
            type="text",
            placeholder="Enter a formula or mp-id…",
        )
        search_button = Button(
            [Icon(kind="search"), html.Span(), "Search"],
            button_kind="primary",
            id=self.id("button"),
        )
        search = html.Div(
            [
                html.Div(search_field, className="control"),
                html.Div(search_button, className="control"),
            ],
            className="field has-addons",
            style={"margin-bottom": "0"},
        )

        random_link = dcc.Link("or load random material", className="is-size-7")

        dropdown = dcc.Dropdown(
            id=self.id("dropdown"), clearable=False, style={"display": "none"}
        )

        warning = Warning(
            size="small", style={"display": "none"}, id=self.id("warning")
        )

        search = html.Div([search, random_link], style={"margin-bottom": "0.75rem"})

        search = html.Div([search, warning, dropdown])

        return {"search": search}

    @property
    def standard_layout(self):
        return html.Div([self.all_layouts["search"]])

    def _generate_callbacks(self, app):

        self._get_tag_cache()

        @app.callback(
            Output(self.id("results"), "data"),
            [Input(self.id("input"), "n_submit"), Input(self.id("button"), "n_clicks")],
            [State(self.id("input"), "value")],
        )
        def update_results(n_submit, n_clicks, search_term):

            if (n_submit is None) and (n_clicks is None):
                raise PreventUpdate

            if search_term.startswith("mpr-") or search_term.startswith("mvc-"):
                return search_term

            # common confusables
            if str(int(search_term)) == search_term:
                search_term = f"mp-{search_term}"
            if search_term.startswith("mp") and "-" not in search_term:
                search_term = f"mp-{search_term.split('mp')[1]}"

            with MPRester() as mpr:
                try:
                    entries = mpr.query(
                        search_term,
                        [
                            "task_id",
                            "pretty_formula",
                            "e_above_hull",
                            "spacegroup.symbol",
                        ],
                    )
                except CompositionError:
                    entries = []

            mpids, tags = None, None
            if len(entries) == 0 and not (
                search_term.startswith("mp-") or search_term.startswith("mvc-")
            ):
                mpids, tags = self.search_tags(search_term)
                entries = mpr.query(
                    {"task_id": {"$in": mpids}},
                    ["task_id", "pretty_formula", "e_above_hull", "spacegroup.symbol"],
                )

            if len(entries) == 0:
                return {"error": f"No results found for {search_term}."}

            # sort by e_above_hull if a normal query, or by Levenshtein distance
            # if fuzzy matching (order of mpids list if present matches Levenshtein distance)
            if not mpids:
                entries = sorted(entries, key=lambda x: x["e_above_hull"])
            else:
                entries = sorted(entries, key=lambda x: mpids.index(x["task_id"]))

            for entry in entries:
                e_hull = entry["e_above_hull"]
                if e_hull == 0:
                    entry["e_above_hull_human"] = "predicted stable phase"
                elif e_hull >= 0.01:
                    entry["e_above_hull_human"] = f"+{e_hull:.2f} eV/atom"
                else:
                    e_hull_str = np.format_float_scientific(e_hull, precision=2)
                    entry["e_above_hull_human"] = f"+{e_hull_str} eV/atom"

            human_readable_results = {
                entry["task_id"]: f"{unicodeify(entry['pretty_formula'])} "
                f"({self._unicodeify_spacegroup(entry['spacegroup.symbol'])}) "
                f"{entry['e_above_hull_human']}"
                for entry in entries
            }

            return human_readable_results

        @app.callback(
            Output(self.id("dropdown"), "options"), [Input(self.id("results"), "data")]
        )
        def update_dropdown_options(results):
            if "error" in results:
                raise PreventUpdate
            return [{"value": mpid, "label": label} for mpid, label in results.items()]

        @app.callback(
            Output(self.id("dropdown"), "value"), [Input(self.id("results"), "data")]
        )
        def update_dropdown_value(results):
            if "error" in results:
                raise PreventUpdate
            return list(results.keys())[0]

        @app.callback(
            Output(self.id("dropdown"), "style"), [Input(self.id("results"), "data")]
        )
        def hide_show_dropdown(results):
            if len(results) <= 1:
                return {"display": "none"}
            else:
                return {}

        @app.callback(
            Output(self.id("warning"), "style"), [Input(self.id("results"), "data")]
        )
        def hide_show_warning(results):
            if "error" in results:
                return {}
            else:
                return {"display": "none"}

        @app.callback(
            Output(self.id("warning"), "children"), [Input(self.id("results"), "data")]
        )
        def hide_show_warning(results):
            return results.get("error", "")

        @app.callback(Output(self.id(), "data"), [Input(self.id("dropdown"), "value")])
        def update_store_from_value(value):
            return {"time_requested": self.get_time(), "mpid": value}
