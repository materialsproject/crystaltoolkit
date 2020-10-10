import os

import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from monty.serialization import loadfn, dumpfn
from pymatgen.core.composition import CompositionError
from pymatgen.util.string import unicodeify
from pymatgen.ext.matproj import MPRester


from pymatgen.util.string import unicodeify_spacegroup
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import *
from crystal_toolkit import __file__ as module_path

import numpy as np

from collections import defaultdict
from itertools import chain
from random import choice


class SearchComponent(MPComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_store("results")

    def _get_mpid_cache(self):

        path = os.path.join(os.path.dirname(module_path), "mpid_cache.json")

        if os.path.isfile(path):
            mpid_cache = loadfn(path)
        else:
            try:
                with MPRester() as mpr:
                    # restrict random mpids to those likely experimentally known
                    # and not too large
                    entries = mpr.query(
                        {"nsites": {"$lte": 16}},
                        ["task_id", "icsd_ids"],
                        chunk_size=0,
                        mp_decode=False,
                    )
                mpid_cache = [
                    entry["task_id"] for entry in entries if len(entry["icsd_ids"]) > 2
                ]
                dumpfn(mpid_cache, path)
            except Exception:
                mpid_cache = []

        self.mpid_cache = mpid_cache

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
        search = Field(
            [Control(search_field), Control(search_button)],
            addons=True,
            style={"marginBottom": "0"},
        )

        return html.Div(
            [html.Label("Search Materials Project:", className="mpc-label"), search]
        )

    @property
    def _sub_layouts(self):

        search = html.Div(self._make_search_box(), id=self.id("search_container"))

        random_link = html.A(
            "get random mp-id", className="is-text is-size-7", id=self.id("random")
        )

        dropdown = dcc.Dropdown(id=self.id("dropdown"), clearable=False)
        dropdown_container = html.Div(
            [html.Label("Multiple results found, please select one:"), dropdown],
            id=self.id("dropdown-container"),
            style={"display": "none"},
        )

        warning = html.Div(style={"display": "none"}, id=self.id("warning"))

        search = html.Div([search, random_link], style={"marginBottom": "0.75rem"})

        search = html.Div([search, warning, dropdown_container])

        return {"search": search}

    def layout(self):
        return html.Div([self._sub_layouts["search"]])

    def generate_callbacks(self, app, cache):

        self._get_mpid_cache()

        @cache.memoize(timeout=0)
        def get_human_readable_results_from_search_term(search_term):

            # common confusables
            if search_term.isnumeric() and str(int(search_term)) == search_term:
                search_term = f"mp-{search_term}"
            if search_term.startswith("mp") and "-" not in search_term:
                search_term = f"mp-{search_term.split('mp')[1]}"

            if search_term.startswith("mp-") or search_term.startswith("mvc-"):
                # no need to actually search, support multiple mp-ids (space separated)
                return {mpid: mpid for mpid in search_term.split(" ")}

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
                f"({unicodeify_spacegroup(entry['spacegroup.symbol'])}) "
                f"{entry['e_above_hull_human']}"
                for entry in entries
            }

            return human_readable_results

        @app.callback(
            Output(self.id("results"), "data"),
            [Input(self.id("input"), "n_submit"), Input(self.id("button"), "n_clicks")],
            [State(self.id("input"), "value")],
        )
        def update_results(n_submit, n_clicks, search_term):

            if not search_term:
                raise PreventUpdate

            self.logger.info(f"Search: {search_term}")

            results = get_human_readable_results_from_search_term(search_term)

            self.logger.debug(f"Search results: {results}")

            return results

        @app.callback(
            Output(self.id("dropdown"), "options"), [Input(self.id("results"), "data")]
        )
        def update_dropdown_options(results):
            if not results or "error" in results:
                raise PreventUpdate
            return [{"value": mpid, "label": label} for mpid, label in results.items()]

        @app.callback(
            Output(self.id("dropdown"), "value"), [Input(self.id("results"), "data")]
        )
        def update_dropdown_value(results):
            if not results or "error" in results:
                raise PreventUpdate
            return list(results.keys())[0]

        @app.callback(
            Output(self.id("dropdown-container"), "style"),
            [Input(self.id("results"), "data")],
        )
        def hide_show_dropdown(results):
            if not results or len(results) <= 1:
                return {"display": "none"}
            else:
                return {}

        @app.callback(
            Output(self.id("warning"), "children"), [Input(self.id("results"), "data")]
        )
        def show_warning(results):
            if results and "error" in results:
                return MessageContainer(MessageBody(results["error"]))
            else:
                return html.Div()

        @app.callback(
            Output(self.id("search_container"), "children"),
            [Input(self.id("random"), "n_clicks")],
        )
        def update_displayed_mpid(random_n_clicks):
            # TODO: this is a really awkward solution to a complex callback chain, improve in future?
            return self._make_search_box(search_term=choice(self.mpid_cache))

        @app.callback(Output(self.id(), "data"), [Input(self.id("dropdown"), "value")])
        def update_store_from_value(mpid):
            return mpid
