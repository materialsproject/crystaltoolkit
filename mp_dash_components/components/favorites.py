import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from mp_dash_components.components.core import MPComponent, unicodeify_spacegroup
from mp_dash_components.helpers.layouts import *

from pymatgen.util.string import unicodeify

from typing import List, Dict
from collections import namedtuple

from toml import dumps

Favorite = namedtuple("Favorite", ["mpid", "formula", "spacegroup", "notes"])


sample_favorites = [
    Favorite(mpid="mp-13", formula="Fe", spacegroup="Im-3m", notes=""),
    Favorite(mpid="mp-5020", formula="BaTiO3", spacegroup="R3m", notes=""),
    Favorite(mpid="mp-804", formula="GaN", spacegroup="P63mc", notes=""),
]


class FavoritesComponent(MPComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_toml(self, favorites: List[Favorite]):

        save_format = {
            f.mpid: {
                "Formula": f.formula,
                "Spacegroup": f.spacegroup,
                "Notes": f.notes,
            }
            for f in favorites
        }

        header = "# Crystal Toolkit Favorites File\n\n"

        return header + dumps(save_format)

    def _make_links(self, favorites: List[Favorite]):

        return Field(
            [
                Control(
                    [
                        dcc.Link(
                            [
                                f"{unicodeify(favorite.formula)} "
                                f"({unicodeify_spacegroup(favorite.spacegroup)})"
                            ],
                            href=favorite.mpid,
                        )
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

        favorite_materials = Reveal(
            [self._make_links(sample_favorites)],
            title=H6("Favorited Materials", style={"display": "inline-block", "vertical-align": "middle"}),
            id=self.id("favorite-materials"),
            open=True
        )

        # TODO: add when Dash supports text areas!
        notes_layout = Reveal([Field(
            [
                Control(
                    dcc.Textarea(
                        id=self.id("favorite-notes"),
                        className="textarea",
                        rows=6,
                        style={"height": "100%", "width": "100%"},
                        placeholder="Enter your notes on the current material here"
                    )
                ),
                html.P(
                    [
                        dcc.Markdown(
                            "Favorites and notes are saved in your web browser "
                            "and not associated with your Materials Project account or stored on our servers. "
                            "If you want a permanent copy, [click here to download all of your notes]()."
                        )
                    ],
                    className="help",
                ),
            ]
        )], title="Notes")

        return {
            "button": favorite_button_container,
            "favorite_materials": favorite_materials,
            "notes": notes_layout
        }

    def _generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("favorite-button-container"), "children"),
            [Input(self.id("favorite-button"), "n_clicks")],
            [State(self.id("favorite-button"), "className")],
        )
        def toggle_style(n_clicks, className):
            """
            Switches the style of the favorites button when it's clicked.
            """
            # TODO: there may be a more graceful way of doing this
            # should define custom style for favorite)
            if n_clicks is None:
                raise PreventUpdate
            if "white" in className:
                return self.favorited_button
            else:
                return self.favorite_button

        @app.callback(
            Output(self.id("favorite-button"), "n_clicks"),
            [Input(self.id("favorite-notes"), "value")],
            [State(self.id("favorite-button"), "className"),
             State(self.id("favorite-button"), "n_clicks")]
        )
        def auto_favorite(note_contents, className, n_clicks):
            """
            Automatically favorites material when notes are added.
            """
            # TODO: there may be a more graceful way of doing this
            # should define custom style for favorite)
            if note_contents is None:
                raise PreventUpdate
            if len(note_contents) and "white" in className:
                return 1 if n_clicks is None else n_clicks+1
            else:
                return n_clicks


        def update_store(note_contents, favorite_click, current_mpid, data):


            if current_mpid not in data:
                data[current_mpid] = Favorite


        def update_links_list():
            ...
