import os

import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from monty.serialization import loadfn, dumpfn
from fuzzywuzzy import process
from pymatgen import MPRester
from pymatgen.core.composition import CompositionError

from mp_dash_components.components.core import MPComponent
from mp_dash_components import __file__ as module_path

from collections import defaultdict
from itertools import chain


class SearchComponent(MPComponent):

    def _get_tag_cache(self):

        path = os.path.join(os.path.dirname(module_path), "tag_cache.json")
        print(path)

        def _process_tag(tag):
            # remove information that is typically not helpful
            return tag.split(' (')[0]

        if os.path.isfile(path):
            tag_cache = loadfn(path)
        else:
            with MPRester() as mpr:
                entries = mpr.query({}, ['exp.tags', 'task_id',
                                      'e_above_hull', 'formula_pretty'],
                                 chunk_size=0, mp_decode=False)
            tags = [[(_process_tag(tag), entry)
                     for tag in entry['exp.tags']]
                    for entry in entries]
            tag_cache = defaultdict(list)
            for tag, entry in chain.from_iterable(tags):
                tag_cache[tag].append(entry)
            dumpfn(tag_cache, path)

        self.tag_cache = tag_cache
        self.tag_cache_keys = list(tag_cache.keys())

    #@self.caching()
    def search_tags(self, search_term):

        fuzzy_search_results = process.extract(search_term,
                                               self.tag_cache_keys, limit=5)

        tags = [item[0] for item in fuzzy_search_results]

        entries = [self.tag_cache[tag] for tag in tags]

        return list(chain.from_iterable(entries)), tags


    @property
    def layouts(self):

        search_field = dcc.Input(id=f"{self.id}_input")
        search_button = html.Button('Search', id=f"{self.id}_button")

        return {
            'search': html.Div([search_field, search_button]),
            'error': html.Div(id=f"{self.id}_error"),
            'store': self._store
        }

    @property
    def all_layouts(self):
        return html.Div([self.layouts['search'], self.layouts['store']])

    def _generate_callbacks(self, app):

        self._get_tag_cache()

        @app.callback(
            Output(self.store_id, "data"),
            [Input(f"{self.id}_input", "n_submit"),
             Input(f"{self.id}_button", "n_clicks")],
            [State(f"{self.id}_input", "value")]
        )
        def update_store(n_submit, n_clicks, search_term):

            if (n_submit is None) and (n_clicks is None):
                raise PreventUpdate

            if search_term.startswith('mpr-') or search_term.startswith('mvc-'):
                return search_term

            with MPRester() as mpr:
                try:
                    entries = mpr.query(search_term,
                                        ['task_id', 'formula_pretty',
                                         'e_above_hull'])
                except CompositionError:
                    entries = []

            if len(entries) == 0:
                entries = self.search_tags(search_term)

            if len(entries) == 0:
                raise PreventUpdate

            entries = sorted(entries, key=lambda x: x['e_above_hull'])

            for entry in entries:
                if entry['e_above_hull'] == 0:
                    entry['e_above_hull_human'] = "predicted stable"
                else:
                    entry['e_above_hull_human'] = "+{} eV/atom"

            human_readable_results = {
                entry['task_id']: "{} ({}) {}"
                for entry in entries
            }

            return entries[0]['task_id']

        def process_options(opts):

            ...
