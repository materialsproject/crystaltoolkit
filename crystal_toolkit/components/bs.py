import numpy as np
import numpy as np
import plotly.graph_objs as go
import plotly.subplots as tls
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from pymatgen.core.periodic_table import Element
from pymatgen.electronic_structure.bandstructure import BandStructureSymmLine as BSML
from pymatgen.electronic_structure.core import Spin
from pymatgen.electronic_structure.dos import CompleteDos
from pymatgen.electronic_structure.plotter import BSPlotter

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import *


# from pymongo import MongoClient


# Author: Jason Munro
# Contact: jmunro@lbl.gov


class BandstructureAndDosComponent(MPComponent):
    def __init__(
        self,
        mpid=None,
        bandstructure_symm_line=None,
        density_of_states=None,
        id=None,
        **kwargs,
    ):

        super().__init__(id=id, default_data=mpid, **kwargs)

        self.create_store("mpid", initial_data=mpid)
        self.create_store("traces")
        self.create_store(
            "bandstructure_symm_line", initial_data=bandstructure_symm_line
        )
        self.create_store("density_of_states", initial_data=density_of_states)
        self.create_store("elements")

    empty_plot_style = {
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
    }

    @property
    def _sub_layouts(self):

        # Main plot
        graph = Loading(
            [
                dcc.Graph(
                    figure=go.Figure(
                        layout=BandstructureAndDosComponent.empty_plot_style
                    ),
                    config={"displayModeBar": False},
                    responsive=True,
                )
            ],
            id=self.id("bsdos-div"),
        )

        # Convention selection for band structure
        convention = html.Div(
            [
                html.P("Path Convention"),
                dcc.Dropdown(
                    id=self.id("path-convention"),
                    options=[
                        {"label": "Setyawan-Curtarolo", "value": "sc"},
                        {"label": "Latimer-Munro", "value": "lm"},
                        {"label": "Hinuma et al.", "value": "hin"},
                    ],
                    value="sc",
                    clearable=False,
                ),
            ],
            style={"max-width": "200"},
            id=self.id("path-container"),
        )

        # Equivalent labels across band structure conventions
        label_select = html.Div(
            [
                html.P("Label Type"),
                dcc.RadioItems(
                    id=self.id("label-select"),
                    options=[
                        {
                            "label": "Setyawan-Curtarolo",
                            "value": "sc",
                            "disabled": False,
                        },
                        {"label": "Latimer-Munro", "value": "lm", "disabled": False},
                        {"label": "Hinuma et al.", "value": "hin", "disabled": False},
                    ],
                    value="",
                ),
            ],
            style={"max-width": "200"},
            id=self.id("label-container"),
        )

        # Density of states data selection
        dos_select = html.Div(
            [
                html.P("Density of States Data"),
                dcc.Dropdown(
                    id=self.id("dos-select"),
                    options=[{"label": "Atom Projected", "value": "ap"}],
                    value="ap",
                    clearable=False,
                ),
            ],
            style={"max-width": "200"},
        )

        return {
            "graph": graph,
            "convention": convention,
            "dos-select": dos_select,
            "label-select": label_select,
        }

    def layout(self):
        return html.Div(
            [
                Column([self._sub_layouts["convention"]], size=2),
                Column([self._sub_layouts["dos-select"]], size=2),
                Column([self._sub_layouts["label-select"]], size=2),
                Column([self._sub_layouts["graph"]], size=8),
            ]
        )

    def generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("bsdos-div"), "children"), [Input(self.id("traces"), "data")]
        )
        def update_graph(traces):

            if traces == "error":
                search_error = (
                    MessageContainer(
                        [
                            MessageBody(
                                dcc.Markdown(
                                    "Band structure and density of states not available for this selection."
                                )
                            )
                        ],
                        kind="warning",
                    ),
                )
                return search_error

            if traces is None:
                raise PreventUpdate

            figure = tls.make_subplots(
                rows=1, cols=2, shared_yaxes=True, print_grid=False
            )

            bstraces, dostraces, bs_data = traces

            # -- Add trace data to plots
            for bstrace in bstraces:
                figure.add_trace(bstrace, 1, 1)

            for dostrace in dostraces:
                figure.add_trace(dostrace, 1, 2)

            xaxis_style = go.layout.XAxis(
                title=dict(text="Wave Vector", font=dict(size=16)),
                tickmode="array",
                tickvals=bs_data["ticks"]["distance"],
                ticktext=bs_data["ticks"]["label"],
                tickfont=dict(size=16),
                ticks="inside",
                tickwidth=2,
                showgrid=True,
                showline=True,
                linewidth=2,
                mirror=True,
            )

            yaxis_style = go.layout.YAxis(
                title=dict(text="E-Efermi (eV)", font=dict(size=16)),
                tickfont=dict(size=16),
                showgrid=True,
                showline=True,
                zeroline=True,
                mirror="ticks",
                ticks="inside",
                linewidth=2,
                tickwidth=2,
                zerolinewidth=2,
                range=[-5, 9],
            )

            xaxis_style_dos = go.layout.XAxis(
                title=dict(text="Density of States", font=dict(size=16)),
                tickfont=dict(size=16),
                showgrid=True,
                showline=True,
                mirror=True,
                ticks="inside",
                linewidth=2,
                tickwidth=2,
            )

            yaxis_style_dos = go.layout.YAxis(
                tickfont=dict(size=16),
                showgrid=True,
                showline=True,
                zeroline=True,
                mirror="ticks",
                ticks="inside",
                linewidth=2,
                tickwidth=2,
                zerolinewidth=2,
                range=[-5, 9],
            )

            layout = go.Layout(
                title="",
                xaxis1=xaxis_style,
                xaxis2=xaxis_style_dos,
                yaxis=yaxis_style,
                yaxis2=yaxis_style_dos,
                showlegend=True,
                height=500,
                width=1500,
                hovermode="x",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=60, b=50, t=50, pad=0, r=30),
            )

            figure["layout"].update(layout)

            legend = go.layout.Legend(
                x=1.01,
                y=1.0,
                xanchor="left",
                yanchor="top",
                bordercolor="#333",
                borderwidth=1,
                traceorder="normal",
            )

            figure["layout"]["legend"] = legend

            figure["layout"]["xaxis1"]["domain"] = [0.0, 0.6]
            figure["layout"]["xaxis2"]["domain"] = [0.65, 1.0]

            return [
                dcc.Graph(
                    figure=figure, config={"displayModeBar": False}, responsive=True
                )
            ]

        @app.callback(
            [
                Output(self.id("label-select"), "options"),
                Output(self.id("label-select"), "value"),
                Output(self.id("label-container"), "style"),
            ],
            [
                Input(self.id("mpid"), "data"),
                Input(self.id("path-convention"), "value"),
            ],
        )
        def update_label_select(mpid, path_convention):
            if not mpid or "mpid" not in mpid:

                label_options = [{"label": "N/A", "value": ""}]
                label_value = ""
                label_style = {"max-width": "200", "display": "none"}

                return [label_options, label_value, label_style]
            else:

                label_options = [
                    {
                        "label": "Setyawan-Curtarolo",
                        "value": "sc",
                        "disabled": not (
                            path_convention == "lm" or path_convention == "sc"
                        ),
                    },
                    {
                        "label": "Latimer-Munro",
                        "value": "lm",
                        "disabled": not (path_convention == "lm"),
                    },
                    {
                        "label": "Hinuma et al.",
                        "value": "hin",
                        "disabled": not (
                            path_convention == "lm" or path_convention == "hin"
                        ),
                    },
                ]

                label_value = path_convention
                label_style = {"max-width": "200"}

                return [label_options, label_value, label_style]

        @app.callback(
            [
                Output(self.id("dos-select"), "options"),
                Output(self.id("path-convention"), "options"),
                Output(self.id("path-container"), "style"),
            ],
            [Input(self.id("elements"), "data"), Input(self.id("mpid"), "data")],
        )
        def update_select(elements, mpid):
            if elements is None:
                raise PreventUpdate
            elif not mpid or "mpid" not in mpid:
                dos_options = (
                    [{"label": "Element Projected", "value": "ap"}]
                    + [{"label": "Orbital Projected - Total", "value": "op"}]
                    + [
                        {
                            "label": "Orbital Projected - " + str(ele_label),
                            "value": "orb" + str(ele_label),
                        }
                        for ele_label in elements
                    ]
                )

                path_options = [{"label": "N/A", "value": "sc"}]
                path_style = {"max-width": "200", "display": "none"}

                return [dos_options, path_options, path_style]
            else:
                dos_options = (
                    [{"label": "Element Projected", "value": "ap"}]
                    + [{"label": "Orbital Projected - Total", "value": "op"}]
                    + [
                        {
                            "label": "Orbital Projected - " + str(ele_label),
                            "value": "orb" + str(ele_label),
                        }
                        for ele_label in elements
                    ]
                )

                path_options = [
                    {"label": "Setyawan-Curtarolo", "value": "sc"},
                    {"label": "Latimer-Munro", "value": "lm"},
                    {"label": "Hinuma et al.", "value": "hin"},
                ]

                path_style = {"max-width": "200"}

                return [dos_options, path_options, path_style]

        @app.callback(
            [Output(self.id("traces"), "data"), Output(self.id("elements"), "data")],
            [
                Input(self.id("mpid"), "data"),
                Input(self.id("path-convention"), "value"),
                Input(self.id("dos-select"), "value"),
                Input(self.id("label-select"), "value"),
                Input(self.id("bandstructure_symm_line"), "data"),
                Input(self.id("density_of_states"), "data"),
            ],
        )
        def bs_dos_data(
            mpid,
            path_convention,
            dos_select,
            label_select,
            bandstructure_symm_line,
            density_of_states,
        ):
            if (not mpid or "mpid" not in mpid) and (
                bandstructure_symm_line is None or density_of_states is None
            ):
                raise PreventUpdate
            elif mpid:
                raise PreventUpdate
            elif bandstructure_symm_line is None or density_of_states is None:

                # --
                # -- BS and DOS from API
                # --

                mpid = mpid["mpid"]
                bs_data = {"ticks": {}}

                # client = MongoClient(
                #     "mongodb03.nersc.gov", username="jmunro_lbl.gov_readWrite", password="", authSource="fw_bs_prod",
                # )

                db = client.fw_bs_prod

                # - BS traces from DB using task_id
                bs_query = list(
                    db.electronic_structure.find(
                        {"task_id": int(mpid)},
                        ["bandstructure.{}.total.traces".format(path_convention)],
                    )
                )[0]

                is_sp = (
                    len(bs_query["bandstructure"][path_convention]["total"]["traces"])
                    == 2
                )

                if is_sp:
                    bstraces = (
                        bs_query["bandstructure"][path_convention]["total"]["traces"][
                            "1"
                        ]
                        + bs_query["bandstructure"][path_convention]["total"]["traces"][
                            "-1"
                        ]
                    )
                else:
                    bstraces = bs_query["bandstructure"][path_convention]["total"][
                        "traces"
                    ]["1"]

                bs_data["ticks"]["distance"] = bs_query["bandstructure"][
                    path_convention
                ]["total"]["traces"]["ticks"]
                bs_data["ticks"]["label"] = bs_query["bandstructure"][path_convention][
                    "total"
                ]["traces"]["labels"]

                # If LM convention, get equivalent labels
                if path_convention == "lm" and label_select != "lm":
                    bs_equiv_labels = bs_query["bandstructure"][path_convention][
                        "total"
                    ]["traces"]["equiv_labels"]

                    alt_choice = label_select

                    if label_select == "hin":
                        alt_choice = "h"

                    new_labels = []
                    for label in bs_data["ticks"]["label"]:
                        label_formatted = label.replace("$", "")

                        if "|" in label_formatted:
                            f_label = label_formatted.split("|")
                            new_labels.append(
                                "$"
                                + bs_equiv_labels[alt_choice][f_label[0]]
                                + "|"
                                + bs_equiv_labels[alt_choice][f_label[1]]
                                + "$"
                            )
                        else:
                            new_labels.append(
                                "$" + bs_equiv_labels[alt_choice][label_formatted] + "$"
                            )

                    bs_data["ticks"]["label"] = new_labels

                # Strip latex math wrapping
                str_replace = {
                    "$": "",
                    "\\mid": "|",
                    "\\Gamma": "Γ",
                    "\\Sigma": "Σ",
                    "GAMMA": "Γ",
                    "_1": "₁",
                    "_2": "₂",
                    "_3": "₃",
                    "_4": "₄",
                }

                for entry_num in range(len(bs_data["ticks"]["label"])):
                    for key in str_replace.keys():
                        if key in bs_data["ticks"]["label"][entry_num]:
                            bs_data["ticks"]["label"][entry_num] = bs_data["ticks"][
                                "label"
                            ][entry_num].replace(key, str_replace[key])

                # - DOS traces from DB using task_id
                dostraces = []

                dos_tot_ele_traces = list(
                    db.electronic_structure.find(
                        {"task_id": int(mpid)}, ["dos.total.traces", "dos.elements"]
                    )
                )[0]

                dostraces = [
                    dos_tot_ele_traces["dos"]["total"]["traces"][spin]
                    for spin in dos_tot_ele_traces["dos"]["total"]["traces"].keys()
                ]

                elements = [ele for ele in dos_tot_ele_traces["dos"]["elements"].keys()]

                if dos_select == "ap":
                    for ele_label in elements:
                        dostraces += [
                            dos_tot_ele_traces["dos"]["elements"][ele_label]["total"][
                                "traces"
                            ][spin]
                            for spin in dos_tot_ele_traces["dos"]["elements"][
                                ele_label
                            ]["total"]["traces"].keys()
                        ]

                elif dos_select == "op":
                    orb_tot_traces = list(
                        db.electronic_structure.find(
                            {"task_id": int(mpid)}, ["dos.orbitals"]
                        )
                    )[0]
                    for orbital in ["s", "p", "d"]:
                        dostraces += [
                            orb_tot_traces["dos"]["orbitals"][orbital]["traces"][spin]
                            for spin in orb_tot_traces["dos"]["orbitals"]["s"][
                                "traces"
                            ].keys()
                        ]

                elif "orb" in dos_select:
                    ele_label = dos_select.replace("orb", "")

                    for orbital in ["s", "p", "d"]:
                        dostraces += [
                            dos_tot_ele_traces["dos"]["elements"][ele_label][orbital][
                                "traces"
                            ][spin]
                            for spin in dos_tot_ele_traces["dos"]["elements"][
                                ele_label
                            ][orbital]["traces"].keys()
                        ]

                traces = [bstraces, dostraces, bs_data]

                return (traces, elements)

            else:

                # --
                # -- BS and DOS passed manually
                # --

                # - BS Data

                if type(bandstructure_symm_line) != dict:
                    bandstructure_symm_line = bandstructure_symm_line.to_dict()

                if type(density_of_states) != dict:
                    density_of_states = density_of_states.to_dict()

                bs_reg_plot = BSPlotter(BSML.from_dict(bandstructure_symm_line))
                bs_data = bs_reg_plot.bs_plot_data()

                # - Strip latex math wrapping
                str_replace = {
                    "$": "",
                    "\\mid": "|",
                    "\\Gamma": "Γ",
                    "\\Sigma": "Σ",
                    "GAMMA": "Γ",
                    "_1": "₁",
                    "_2": "₂",
                    "_3": "₃",
                    "_4": "₄",
                }

                for entry_num in range(len(bs_data["ticks"]["label"])):
                    for key in str_replace.keys():
                        if key in bs_data["ticks"]["label"][entry_num]:
                            bs_data["ticks"]["label"][entry_num] = bs_data["ticks"][
                                "label"
                            ][entry_num].replace(key, str_replace[key])

                # Obtain bands to plot over:
                energy_window = (-6.0, 10.0)
                bands = []
                for band_num in range(bs_reg_plot._nb_bands):
                    if (
                        bs_data["energy"][0][str(Spin.up)][band_num][0]
                        <= energy_window[1]
                    ) and (
                        bs_data["energy"][0][str(Spin.up)][band_num][0]
                        >= energy_window[0]
                    ):
                        bands.append(band_num)

                bstraces = []

                # Generate traces for total BS data
                for d in range(len(bs_data["distances"])):
                    dist_dat = bs_data["distances"][d]
                    energy_ind = [i for i in range(len(bs_data["distances"][d]))]

                    traces_for_segment = [
                        {
                            "x": dist_dat,
                            "y": [bs_data["energy"][d]["1"][i][j] for j in energy_ind],
                            "mode": "lines",
                            "line": {"color": "#666666"},
                            "hoverinfo": "skip",
                            "showlegend": False,
                        }
                        for i in bands
                    ]

                    if bs_reg_plot._bs.is_spin_polarized:
                        traces_for_segment += [
                            {
                                "x": dist_dat,
                                "y": [
                                    bs_data["energy"][d]["-1"][i][j] for j in energy_ind
                                ],
                                "mode": "lines",
                                "line": {"color": "#666666"},
                                "hoverinfo": "skip",
                                "showlegend": False,
                            }
                            for i in bands
                        ]

                    bstraces += traces_for_segment

                # - DOS Data
                dostraces = []

                dos = CompleteDos.from_dict(density_of_states)

                dos_max = np.abs(
                    (dos.energies - dos.efermi - energy_window[1])
                ).argmin()
                dos_min = np.abs(
                    (dos.energies - dos.efermi - energy_window[0])
                ).argmin()

                if bs_reg_plot._bs.is_spin_polarized:
                    # Add second spin data if available
                    trace_tdos = go.Scatter(
                        x=dos.densities[Spin.down][dos_min:dos_max],
                        y=dos.energies[dos_min:dos_max] - dos.efermi,
                        mode="lines",
                        name="Total DOS (spin ↓)",
                        line=go.scatter.Line(color="#444444", dash="dash"),
                        fill="tozerox",
                    )

                    dostraces.append(trace_tdos)

                    tdos_label = "Total DOS (spin ↑)"
                else:
                    tdos_label = "Total DOS"

                # Total DOS
                trace_tdos = go.Scatter(
                    x=dos.densities[Spin.up][dos_min:dos_max],
                    y=dos.energies[dos_min:dos_max] - dos.efermi,
                    mode="lines",
                    name=tdos_label,
                    line=go.scatter.Line(color="#444444"),
                    fill="tozerox",
                    legendgroup="spinup",
                )

                dostraces.append(trace_tdos)

                ele_dos = dos.get_element_dos()
                elements = [str(entry) for entry in ele_dos.keys()]

                if dos_select == "ap":
                    proj_data = ele_dos
                elif dos_select == "op":
                    proj_data = dos.get_spd_dos()
                elif "orb" in dos_select:
                    proj_data = dos.get_element_spd_dos(
                        Element(dos_select.replace("orb", ""))
                    )
                else:
                    raise PreventUpdate

                # Projected DOS
                count = 0
                colors = [
                    "#1f77b4",  # muted blue
                    "#ff7f0e",  # safety orange
                    "#2ca02c",  # cooked asparagus green
                    "#9467bd",  # muted purple
                    "#e377c2",  # raspberry yogurt pink
                    "#d62728",  # brick red
                    "#8c564b",  # chestnut brown
                    "#bcbd22",  # curry yellow-green
                    "#17becf",  # blue-teal
                ]

                for label in proj_data.keys():

                    if bs_reg_plot._bs.is_spin_polarized:
                        trace = go.Scatter(
                            x=proj_data[label].densities[Spin.down][dos_min:dos_max],
                            y=dos.energies[dos_min:dos_max] - dos.efermi,
                            mode="lines",
                            name=str(label) + " (spin ↓)",
                            line=dict(width=3, color=colors[count], dash="dash"),
                        )

                        dostraces.append(trace)
                        spin_up_label = str(label) + " (spin ↑)"

                    else:
                        spin_up_label = str(label)

                    trace = go.Scatter(
                        x=proj_data[label].densities[Spin.up][dos_min:dos_max],
                        y=dos.energies[dos_min:dos_max] - dos.efermi,
                        mode="lines",
                        name=spin_up_label,
                        line=dict(width=3, color=colors[count]),
                    )

                    dostraces.append(trace)

                    count += 1

                traces = [bstraces, dostraces, bs_data]

                return (traces, elements)


class BandstructureAndDosPanelComponent(PanelComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bs = BandstructureAndDosComponent()
        self.bs.attach_from(self, this_store_name="mpid")

    @property
    def title(self):
        return "Band Structure and Density of States"

    @property
    def description(self):
        return "Display the band structure and density of states for this structure \
        if it has been calculated by the Materials Project."

    @property
    def initial_contents(self):
        return html.Div(
            [
                super().initial_contents,
                html.Div([self.bs.standard_layout], style={"display": "none"}),
            ]
        )

    def update_contents(self, new_store_contents, *args):
        return self.bs.standard_layout
