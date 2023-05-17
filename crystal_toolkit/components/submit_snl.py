from __future__ import annotations

import os
from urllib import parse

import requests
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from mp_api.client import MPRester
from pymatgen.core import Structure
from pymatgen.util.provenance import StructureNL

from crystal_toolkit import __version__ as ct_version
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import (
    Button,
    MessageBody,
    MessageContainer,
    MessageHeader,
    dcc,
    html,
)

# ask Patrick phuck@lbl.gov
MP_CLIENT_KEY = os.getenv("MP_CLIENT_KEY")


class SubmitSNLPanel(PanelComponent):
    """This component is designed solely for use in the Materials Project infrastructure.

    It requires a component "url.search" in the app layout to work, from which a token will be
    extracted, and also requires a "SearchComponent_search_container" component.
    """

    def __init__(self, *args, url_id: str | None = None, **kwargs) -> None:
        self.url_id = url_id
        super().__init__(*args, **kwargs)

    @property
    def title(self) -> str:
        return "Submit to Materials Project"

    @property
    def description(self) -> str:
        return (
            "Help us complete our database by submitting your structure to "
            "MPComplete where we will add your structure to our calculation queue."
        )

    def contents_layout(self) -> html.Div:
        return html.Div(
            [
                dcc.Input(
                    placeholder="Write a comment about your structure (optional)",
                    id=self.id("comments"),
                    className="input",
                    maxLength=140,
                ),
                html.Div(id=self.id("info")),
                Button("Submit to Materials Project", id=self.id("submit")),
                html.Br(),
                html.Div(id=self.id("confirmation")),
            ]
        )

    def generate_callbacks(self, app, cache) -> None:
        super().generate_callbacks(app, cache)

        def parse_token(url):
            if not url:
                return None
            if url.startswith("?"):
                url = url[1:]
            return dict(parse.parse_qsl(url)).get("token")

        @cache.memoize(timeout=60 * 60 * 24)
        def get_token_response(token):
            url = "https://materialsproject.org/rest/v2/snl/get_user_info"
            payload = {"token": token, "client_key": MP_CLIENT_KEY}

            return requests.post(url, data=payload).json()["response"]

        @app.callback(
            Output(self.id("panel"), "style"),
            # for MP Crystal Toolkit app only, this is brittle(!)
            Output("SearchComponent_search_container", "style"),
            Input("url", "search"),
        )
        def hide_panel_if_no_token(url):
            token = parse_token(url)

            if not token:
                return {"display": "none"}, {}
            return {}, {}  # {"display": "none"}

        @app.callback(
            Output(self.id("info"), "children"),
            Input(self.id(), "data"),
            Input(self.id("comments"), "value"),
            Input(self.id("panel"), "open"),
            Input("url", "search"),
        )
        def generate_description(structure, comments, panel_open, url):
            token = parse_token(url)

            if not token:
                raise PreventUpdate

            contents = get_token_response(token)

            structure = self.from_data(structure)
            if type(structure) != Structure:
                raise PreventUpdate

            description = dcc.Markdown(
                f"""
> **Structure to upload:** {structure.composition.reduced_formula} ({len(structure)} sites)
> **Name:** {contents['first_name']} {contents['last_name']}
> **Email:** {contents['email']}
> **Comment:** {comments}

This information is stored so that we can give credit to you on the Materials
Project website and to say thank you for submitting the structure.
For more information, see the Materials Project
[privacy policy](https://materialsproject.org/terms).
"""
            )

            return html.Div([html.Br(), description, html.Br()])

        @app.callback(
            Output(self.id("confirmation"), "children"),
            Input(self.id("submit"), "n_clicks"),
            State(self.id(), "data"),
            State(self.id("comments"), "value"),
            State("url", "search"),
        )
        def submit_snl(n_clicks, structure, comments, url):
            if not n_clicks:
                raise PreventUpdate

            token = parse_token(url)
            if not token:
                raise PreventUpdate

            structure = self.from_data(structure)
            if type(structure) != Structure:
                message = (
                    f"Can only submit structures to Materials Project, "
                    f"not {type(structure)}"
                )
                return MessageContainer(message, kind="warning")

            if not MP_CLIENT_KEY:
                message = (
                    "Submission to MPComplete is currently disabled, "
                    "please check back soon or contact @mkhorton."
                )
                return MessageContainer(message, kind="warning")

            # check if structure already exists on MP

            with MPRester() as mpr:
                mp_ids = mpr.find_structure(structure)

            if mp_ids:
                message = (
                    f"Similar structures are already available on "
                    f"the Materials Project, see: {', '.join(mp_ids)}"
                )
                return MessageContainer(message, kind="warning")

            remarks = [
                f"Generated by Crystal Toolkit {ct_version} and "
                f"submitted with MPComplete"
            ]
            if comments:
                remarks.append(comments)

            contents = get_token_response(token)

            user_name = f"{contents['first_name']} {contents['last_name']}"
            user_email = contents["email"]
            user_api_key = contents["api_key"]

            snl = StructureNL(
                structure, [{"name": user_name, "email": user_email}], remarks=remarks
            )

            with MPRester(
                user_api_key, endpoint="https://www.materialsproject.org/rest/v1"
            ) as mpr:
                try:
                    submission_response = mpr.submit_snl(snl)
                except Exception as exc:
                    return MessageContainer(str(exc), kind="warning")

            header = f"Structure submission status: {submission_response[0]['status']}"
            message = submission_response[0]["details"]

            return MessageContainer(
                [MessageHeader(header), MessageBody(message)], kind="info"
            )
