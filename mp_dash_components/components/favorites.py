import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from mp_dash_components.components.core import MPComponent, unicodeify_spacegroup
from mp_dash_components.helpers.layouts import *

from pymatgen.util.string import unicodeify

from typing import List
from collections import namedtuple

Favorite = namedtuple("Favorite", ["mpid", "formula", "spacegroup", "doi", "notes"])


sample_favorites = [
    Favorite(mpid="mp-13", formula="Fe", spacegroup="Im-3m", doi="", notes=""),
    Favorite(mpid="mp-5020", formula="BaTiO3", spacegroup="R3m", doi="", notes=""),
    Favorite(mpid="mp-804", formula="GaN", spacegroup="P63mc", doi="", notes=""),
]


class FavoritesComponent(MPComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _make_tags(self, favorites: List[Favorite]):

        return Field(
            [
                Control(
                    [
                        dcc.Link([Tag(
                            favorite.mpid,
                            tag_type="link",
                            tag_addon=f"{unicodeify(favorite.formula)} "
                            f"({unicodeify_spacegroup(favorite.spacegroup)})",
                            tag_addon_type="white",
                        )], href=favorite.mpid)
                    ],
                    style={"margin-bottom": "0.2rem"},
                )
                for favorite in favorites
            ],
            grouped_multiline=True,
            grouped=True,
        )

    @property
    def all_layouts(self):

        self.favorite_button = Button(
            [Icon(kind="heart", fill="r"), html.Span("Favorite")],
            kind="white",
            id=self.id("favorite-button"),
        )
        self.favorited_button = Button(
            [Icon(kind="heart", fill="s"), html.Span("Favorited")],
            kind="danger",
            id=self.id("favorite-button"),
        )
        favorite_button_container = html.Div(
            [self.favorite_button],
            id=self.id("favorite-button-container"),
            style={"display": "inline-block"},
        )

        favorite_materials = html.Div(
            self._make_tags(sample_favorites), id=self.id("favorite-materials")
        )

        return {
            "button": favorite_button_container,
            "favorite_materials": favorite_materials,
        }

    def _generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("favorite-button-container"), "children"),
            [Input(self.id("favorite-button"), "n_clicks")],
            [State(self.id("favorite-button"), "className")],
        )
        def toggle_style(n_clicks, className):
            # TODO: there may be a more graceful way of doing this
            # should define custom style for favorite)
            if n_clicks is None:
                raise PreventUpdate
            if "white" in className:
                return self.favorited_button
            else:
                return self.favorite_button
