from __future__ import annotations

import logging
import re
from urllib.parse import urljoin

import dash
import dash_mp_components as mpc
import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from monty.serialization import loadfn
from pymatgen.util.string import unicodeify, unicodeify_spacegroup

import crystal_toolkit.components as ctc
import crystal_toolkit.helpers.layouts as ctl
from crystal_toolkit import MODULE_PATH
from crystal_toolkit.core.mpapp import MPApp
from crystal_toolkit.helpers.utils import (
    get_box_title,
    get_contribs_api_base_url,
    get_contribs_client,
    get_user_api_key,
)

logger = logging.getLogger(__name__)
_CATALYST_SEARCH_FILTER_GROUPS = loadfn(
    MODULE_PATH / "apps/examples/mpcontribs/catalysis_filter_groups.json"
)
_CATALYST_SEARCH_COLUMNS = loadfn(
    MODULE_PATH / "apps/examples/mpcontribs/catalysis_columns.json"
)

_ADSORBATE_CHOICES = (
    (MODULE_PATH / "apps/examples/mpcontribs/adsorbate_choices.txt")
    .read_text(encoding="utf-8")
    .splitlines()
)


class CatalysisApp(MPApp):
    @staticmethod
    def modify_df(dataframe: pd.DataFrame) -> list[pd.DataFrame]:
        """Filter DataFrame for unary+binary materials visualization.

        Args:
          dataframe (pd.DataFrame): the dataframe that you want to modify

        Returns:
            list[pd.Dataframe): two dataframes, the input df filtered to unary or binary materials
                and one with the minimum energy of each material
        """

        # Extract the elements and number of them from formula
        def grab_elements_and_number_of(formula):
            element_tup = tuple(np.sort(re.findall(r"([A-Z][a-z]*)", formula)))
            return element_tup, len(element_tup)

        dataframe["element_tup"], dataframe["number_elements"] = zip(
            *dataframe.formula.apply(grab_elements_and_number_of)
        )

        # Filter the df to only include unary, binary materials
        dataframe = dataframe[
            (dataframe["number_elements"] == 1) | (dataframe["number_elements"] == 2)
        ]

        # Create a df of minimum values
        min_E_df = dataframe.groupby(by=["element_tup"]).agg({"energy": "min"})
        min_E_df = min_E_df.reset_index()

        return [dataframe, min_E_df]

    @staticmethod
    def get_plot(
        df_all_data: pd.DataFrame,
        df_min_E: pd.DataFrame,
        target_E,
        range_E,
        user_options,
    ) -> go.Figure:
        """Generate a 2D plot for binary visualization.

        :param df_all_data:
        :param df_min_E:
        :param target_E:
        :param range_E:
        :param user_options: Not implemented.
        :return: 2D plot
        """
        # Create a list of unique elements for use as axis labels
        element_list = df_min_E.element_tup.tolist()
        flat_element_list = [item for sublist in element_list for item in sublist]
        labels = np.sort(np.unique(flat_element_list))

        def construct_grid(df, labels):
            grid_dim = len(labels)
            grid = np.zeros((grid_dim, grid_dim))
            custom_data = np.zeros((grid_dim, grid_dim), dtype=object)
            add_data = np.zeros((grid_dim, grid_dim), dtype=object)
            lookup_dict = df_min_E.set_index("element_tup").to_dict()
            el_combos = list(lookup_dict["energy"])
            for ii in range(len(labels)):
                for kk in range(len(labels)):
                    els_now = (
                        (labels[ii],)
                        if ii == kk
                        else tuple(np.sort([labels[ii], labels[kk]]))
                    )
                    if els_now in el_combos:
                        grid[ii, kk] = lookup_dict["energy"][els_now]
                        random_ids = df_all_data[
                            df_all_data["element_tup"] == els_now
                        ].identifier.tolist()
                        random_id_text = "<br>"
                        add_data_text = ""
                        for id in random_ids:
                            random_id_text = random_id_text + id + " <br> "
                            add_data_text = add_data_text + id + "-"
                        custom_data[ii, kk] = [len(random_ids), random_id_text]
                        add_data[ii, kk] = add_data_text
                    else:
                        grid[ii, kk] = np.nan
                        custom_data[ii, kk] = ["None", "None"]
                        add_data[ii, kk] = "None"
            return grid, custom_data, add_data

        grid, customdata, add_data = construct_grid(df_min_E, labels)
        fig = go.Figure(
            data=go.Heatmap(
                x=labels,
                y=labels,
                z=grid,
                customdata=customdata,
                text=add_data,
                hovertemplate="<b>number of calculations</b>: %{customdata[0]} <br><br><b> Open Catalyst Project IDs: "
                "</b> %{customdata[1]} <extra></extra>",
                colorscale=plotly.colors.cyclical.Twilight,
                zmin=float(target_E[0]) - float(range_E[0]),
                zmax=float(target_E[0]) + float(range_E[0]),
            )
        )

        fig.update_layout(autosize=True, width=1000, height=1000)
        # fig.update_yaxes(scaleanchor = "x", scaleratio = 1)
        fig.update_layout(transition_duration=500)

        return fig

    def get_catalysis_explorer(self) -> mpc.SearchUIContainer:
        """Get the Catalysis Explorer app."""
        return mpc.SearchUIContainer(
            [
                self.search_bar_container(
                    mpc.SearchUISearchBar(
                        placeholder="e.g. Al3Pt5 or mp-10025",
                        errorMessage='Please enter a valid bulk formula (e.g. "Ti5Ge4") or Material ID '
                        '(e.g. "mp-1501").',
                        periodicTableMode="none",
                        allowedInputTypesMap={
                            "formula": {"field": "data__bulkFormula__exact"},
                            "text": {"field": "data__mpid__exact"},
                        },
                        helpItems=[
                            {"label": "Search Examples"},
                            {
                                "label": "Has exact bulk formula",
                                "examples": ["Ni4W", "Ca5P8"],
                            },
                            {
                                "label": "Has Bulk Material ID",
                                "examples": ["mp-30811", "mp-10025"],
                            },
                            {
                                "label": "Additional search options available in the filters panel."
                            },
                        ],
                    )
                ),
                mpc.SearchUIGrid(),
            ],
            id="catalysis-explorer",
            resultLabel="catalyst",
            columns=_CATALYST_SEARCH_COLUMNS,
            filterGroups=_CATALYST_SEARCH_FILTER_GROUPS,
            apiEndpoint=urljoin(get_contribs_api_base_url(), "/contributions/"),
            apiEndpointParams={"project": "open_catalyst_project"},
            apiKey=get_user_api_key(),
            sortKey="_sort",
            totalKey="total_count",
            limitKey="_limit",
            skipKey="_skip",
            fieldsKey="_fields",
        )

    def generate_callbacks(self, app, cache) -> None:
        """Register callback functions for this component."""
        super().generate_callbacks(app, cache)

        @cache.memoize(timeout=60 * 60)
        def get_plot_data(smile: str) -> pd.DataFrame:
            client = get_contribs_client()
            contributions = client.query_contributions(
                query={
                    "project": "open_catalyst_project",
                    "data__adsorbateSmiles__exact": smile,
                },
                fields=["identifier", "data.bulkFormula", "data.adsorptionEnergy"],
                paginate=True,
            )
            records = [
                {
                    "formula": resp["data"]["bulkFormula"],
                    "identifier": resp["identifier"],
                    "energy": resp["data"]["adsorptionEnergy"]["value"],
                }
                for resp in contributions["data"]
            ]
            return pd.DataFrame(records)

        @app.callback(
            Output(self.id("heat_map"), "figure"),
            Input(self.get_kwarg_id("smiles"), "value"),
            Input(self.get_kwarg_id("targetE"), "value"),
            Input(self.get_kwarg_id("range_E"), "value"),
            Input(self.id("tabs"), "value"),
        )
        @cache.memoize(timeout=60 * 60 * 24)
        def update_figure(smile, mid_E, range_E, active_tab):
            # guard statement to ensure callback is not triggered unless viewing visualization
            if active_tab != "visualization":
                raise PreventUpdate

            smile = smile[0]
            df = get_plot_data(smile)
            df_full, df_min_E = self.modify_df(df)
            return self.get_plot(df_full, df_min_E, mid_E, range_E, 1)

        @app.callback(
            Output(self.id("display_table"), "children"),
            Input(self.id("heat_map"), "clickData"),
        )
        def display_click_data(clickData):
            if clickData is None:
                table = ctl.get_data_list(
                    {
                        "Elements": "None",
                        "Number of Calculations": "None",
                        "Calculations": "None",
                    }
                )
            else:
                el1 = str(clickData["points"][0]["x"])
                el2 = str(clickData["points"][0]["y"])
                el_combo = el1 if el1 == el2 else el1 + ", " + el2
                randids = clickData["points"][0]["text"].split("-")
                num_calcs = str(len(randids) - 1)
                table = ctl.get_data_list(
                    {
                        "Elements": el_combo,
                        "Number of Calculations": num_calcs,
                        "Calculations": [
                            html.Div(
                                dcc.Link(rand_id_now, href="/catalysis/" + rand_id_now)
                            )
                            for rand_id_now in randids
                        ],
                    }
                )
            return table

    def get_visualization(self, structure):
        # from the definition supplied by the Open Catalyst Project
        display_text_map = {
            0: "Fixed Surface Atoms",
            1: "Relaxed Surface Atoms",
            2: "Adsorbate",
        }
        structure.add_site_property(
            "display_text",
            [display_text_map[tag] for tag in structure.site_properties["tags"]],
        )

        return ctc.StructureMoleculeComponent(
            structure,
            disable_callbacks=True,
            bonding_strategy="CutOffDictNN",
            radius_strategy="covalent",
            show_compass=False,
            show_settings=False,
            show_image_button=False,
            show_export_button=False
            # group_by_site_property="display_text",  # pending new Crystal Toolkit release
        ).layout()

    def get_layout(self, payload=None):
        return dcc.Tabs(
            [
                dcc.Tab(
                    children=[html.Br(), self.get_search_layout(payload=payload)],
                    label="Search",
                    id=self.id("search-tab"),
                    value="search",
                ),
                dcc.Tab(
                    children=[
                        html.Br(),
                        self.get_visualization_layout(payload=payload),
                    ],
                    label="Binary Visualization",
                    id=self.id("vis-tab"),
                    value="visualization",
                ),
            ],
            value="search",
            id=self.id("tabs"),
        )

    def get_visualization_layout(self, payload=None):
        state = {"smiles": "*C", "targetE": 0.2, "range_E": 1}
        smiles_input = self.get_choice_input(
            kwarg_label="smiles",
            label="SMILES",
            help_str="Choose an adsorbate to display by its SMILES string.",
            state=state,
            options=[{"label": s, "value": s} for s in _ADSORBATE_CHOICES],
            style={"width": "8rem"},
        )

        E_input = self.get_slider_input(
            kwarg_label="targetE",
            label="Target adsorption enthalpy (eV)",
            help_str="Choose an adsorption enthalpy to set as the midpoint.",
            state=state,
            domain=[0, 3],
            step=0.2,
        )

        range_input = self.get_slider_input(
            kwarg_label="range_E",
            label="Color scale range (eV)",
            help_str="Choose a value to be used as the maximum and minimum value in the color scale.",
            state=state,
            domain=[0, 3],
            step=0.2,
        )
        additional_data = get_box_title(
            use_point="CatalysisApp",
            title="catapp-add-data",
        )

        description = (
            "Explore binary materials in the catalysis dataset. Click on a point in the graph "
            "for more information about the materials associated with that point."
        )

        controls = html.Div(
            [description, html.Br(), html.Br(), smiles_input, E_input, range_input]
        )

        return html.Div(
            ctl.Columns(
                [
                    ctl.Column(
                        children=[
                            ctl.Columns([ctl.Column(controls)]),
                            ctl.Columns(
                                [
                                    ctl.Column(
                                        children=[
                                            ctl.Box(
                                                ctl.Loading(
                                                    dcc.Graph(id=self.id("heat_map"))
                                                ),
                                                style={"min-width": "1000px"},
                                            ),
                                        ]
                                    ),
                                    ctl.Column(
                                        children=[
                                            ctl.Loading(
                                                ctl.Box(
                                                    [
                                                        additional_data,
                                                        html.Div(
                                                            id=self.id("display_table")
                                                        ),
                                                    ],
                                                    className="mp-data-list",
                                                )
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            )
        )

    def get_search_layout(self, payload=None):
        if not payload:
            return self.get_catalysis_explorer()

        client = get_contribs_client()

        # Fetch contribution-level data
        contributions_resp = client.query_contributions(
            query={"project": "open_catalyst_project", "identifier": payload},
            fields=["id", "identifier", "project", "formula", "data", "structures"],
        )

        if not contributions_resp["data"]:
            logger.error(f"Failed to load contribution for {payload}")
            raise PreventUpdate

        # TODO: can we assume there will always be one result?
        contribution = contributions_resp["data"][0]

        try:
            structure = client.get_structure(contribution["structures"][0]["id"])
        except Exception as ex:
            logger.error(ex)
            raise PreventUpdate from ex

        bulk_formula = contribution["data"]["bulkFormula"]
        adsorbate_smiles = contribution["data"]["adsorbateSmiles"]

        contribution_data = {
            "Bulk Formula": unicodeify(contribution["data"]["bulkFormula"]),
            "Surface Formula": unicodeify(contribution["formula"]),
            "Surface Material ID": dcc.Link(
                contribution["data"]["mpid"],
                href=f'/materials/{contribution["data"]["mpid"]}',
            ),
            "Adsorbate SMILES": adsorbate_smiles,
            "Adsorbate IUPAC Formula": contribution["data"]["adsorbateIUPACFormula"],
            "Adsorption Energy": contribution["data"]["adsorptionEnergy"]["value"],
            "Miller Index": unicodeify_spacegroup(
                f'({int(contribution["data"]["h"]["value"])} '
                f'{int(contribution["data"]["k"]["value"])} '
                f'{int(contribution["data"]["l"]["value"])})'
            ),
            "Surface Shift": contribution["data"]["surfaceShift"]["value"],
        }

        how_to_cite = ctl.MessageContainer(
            [
                ctl.MessageHeader("How to Cite"),
                ctl.MessageBody(
                    dcc.Markdown(
                        "This dataset is provided by the [Open Catalyst Project](https://opencatalystproject.org). "
                        "Please cite the appropriate publications if this data is useful for your work."
                    )
                ),
            ],
            kind="info",
        )

        return ctl.Container(
            [
                ctl.H2(f"{unicodeify(adsorbate_smiles)} on {unicodeify(bulk_formula)}"),
                ctl.H4(f"OCP ID: {payload}", subtitle=True),
                ctl.Columns(
                    [
                        ctl.Column(
                            [
                                ctl.Box([ctl.get_data_list(contribution_data)]),
                                how_to_cite,
                            ],
                            className="is-6",
                        ),
                        ctl.Column(self.get_visualization(structure), narrow=True),
                    ]
                ),
            ],
            className="content",
        )


if __name__ == "__main__":
    # for development purposes, to run just this component
    app = dash.Dash(assets_folder="../../assets")
    section = CatalysisApp()
    # edit payload here to run for a specific OCP id, e.g. payload="random1222473"
    layout = ctl.Section([section.get_layout(payload=None)])
    ctc.register_crystal_toolkit(app=app, layout=layout, cache=None)
    app.run(debug=True, port=8050)
