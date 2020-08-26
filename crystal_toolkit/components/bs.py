import numpy as np
import numpy as np
import plotly.graph_objs as go
import plotly.subplots as tls
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from pymatgen.core.periodic_table import Element
from pymatgen.electronic_structure.bandstructure import BandStructureSymmLine as BSML
from pymatgen.symmetry.bandstructure import HighSymmKpath as HSKP
from pymatgen.electronic_structure.core import Spin
from pymatgen.electronic_structure.dos import CompleteDos
from pymatgen.electronic_structure.plotter import BSPlotter

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import *

# -- Temp fake API
from maggma.stores import MongoStore, GridFSStore, JSONStore


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

            bstraces, dostraces, bs_data = traces

            rmax = max(
                [
                    max(dostraces[0]["x"]),
                    abs(min(dostraces[0]["x"])),
                    max(dostraces[1]["x"]),
                    abs(min(dostraces[1]["x"])),
                ]
            )

            # -- Add trace data to plots

            xaxis_style = dict(
                title=dict(text="Wave Vector", font=dict(size=16)),
                tickmode="array",
                tickvals=bs_data["ticks"]["distance"],
                ticktext=bs_data["ticks"]["label"],
                tickfont=dict(size=16),
                ticks="inside",
                tickwidth=2,
                showgrid=False,
                showline=True,
                zeroline=False,
                linewidth=2,
                mirror=True,
                range=[0, bs_data["ticks"]["distance"][-1]],
                linecolor="rgb(71,71,71)",
                gridcolor="white",
            )

            yaxis_style = dict(
                title=dict(text="E−E<sub>fermi</sub> (eV)", font=dict(size=16)),
                tickfont=dict(size=16),
                showgrid=False,
                showline=True,
                zeroline=True,
                mirror="ticks",
                ticks="inside",
                linewidth=2,
                tickwidth=2,
                zerolinewidth=2,
                range=[-5, 9],
                linecolor="rgb(71,71,71)",
                gridcolor="white",
                zerolinecolor="white",
            )

            xaxis_style_dos = dict(
                title=dict(text="Density of States", font=dict(size=16)),
                tickfont=dict(size=16),
                showgrid=False,
                showline=True,
                zeroline=False,
                mirror=True,
                ticks="inside",
                linewidth=2,
                tickwidth=2,
                range=[
                    -rmax * 1.1 * int(len(bs_data["energy"][0].keys()) == 2),
                    rmax * 1.1,
                ],
                linecolor="rgb(71,71,71)",
                gridcolor="white",
                zerolinecolor="white",
                zerolinewidth=2,
            )

            yaxis_style_dos = dict(
                tickfont=dict(size=16),
                showgrid=False,
                showline=True,
                zeroline=True,
                showticklabels=False,
                mirror="ticks",
                ticks="inside",
                linewidth=2,
                tickwidth=2,
                zerolinewidth=2,
                range=[-5, 9],
                linecolor="rgb(71,71,71)",
                gridcolor="white",
                zerolinecolor="white",
                matches="y",
                anchor="x2",
            )

            layout = dict(
                title="",
                xaxis1=xaxis_style,
                xaxis2=xaxis_style_dos,
                yaxis=yaxis_style,
                yaxis2=yaxis_style_dos,
                showlegend=True,
                height=500,
                width=1000,
                hovermode="closest",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(230,230,230,230)",
                margin=dict(l=60, b=50, t=50, pad=0, r=30),
            )

            figure = {"data": bstraces + dostraces, "layout": layout}

            legend = dict(
                x=1.02,
                y=1.005,
                xanchor="left",
                yanchor="top",
                bordercolor="#333",
                borderwidth=2,
                traceorder="normal",
            )

            figure["layout"]["legend"] = legend

            figure["layout"]["xaxis1"]["domain"] = [0.0, 0.7]
            figure["layout"]["xaxis2"]["domain"] = [0.73, 1.0]

            return [
                dcc.Graph(
                    figure=figure, config={"displayModeBar": False}, responsive=True
                )
            ]

        @app.callback(
            [
                Output(self.id("label-select"), "value"),
                Output(self.id("label-container"), "style"),
            ],
            [
                Input(self.id("mpid"), "data"),
                Input(self.id("path-convention"), "value"),
            ],
        )
        def update_label_select(mpid, path_convention):
            if not mpid:
                raise PreventUpdate
            else:

                label_value = path_convention
                label_style = {"max-width": "200"}

                return [label_value, label_style]

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
            elif not mpid:
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
            if not mpid and (
                bandstructure_symm_line is None or density_of_states is None
            ):
                raise PreventUpdate

            elif bandstructure_symm_line is None or density_of_states is None:
                if label_select == "":
                    raise PreventUpdate

                # --
                # -- BS and DOS from API or DB
                # --

                bs_data = {"ticks": {}}

                bs_store = GridFSStore(
                    database="fw_bs_prod",
                    collection_name="bandstructure_fs",
                    host="mongodb03.nersc.gov",
                    port=27017,
                    username="jmunro_lbl.gov_readWrite",
                    password="",
                )

                dos_store = GridFSStore(
                    database="fw_bs_prod",
                    collection_name="dos_fs",
                    host="mongodb03.nersc.gov",
                    port=27017,
                    username="jmunro_lbl.gov_readWrite",
                    password="",
                )

                es_store = MongoStore(
                    database="fw_bs_prod",
                    collection_name="electronic_structure",
                    host="mongodb03.nersc.gov",
                    port=27017,
                    username="jmunro_lbl.gov_readWrite",
                    password="",
                    key="task_id",
                )

                # - BS traces from DB using task_id
                es_store.connect()
                bs_query = es_store.query_one(
                    criteria={"task_id": int(mpid)},
                    properties=[
                        "bandstructure.{}.task_id".format(path_convention),
                        "bandstructure.{}.total.equiv_labels".format(path_convention),
                    ],
                )

                es_store.close()

                bs_store.connect()
                bandstructure_symm_line = bs_store.query_one(
                    criteria={
                        "metadata.task_id": int(
                            bs_query["bandstructure"][path_convention]["task_id"]
                        )
                    },
                )

                # If LM convention, get equivalent labels
                if path_convention != label_select:
                    bs_equiv_labels = bs_query["bandstructure"][path_convention][
                        "total"
                    ]["equiv_labels"]

                    new_labels_dict = {}
                    for label in bandstructure_symm_line["labels_dict"].keys():

                        label_formatted = label.replace("$", "")

                        if "|" in label_formatted:
                            f_label = label_formatted.split("|")
                            new_labels.append(
                                "$"
                                + bs_equiv_labels[label_select][f_label[0]]
                                + "|"
                                + bs_equiv_labels[label_select][f_label[1]]
                                + "$"
                            )
                        else:
                            new_labels_dict[
                                "$"
                                + bs_equiv_labels[label_select][label_formatted]
                                + "$"
                            ] = bandstructure_symm_line["labels_dict"][label]

                    bandstructure_symm_line["labels_dict"] = new_labels_dict

                # - DOS traces from DB using task_id
                es_store.connect()
                dos_query = es_store.query_one(
                    criteria={"task_id": int(mpid)}, properties=["dos.task_id"],
                )
                es_store.close()

                dos_store.connect()
                density_of_states = dos_store.query_one(
                    criteria={"task_id": int(dos_query["dos"]["task_id"])},
                )

            # - BS Data
            if (
                type(bandstructure_symm_line) != dict
                and bandstructure_symm_line is not None
            ):
                bandstructure_symm_line = bandstructure_symm_line.to_dict()

            if type(density_of_states) != dict and density_of_states is not None:
                density_of_states = density_of_states.to_dict()

            bsml = BSML.from_dict(bandstructure_symm_line)

            bs_reg_plot = BSPlotter(bsml)

            bs_data = bs_reg_plot.bs_plot_data()

            # Make plot continous for lm
            if path_convention == "lm":
                distance_map, kpath_euler = HSKP(bsml.structure).get_continuous_path(
                    bsml
                )

                kpath_labels = [pair[0] for pair in kpath_euler]
                kpath_labels.append(kpath_euler[-1][1])

            else:
                distance_map = [(i, False) for i in range(len(bs_data["distances"]))]
                kpath_labels = []
                for label_ind in range(len(bs_data["ticks"]["label"]) - 1):
                    if (
                        bs_data["ticks"]["label"][label_ind]
                        != bs_data["ticks"]["label"][label_ind + 1]
                    ):
                        kpath_labels.append(bs_data["ticks"]["label"][label_ind])
                kpath_labels.append(bs_data["ticks"]["label"][-1])

            bs_data["ticks"]["label"] = kpath_labels

            # Obtain bands to plot over and generate traces for bs data:
            energy_window = (-6.0, 10.0)
            bands = []
            for band_num in range(bs_reg_plot._nb_bands):
                if (
                    bs_data["energy"][0][str(Spin.up)][band_num][0] <= energy_window[1]
                ) and (
                    bs_data["energy"][0][str(Spin.up)][band_num][0] >= energy_window[0]
                ):
                    bands.append(band_num)

            bstraces = []

            pmin = 0.0
            tick_vals = [0.0]

            cbm = bsml.get_cbm()
            vbm = bsml.get_vbm()

            cbm_new = bs_data["cbm"]
            vbm_new = bs_data["vbm"]

            for dnum, (d, rev) in enumerate(distance_map):

                x_dat = [
                    dval - bs_data["distances"][d][0] + pmin
                    for dval in bs_data["distances"][d]
                ]

                pmin = x_dat[-1]

                tick_vals.append(pmin)

                if not rev:
                    traces_for_segment = [
                        {
                            "x": x_dat,
                            "y": [
                                bs_data["energy"][d][str(Spin.up)][i][j]
                                for j in range(len(bs_data["distances"][d]))
                            ],
                            "mode": "lines",
                            "line": {"color": "#1f77b4"},
                            "hoverinfo": "skip",
                            "name": "spin ↑"
                            if bs_reg_plot._bs.is_spin_polarized
                            else "Total",
                            "hovertemplate": "%{y:.2f} eV",
                            "showlegend": False,
                            "xaxis": "x",
                            "yaxis": "y",
                        }
                        for i in bands
                    ]
                elif rev:
                    traces_for_segment = [
                        {
                            "x": x_dat,
                            "y": [
                                bs_data["energy"][d][str(Spin.up)][i][j]
                                for j in reversed(range(len(bs_data["distances"][d])))
                            ],
                            "mode": "lines",
                            "line": {"color": "#1f77b4"},
                            "hoverinfo": "skip",
                            "name": "spin ↑"
                            if bs_reg_plot._bs.is_spin_polarized
                            else "Total",
                            "hovertemplate": "%{y:.2f} eV",
                            "showlegend": False,
                            "xaxis": "x",
                            "yaxis": "y",
                        }
                        for i in bands
                    ]

                if bs_reg_plot._bs.is_spin_polarized:

                    if not rev:
                        traces_for_segment += [
                            {
                                "x": x_dat,
                                "y": [
                                    bs_data["energy"][d][str(Spin.down)][i][j]
                                    for j in range(len(bs_data["distances"][d]))
                                ],
                                "mode": "lines",
                                "line": {"color": "#ff7f0e", "dash": "dot"},
                                "hoverinfo": "skip",
                                "showlegend": False,
                                "name": "spin ↓",
                                "hovertemplate": "%{y:.2f} eV",
                                "xaxis": "x",
                                "yaxis": "y",
                            }
                            for i in bands
                        ]
                    elif rev:
                        traces_for_segment += [
                            {
                                "x": x_dat,
                                "y": [
                                    bs_data["energy"][d][str(Spin.down)][i][j]
                                    for j in reversed(
                                        range(len(bs_data["distances"][d]))
                                    )
                                ],
                                "mode": "lines",
                                "line": {"color": "#ff7f0e", "dash": "dot"},
                                "hoverinfo": "skip",
                                "showlegend": False,
                                "name": "spin ↓",
                                "hovertemplate": "%{y:.2f} eV",
                                "xaxis": "x",
                                "yaxis": "y",
                            }
                            for i in bands
                        ]

                bstraces += traces_for_segment

                # - Get proper cbm and vbm coords for lm
                if path_convention == "lm":
                    for (x_point, y_point) in bs_data["cbm"]:
                        if x_point in bs_data["distances"][d]:
                            xind = bs_data["distances"][d].index(x_point)
                            if not rev:
                                x_point_new = x_dat[xind]
                            else:
                                x_point_new = x_dat[len(x_dat) - xind - 1]

                            new_label = bs_data["ticks"]["label"][
                                tick_vals.index(x_point_new)
                            ]

                            if (
                                cbm["kpoint"].label is None
                                or cbm["kpoint"].label in new_label
                            ):
                                cbm_new.append((x_point_new, y_point))

                    for (x_point, y_point) in bs_data["vbm"]:
                        if x_point in bs_data["distances"][d]:
                            xind = bs_data["distances"][d].index(x_point)
                            if not rev:
                                x_point_new = x_dat[xind]
                            else:
                                x_point_new = x_dat[len(x_dat) - xind - 1]

                            new_label = bs_data["ticks"]["label"][
                                tick_vals.index(x_point_new)
                            ]

                            if (
                                vbm["kpoint"].label is None
                                or vbm["kpoint"].label in new_label
                            ):
                                vbm_new.append((x_point_new, y_point))

            bs_data["ticks"]["distance"] = tick_vals

            # - Strip latex math wrapping for labels
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
                "_{1}": "₁",
                "_{2}": "₂",
                "_{3}": "₃",
                "_{4}": "₄",
                "^{*}": "*",
            }

            bar_loc = []
            for entry_num in range(len(bs_data["ticks"]["label"])):
                for key in str_replace.keys():
                    if key in bs_data["ticks"]["label"][entry_num]:
                        bs_data["ticks"]["label"][entry_num] = bs_data["ticks"][
                            "label"
                        ][entry_num].replace(key, str_replace[key])
                        if key == "\\mid":
                            bar_loc.append(bs_data["ticks"]["distance"][entry_num])

            # Vertical lines for disjointed segments
            vert_traces = [
                {
                    "x": [x_point, x_point],
                    "y": energy_window,
                    "mode": "lines",
                    "marker": {"color": "white"},
                    "hoverinfo": "skip",
                    "showlegend": False,
                    "xaxis": "x",
                    "yaxis": "y",
                }
                for x_point in bar_loc
            ]

            bstraces += vert_traces

            # Dots for cbm and vbm

            dot_traces = [
                {
                    "x": [x_point],
                    "y": [y_point],
                    "mode": "markers",
                    "marker": {
                        "color": "#7E259B",
                        "size": 16,
                        "line": {"color": "white", "width": 2},
                    },
                    "showlegend": False,
                    "hoverinfo": "text",
                    "name": "",
                    "hovertemplate": "CBM: k = {}, {} eV".format(
                        list(cbm["kpoint"].frac_coords), cbm["energy"]
                    ),
                    "xaxis": "x",
                    "yaxis": "y",
                }
                for (x_point, y_point) in set(cbm_new)
            ] + [
                {
                    "x": [x_point],
                    "y": [y_point],
                    "mode": "marker",
                    "marker": {
                        "color": "#7E259B",
                        "size": 16,
                        "line": {"color": "white", "width": 2},
                    },
                    "showlegend": False,
                    "hoverinfo": "text",
                    "name": "",
                    "hovertemplate": "VBM: k = {}, {} eV".format(
                        list(vbm["kpoint"].frac_coords), vbm["energy"]
                    ),
                    "xaxis": "x",
                    "yaxis": "y",
                }
                for (x_point, y_point) in set(vbm_new)
            ]

            bstraces += dot_traces

            # - DOS Data
            dostraces = []

            dos = CompleteDos.from_dict(density_of_states)

            dos_max = np.abs((dos.energies - dos.efermi - energy_window[1])).argmin()
            dos_min = np.abs((dos.energies - dos.efermi - energy_window[0])).argmin()

            if bs_reg_plot._bs.is_spin_polarized:
                # Add second spin data if available
                trace_tdos = {
                    "x": -1.0 * dos.densities[Spin.down][dos_min:dos_max],
                    "y": dos.energies[dos_min:dos_max] - dos.efermi,
                    "mode": "lines",
                    "name": "Total DOS (spin ↓)",
                    "line": go.scatter.Line(color="#444444", dash="dot"),
                    "fill": "tozerox",
                    "fillcolor": "#C4C4C4",
                    "xaxis": "x2",
                    "yaxis": "y2",
                }

                dostraces.append(trace_tdos)

                tdos_label = "Total DOS (spin ↑)"
            else:
                tdos_label = "Total DOS"

            # Total DOS
            trace_tdos = {
                "x": dos.densities[Spin.up][dos_min:dos_max],
                "y": dos.energies[dos_min:dos_max] - dos.efermi,
                "mode": "lines",
                "name": tdos_label,
                "line": go.scatter.Line(color="#444444"),
                "fill": "tozerox",
                "fillcolor": "#C4C4C4",
                "legendgroup": "spinup",
                "xaxis": "x2",
                "yaxis": "y2",
            }

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
                "#d62728",  # brick red
                "#2ca02c",  # cooked asparagus green
                "#17becf",  # blue-teal
                "#bcbd22",  # curry yellow-green
                "#9467bd",  # muted purple
                "#8c564b",  # chestnut brown
                "#e377c2",  # raspberry yogurt pink
            ]

            for label in proj_data.keys():

                if bs_reg_plot._bs.is_spin_polarized:
                    trace = {
                        "x": -1.0
                        * proj_data[label].densities[Spin.down][dos_min:dos_max],
                        "y": dos.energies[dos_min:dos_max] - dos.efermi,
                        "mode": "lines",
                        "name": str(label) + " (spin ↓)",
                        "line": dict(width=3, color=colors[count], dash="dot"),
                        "xaxis": "x2",
                        "yaxis": "y2",
                    }

                    dostraces.append(trace)
                    spin_up_label = str(label) + " (spin ↑)"

                else:
                    spin_up_label = str(label)

                trace = {
                    "x": proj_data[label].densities[Spin.up][dos_min:dos_max],
                    "y": dos.energies[dos_min:dos_max] - dos.efermi,
                    "mode": "lines",
                    "name": spin_up_label,
                    "line": dict(width=2, color=colors[count]),
                    "xaxis": "x2",
                    "yaxis": "y2",
                }

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
