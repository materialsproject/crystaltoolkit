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
from mp_dash_components.helpers.layouts import *
from mp_dash_components import __file__ as module_path

import numpy as np

from collections import defaultdict
from itertools import chain
from random import choice


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

    def _get_mpid_cache(self):

        path = os.path.join(os.path.dirname(module_path), "mpid_cache.json")

        if os.path.isfile(path):
            mpid_cache = loadfn(path)
        else:
            with MPRester() as mpr:
                entries = mpr.query({}, ["task_id"], chunk_size=0, mp_decode=False)
            mpid_cache = [entry["task_id"] for entry in entries]
            dumpfn(mpid_cache, path)

        self.mpid_cache = mpid_cache

    @MPComponent.cache.memoize(timeout=0)
    def search_tags(self, search_term):

        self.logger.info(f"Tag search: {search_term}")

        # TODO: this is slow, replace with something more sensible
        fuzzy_search_results = process.extract(
            search_term, self.tag_cache_keys, limit=5
        )

        score_cutoff = 80
        fuzzy_search_results = [
            result for result in fuzzy_search_results if result[1] >= score_cutoff
        ]

        tags = [item[0] for item in fuzzy_search_results]

        entries = [self.tag_cache[tag] for tag in tags]

        return list(chain.from_iterable(entries)), tags

    def _make_search_box(self, search_term=None):

        search_field = dcc.Input(
            id=self.id("input"),
            className="input",
            type="text",
            value=search_term,
            placeholder="Enter a formula or mp-id…",
        )
        search_button = Button(
            [Icon(kind="search"), html.Span(), "Search"],
            kind="primary",
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

        return search


    @property
    def all_layouts(self):

        search = html.Div(self._make_search_box(), id=self.id("search_container"))

        random_link = html.A(
            "or load random mp-id",
            className="is-text is-size-7",
            id=self.id("random"),
        )

        dropdown = dcc.Dropdown(id=self.id("dropdown"), clearable=False)
        dropdown = html.Div(
            [html.Label("Multiple results found, please select one:"), dropdown],
            id="dropdown-container",
            style={"display": "none"},
        )

        warning = html.Div(style={"display": "none"}, id=self.id("warning"))

        api_hint = MessageContainer(
            [
                MessageHeader(html.Div([Icon(kind="code"), "Retrieve with code"])),
                MessageBody(id=self.id("api_hint")),
            ],
            id=self.id("api_hint_container"),
            kind="info",
            size="small",
            style={"display": "none"},
        )

        search = html.Div([search, random_link], style={"margin-bottom": "0.75rem"})

        search = html.Div([search, warning, dropdown])

        return {"search": search, "api_hint": api_hint}

    @property
    def standard_layout(self):
        return html.Div([self.all_layouts["search"]])

    def _generate_callbacks(self, app):

        self._get_tag_cache()
        self._get_mpid_cache()

        @app.callback(
            Output(self.id("results"), "data"),
            [
                Input(self.id("input"), "n_submit_timestamp"),
                Input(self.id("button"), "n_clicks_timestamp"),
                #Input(self.id("random"), "n_clicks_timestamp"),
            ],
            [State(self.id("input"), "value")],
        )
        def update_results(n_submit, n_clicks, search_term):

            # TODO: we may want to automatically submit form when random button is pressed
            # figure out who's asking ... may be able to change this with later version of Dash
            #if (
            #    random_n_clicks
            #    and (not n_submit or random_n_clicks > n_submit)
            #    and (not n_clicks or random_n_clicks > n_clicks)
            #):
            #    return {choice(self.mpid_cache): "Randomly selected mp-id."}

            #if (n_submit is None) and (n_clicks is None) and (random_n_clicks is None):
            #    raise PreventUpdate

            if search_term is None:
                raise PreventUpdate

            self.logger.info(f"Search: {search_term}")

            # common confusables
            if search_term.isnumeric() and str(int(search_term)) == search_term:
                search_term = f"mp-{search_term}"
            if search_term.startswith("mp") and "-" not in search_term:
                search_term = f"mp-{search_term.split('mp')[1]}"

            if search_term.startswith("mp-") or search_term.startswith("mvc-"):
                return {search_term: search_term}  # no need to actually search

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
                self.logger.info(f"Search: no results for {search_term}")
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
            Output(self.id("dropdown-container"), "style"),
            [Input(self.id("results"), "data")],
        )
        def hide_show_dropdown(results):
            if len(results) <= 1:
                return {"display": "none"}
            else:
                return {}

        @app.callback(
            Output(self.id("warning"), "children"), [Input(self.id("results"), "data")]
        )
        def show_warning(results):
            if "error" in results:
                return MessageContainer(MessageBody(results["error"]))
            else:
                return html.Div()

        @app.callback(
            Output(self.id("search_container"), "children"),
            [Input(self.id("random"), "n_clicks")]
        )
        def update_displayed_mpid(random_n_clicks):
            # TODO: this is a really awkward solution to a complex callback chain, improve in future?
            # TODO: THIS IS BROKEN, WILL SELECT DIFFERENT RANDOM CHOICE (!)
            return self._make_search_box(search_term=choice(self.mpid_cache))

        @app.callback(Output(self.id(), "data"), [Input(self.id("dropdown"), "value")])
        def update_store_from_value(value):
            return {"time_requested": self.get_time(), "mpid": value}

        @app.callback(
            Output(self.id("api_hint_container"), "style"), [Input(self.id(), "data")]
        )
        def hide_show_dropdown(data):
            if data is None or "mpid" not in data:
                return {"display": "none"}
            else:
                return {}

        @app.callback(
            Output(self.id("api_hint"), "children"), [Input(self.id(), "data")]
        )
        def update_api_hint(data):
            if data is None or "mpid" not in data:
                raise PreventUpdate
            md = f"""You can retrieve this structure using the Materials Project API:


```
from pymatgen import MPRester
with MPRester() as mpr:
    struct = mpr.get_structure_by_mpid("{data["mpid"]}")
```


To get an API key and find out more visit [materialsproject.org](https://materialsproject.org/open).
"""

            return dcc.Markdown(md)
