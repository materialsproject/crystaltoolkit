from __future__ import annotations

import os
from random import choice

import numpy as np
from dash import dcc, html
from dash.dependencies import Component, Input, Output, State
from dash.exceptions import PreventUpdate
from monty.serialization import loadfn
from mp_api.client import MPRester, MPRestError
from pymatgen.util.string import unicodeify, unicodeify_spacegroup

from crystal_toolkit import __file__ as module_path
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import (
    Button,
    Control,
    Field,
    Icon,
    MessageBody,
    MessageContainer,
)


class SearchComponent(MPComponent):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.create_store("results")

    def _get_mpid_cache(self):
        path = os.path.join(os.path.dirname(module_path), "mpid_cache.json")

        mpid_cache = loadfn(path) if os.path.isfile(path) else []
        # else:
        #     try:
        #         with MPRester() as mpr:
        #             # restrict random mpids to those likely experimentally known
        #             # and not too large
        #             entries = mpr.query(
        #                 {"nsites": {"$lte": 16}},
        #                 ["task_id", "icsd_ids"],
        #                 chunk_size=0,
        #                 mp_decode=False,
        #             )
        #         mpid_cache = [
        #             entry["task_id"] for entry in entries if len(entry["icsd_ids"]) > 2
        #         ]
        #         dumpfn(mpid_cache, path)
        #     except Exception:
        #         mpid_cache = []

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
    def _sub_layouts(self) -> dict[str, Component]:
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

    def layout(self) -> html.Div:
        """Get the component layout."""
        return html.Div([self._sub_layouts["search"]])

    def generate_callbacks(self, app, cache) -> None:
        self._get_mpid_cache()

        @cache.memoize(timeout=0)
        def get_human_readable_results_from_search_term(search_term):
            # common confusables
            if search_term.isnumeric() and str(int(search_term)) == search_term:
                search_term = f"mp-{search_term}"
            if search_term.startswith("mp") and "-" not in search_term:
                search_term = f"mp-{search_term.split('mp')[1]}"

            if search_term.startswith(("mp-", "mvc-")):
                # no need to actually search, support multiple mp-ids (space separated)
                return {mpid: mpid for mpid in search_term.split(" ")}

            fields = ["material_id", "formula_pretty", "energy_above_hull", "symmetry"]
            with MPRester() as mpr:
                try:
                    entries = mpr.summary.search_summary_docs(
                        formula=search_term, fields=fields
                    )
                except MPRestError:
                    entries = []

            if len(entries) == 0:
                self.logger.info(f"Search: no results for {search_term}")
                return {"error": f"No results found for {search_term}."}

            entries = sorted(entries, key=lambda x: x.energy_above_hull)

            human_readable_hull_labels = []
            for entry in entries:
                e_hull = entry.energy_above_hull
                if e_hull == 0:
                    human_readable_hull_labels.append("predicted stable phase")
                elif e_hull >= 0.01:
                    human_readable_hull_labels.append(f"+{e_hull:.2f} eV/atom")
                else:
                    e_hull_str = np.format_float_scientific(e_hull, precision=2)
                    human_readable_hull_labels.append(f"+{e_hull_str} eV/atom")

            return {
                entry.material_id: f"{unicodeify(entry.formula_pretty)} "
                f"({unicodeify_spacegroup(entry.symmetry.symbol)}) "
                f"{human_readable_hull_label}"
                for entry, human_readable_hull_label in zip(
                    entries, human_readable_hull_labels
                )
            }

        @app.callback(
            Output(self.id("results"), "data"),
            Input(self.id("input"), "n_submit"),
            Input(self.id("button"), "n_clicks"),
            State(self.id("input"), "value"),
        )
        def update_results(n_submit, n_clicks, search_term):
            if not search_term:
                raise PreventUpdate

            self.logger.info(f"Search: {search_term}")

            results = get_human_readable_results_from_search_term(search_term)

            self.logger.debug(f"Search results: {results}")

            return results

        @app.callback(
            Output(self.id("dropdown"), "options"), Input(self.id("results"), "data")
        )
        def update_dropdown_options(results):
            if not results or "error" in results:
                raise PreventUpdate
            return [{"value": mpid, "label": label} for mpid, label in results.items()]

        @app.callback(
            Output(self.id("dropdown"), "value"), Input(self.id("results"), "data")
        )
        def update_dropdown_value(results):
            if not results or "error" in results:
                raise PreventUpdate
            return list(results)[0]

        @app.callback(
            Output(self.id("dropdown-container"), "style"),
            Input(self.id("results"), "data"),
        )
        def hide_show_dropdown(results):
            if not results or len(results) <= 1:
                return {"display": "none"}
            return {}

        @app.callback(
            Output(self.id("warning"), "children"), Input(self.id("results"), "data")
        )
        def show_warning(results):
            if results and "error" in results:
                return MessageContainer(MessageBody(results["error"]))
            return html.Div()

        @app.callback(
            Output(self.id("search_container"), "children"),
            Input(self.id("random"), "n_clicks"),
        )
        def update_displayed_mpid(n_clicks):
            # TODO: this is a really awkward solution to a complex callback chain, improve in future?
            return self._make_search_box(search_term=choice(self.mpid_cache))

        @app.callback(Output(self.id(), "data"), Input(self.id("dropdown"), "value"))
        def update_store_from_value(mpid):
            return mpid
