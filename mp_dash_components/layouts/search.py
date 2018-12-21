import os

import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from monty.serialization import loadfn, dumpfn
from fuzzywuzzy import process
from pymatgen import MPRester
from pymatgen.core.composition import CompositionError

from mp_dash_components.layouts.core import MPComponent
from mp_dash_components import __file__ as module_path

from collections import defaultdict
from itertools import chain

class SearchComponent(MPComponent):

    def _get_tag_cache(self):

        path = os.path.join(os.path.dirname(module_path), "tag_cache.json")
        print(path)

        if os.path.isfile(path):
            tag_cache = loadfn(path)
        else:
            with MPRester() as mpr:
                docs = mpr.query({}, ['exp.tags', 'task_id'],
                                 chunk_size=0, mp_decode=False)
            tags = [[(tag.split(' (')[0], doc['task_id'])
                     for tag in doc['exp.tags']]
                    for doc in docs]
            tag_cache = defaultdict(list)
            for tag, task_id in chain.from_iterable(tags):
                tag_cache[tag].append(task_id)
            dumpfn(tag_cache, path)

        self.tag_cache = tag_cache
        self.tag_cache_keys = list(tag_cache.keys())

    def search_tags(self, search_term):

        results = [item[0] for item in
                   process.extract(search_term, self.tag_cache_keys, limit=5)]

        mpids = [self.tag_cache[result] for result in results]

        return list(chain.from_iterable(mpids))


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

            with MPRester() as mpr:
                try:
                    results = mpr.query(search_term,
                                        ['task_id', 'formula_pretty',
                                         'e_above_hull'])
                except CompositionError:
                    results = []

            if len(results) == 0:
                mpids = self.search_tags(search_term)
                with MPRester() as mpr:
                    results = mpr.query({'task_id': {'$in': mpids}},
                                        ['task_id', 'formula_pretty',
                                         'e_above_hull'])

            if len(results) == 0:
                raise PreventUpdate

            results = sorted(results, key=lambda x: x['e_above_hull'])

            return results[0]['task_id']
