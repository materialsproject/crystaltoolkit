from __future__ import annotations

import itertools

import numpy as np
import plotly.graph_objects as go
from dash.dependencies import Component, Input, Output
from dash.exceptions import PreventUpdate
from dash_mp_components import CrystalToolkitScene
from pymatgen.core import Element
from pymatgen.electronic_structure.bandstructure import (
    BandStructure,
    BandStructureSymmLine,
)
from pymatgen.electronic_structure.core import Spin
from pymatgen.electronic_structure.dos import CompleteDos
from pymatgen.electronic_structure.plotter import BSPlotter
from pymatgen.ext.matproj import MPRester
from pymatgen.symmetry.bandstructure import HighSymmKpath

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.core.scene import Convex, Cylinders, Lines, Scene, Spheres
from crystal_toolkit.helpers.layouts import (
    Column,
    Columns,
    Label,
    Loading,
    MessageBody,
    MessageContainer,
    dcc,
    get_data_list,
    html,
)
from crystal_toolkit.helpers.pretty_labels import pretty_labels

# Author: Jason Munro
# Contact: jmunro@lbl.gov

# TODO: think about moving functionality to BSPlotter, DosPlotter
# TODO: remove access to private attributes of BSPlotter


class BandstructureAndDosComponent(MPComponent):
    def __init__(
        self,
        mpid=None,
        bandstructure_symm_line: BandStructureSymmLine | None = None,
        density_of_states: CompleteDos | None = None,
        id: str | None = None,
        **kwargs,
    ) -> None:
        # this is a compound component, can be fed by mpid or
        # by the BandStructure itself
        super().__init__(
            id=id,
            default_data={
                "mpid": mpid,
                "bandstructure_symm_line": bandstructure_symm_line,
                "density_of_states": density_of_states,
            },
            **kwargs,
        )

    @property
    def _sub_layouts(self) -> dict[str, Component]:
        # defaults
        state = {"label-select": "lm", "dos-select": "ap"}

        bs, dos = BandstructureAndDosComponent._get_bs_dos(self.initial_data["default"])
        fig = BandstructureAndDosComponent.get_figure(bs, dos)
        # Main plot
        graph = Loading(
            [dcc.Graph(figure=fig, config={"displayModeBar": False}, responsive=True)],
            id=self.id("bsdos-div"),
        )

        # Brillouin zone
        zone_scene = self.get_brillouin_zone_scene(bs)
        zone = CrystalToolkitScene(data=zone_scene.to_json(), sceneSize="500px")

        # Hide by default if not loaded by mpid, switching between k-paths
        # on-the-fly only supported for bandstructures retrieved from MP
        show_path_options = bool(self.initial_data["default"]["mpid"])

        # Convention selection for band structure
        convention = html.Div(
            [
                self.get_choice_input(
                    kwarg_label="path-convention",
                    state=state,
                    label="Path convention",
                    help_str="Convention to choose path in k-space",
                    options=[
                        {"label": "Latimer-Munro", "value": "lm"},
                        {"label": "Hinuma et al.", "value": "hin"},
                        {"label": "Setyawan-Curtarolo", "value": "sc"},
                    ],
                )
            ],
            style={"width": "200px"}
            if show_path_options
            else {"maxWidth": "200", "display": "none"},
            id=self.id("path-container"),
        )

        # Equivalent labels across band structure conventions
        label_select = html.Div(
            [
                self.get_choice_input(
                    kwarg_label="label-select",
                    state=state,
                    label="Label convention",
                    help_str="Convention to choose labels for path in k-space",
                    options=[
                        {"label": "Latimer-Munro", "value": "lm"},
                        {"label": "Hinuma et al.", "value": "hin"},
                        {"label": "Setyawan-Curtarolo", "value": "sc"},
                    ],
                )
            ],
            style={"width": "200px"}
            if show_path_options
            else {"width": "200px", "display": "none"},
            id=self.id("label-container"),
        )

        # Density of states data selection
        dos_select = self.get_choice_input(
            kwarg_label="dos-select",
            state=state,
            label="Projection",
            help_str="Choose projection",
            options=[{"label": "Atom Projected", "value": "ap"}],
            style={"width": "200px"},
        )

        table = get_data_list(self._get_data_list_dict(bs, dos))

        return {
            "graph": graph,
            "convention": convention,
            "dos-select": dos_select,
            "label-select": label_select,
            "zone": zone,
            "table": table,
        }

    def layout(self) -> html.Div:
        sub_layouts = self._sub_layouts
        graph = Columns([Column([sub_layouts["graph"]])])
        controls = Columns(
            [
                Column(
                    [
                        sub_layouts["convention"],
                        sub_layouts["label-select"],
                        sub_layouts["dos-select"],
                    ]
                )
            ]
        )
        brillouin_zone = Columns(
            [
                Column([Label("Summary"), sub_layouts["table"]]),
                Column([Label("Brillouin Zone"), sub_layouts["zone"]]),
            ]
        )
        return html.Div([graph, controls, brillouin_zone])

    @staticmethod
    def _get_bs_dos(
        data: dict | None,
    ) -> tuple[BandStructureSymmLine, CompleteDos] | tuple[None, None]:
        data = data or {}

        # this component can be loaded either from mpid or
        # directly from BandStructureSymmLine or CompleteDos objects
        # if mpid is supplied, it takes precedence

        mpid = data.get("mpid")
        bandstructure_symm_line = data.get("bandstructure_symm_line")
        density_of_states = data.get("density_of_states")

        if not mpid and bandstructure_symm_line is None and density_of_states is None:
            return None, None

        if mpid:
            with MPRester() as mpr:
                try:
                    bandstructure_symm_line = mpr.get_bandstructure_by_material_id(mpid)
                except Exception as exc:
                    print(exc)
                    bandstructure_symm_line = None

                try:
                    density_of_states = mpr.get_dos_by_material_id(mpid)
                except Exception as exc:
                    print(exc)
                    density_of_states = None

        else:
            if bandstructure_symm_line and isinstance(bandstructure_symm_line, dict):
                bandstructure_symm_line = BandStructureSymmLine.from_dict(
                    bandstructure_symm_line
                )

            if density_of_states and isinstance(density_of_states, dict):
                density_of_states = CompleteDos.from_dict(density_of_states)

        return bandstructure_symm_line, density_of_states

    @staticmethod
    def get_ifermi_scene(bs: BandStructure) -> Scene:
        pass

    @staticmethod
    def get_brillouin_zone_scene(bs: BandStructureSymmLine) -> Scene:
        if not bs:
            return Scene(name="brillouin_zone", contents=[])

        # TODO: from BSPlotter, merge back into BSPlotter
        # Brillouin zone
        bz_lattice = bs.structure.lattice.reciprocal_lattice
        bz = bz_lattice.get_wigner_seitz_cell()
        lines = []
        for iface in range(len(bz)):  # pylint: disable=C0200
            for line in itertools.combinations(bz[iface], 2):
                for jface in range(len(bz)):
                    if (
                        iface < jface
                        and any(np.all(line[0] == x) for x in bz[jface])
                        and any(np.all(line[1] == x) for x in bz[jface])
                    ):
                        lines += [list(line[0]), list(line[1])]

        zone_lines = Lines(positions=lines)
        zone_surface = Convex(positions=lines, opacity=0.05, color="#000000")

        labels = {}
        for kpt in bs.kpoints:
            if kpt.label:
                label = kpt.label
                for orig, new in pretty_labels.items():
                    label = label.replace(orig, new)
                labels[label] = bz_lattice.get_cartesian_coords(kpt.frac_coords)
        labels = [
            Spheres(positions=[coords], tooltip=label, radius=0.03, color="#5EB1BF")
            for label, coords in labels.items()
        ]

        path = []
        cylinder_pairs = []
        for b in bs.branches:
            start = bz_lattice.get_cartesian_coords(
                bs.kpoints[b["start_index"]].frac_coords
            )
            end = bz_lattice.get_cartesian_coords(
                bs.kpoints[b["end_index"]].frac_coords
            )
            path += [start, end]
            cylinder_pairs += [[start, end]]
        # path_lines = Lines(positions=path, color="#ff4b5c")
        path_lines = Cylinders(
            positionPairs=cylinder_pairs, color="#5EB1BF", radius=0.01
        )
        ibz_region = Convex(positions=path, opacity=0.2, color="#5EB1BF")

        contents = [zone_lines, zone_surface, path_lines, ibz_region, *labels]

        cbm = bs.get_cbm()["kpoint"]
        vbm = bs.get_vbm()["kpoint"]

        if cbm and vbm:
            if cbm.label:
                cbm_label = cbm.label
                for orig, new in pretty_labels.items():
                    cbm_label = cbm_label.replace(orig, new)
                cbm_label = f"CBM at {cbm_label}"
            else:
                cbm_label = "CBM"

            if cbm == vbm:
                cbm_label = f"VBM and {cbm_label}"

            cbm_coords = bz_lattice.get_cartesian_coords(cbm.frac_coords)
            cbm = Spheres(
                positions=[cbm_coords], tooltip=cbm_label, radius=0.05, color="#7E259B"
            )

            contents.append(cbm)

            if cbm != vbm:
                if vbm.label:
                    vbm_label = vbm.label
                    for orig, new in pretty_labels.items():
                        vbm_label = vbm_label.replace(orig, new)
                    vbm_label = f"VBM at {vbm_label}"
                else:
                    vbm_label = "VBM"

                vbm_coords = bz_lattice.get_cartesian_coords(vbm.frac_coords)
                vbm = Spheres(
                    positions=[vbm_coords],
                    tooltip=vbm_label,
                    radius=0.05,
                    color="#7E259B",
                )

                contents.append(vbm)

        return Scene(name="brillouin_zone", contents=contents)

    @staticmethod
    def get_bandstructure_traces(
        bs, path_convention: str, energy_window: tuple[float, float] = (-6.0, 10.0)
    ) -> tuple:
        if path_convention == "lm":
            bs = HighSymmKpath.get_continuous_path(bs)

        bs_reg_plot = BSPlotter(bs)

        bs_data = bs_reg_plot.bs_plot_data(split_branches=False)

        bands = []
        for band_num in range(bs.nb_bands):
            for segment in bs_data["energy"][str(Spin.up)]:
                if any(segment[band_num] <= energy_window[1]) and any(
                    segment[band_num] >= energy_window[0]
                ):
                    bands.append(band_num)  # noqa: PERF401

        bs_traces = []

        cbm = bs.get_cbm()
        vbm = bs.get_vbm()

        cbm_new = bs_data["cbm"]
        vbm_new = bs_data["vbm"]

        for d, dist_val in enumerate(bs_data["distances"]):
            x_dat = dist_val

            traces_for_segment = []

            segment = bs_data["energy"][str(Spin.up)][d]

            traces_for_segment += [
                {
                    "x": x_dat,
                    "y": segment[band_num],
                    "mode": "lines",
                    "line": {"color": "#1f77b4"},
                    "hoverinfo": "skip",
                    "name": "spin ↑" if bs.is_spin_polarized else "Total",
                    "hovertemplate": "%{y:.2f} eV",
                    "showlegend": False,
                    "xaxis": "x",
                    "yaxis": "y",
                }
                for band_num in bands
            ]

            if bs.is_spin_polarized:
                traces_for_segment += [
                    {
                        "x": x_dat,
                        "y": [
                            bs_data["energy"][str(Spin.down)][d][i][j]
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

            bs_traces += traces_for_segment

        for entry_num in range(len(bs_data["ticks"]["label"])):
            for key in pretty_labels:
                if key in bs_data["ticks"]["label"][entry_num]:
                    bs_data["ticks"]["label"][entry_num] = bs_data["ticks"]["label"][
                        entry_num
                    ].replace(key, pretty_labels[key])

        # Vertical lines for disjointed segments
        for dist_val, tick_label in zip(
            bs_data["ticks"]["distance"], bs_data["ticks"]["label"]
        ):
            vert_trace = [
                {
                    "x": [dist_val, dist_val],
                    "y": energy_window,
                    "mode": "lines",
                    "marker": {
                        "color": "#F5F5F5" if "|" not in tick_label else "white"
                    },
                    "line": {"width": 0.5 if "|" not in tick_label else 2},
                    "hoverinfo": "skip",
                    "showlegend": False,
                    "xaxis": "x",
                    "yaxis": "y",
                }
            ]
            bs_traces += vert_trace

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
                "hovertemplate": f"CBM: k = {list(cbm['kpoint'].frac_coords)}, {cbm['energy']} eV",
                "xaxis": "x",
                "yaxis": "y",
            }
            for x_point, y_point in set(cbm_new)
        ] + [
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
                "hovertemplate": f"VBM: k = {list(vbm['kpoint'].frac_coords)}, {vbm['energy']} eV",
                "xaxis": "x",
                "yaxis": "y",
            }
            for x_point, y_point in set(vbm_new)
        ]

        bs_traces += dot_traces

        return bs_traces, bs_data

    @staticmethod
    def get_dos_traces(
        dos,
        dos_select,
        energy_window: tuple[float, float] = (-6.0, 10.0),
        horizontal: bool = False,
    ) -> list:
        if horizontal:
            dos_axis, en_axis = "y", "x"
        else:
            dos_axis, en_axis = "x", "y"

        dos_traces = []

        dos_max = np.abs(dos.energies - dos.efermi - energy_window[1]).argmin()
        dos_min = np.abs(dos.energies - dos.efermi - energy_window[0]).argmin()

        # TODO: pymatgen should have a property here
        spin_polarized = len(dos.densities) == 2

        if spin_polarized:
            # Add second spin data if available
            trace_tdos = {
                dos_axis: -1.0 * dos.densities[Spin.down][dos_min:dos_max],
                en_axis: dos.energies[dos_min:dos_max] - dos.efermi,
                "mode": "lines",
                "name": "Total DOS (spin ↓)",
                "line": go.scatter.Line(color="#444444", dash="dot"),
                "fill": f"tozero{dos_axis}",
                "fillcolor": "#C4C4C4",
                "xaxis": "x2",
                "yaxis": "y2",
            }

            dos_traces.append(trace_tdos)

            tdos_label = "Total DOS (spin ↑)"
        else:
            tdos_label = "Total DOS"

        # Total DOS
        trace_tdos = {
            dos_axis: dos.densities[Spin.up][dos_min:dos_max],
            en_axis: dos.energies[dos_min:dos_max] - dos.efermi,
            "mode": "lines",
            "name": tdos_label,
            "line": go.scatter.Line(color="#444444"),
            "fill": f"tozero{dos_axis}",
            "fillcolor": "#C4C4C4",
            "legendgroup": "spinup",
            "xaxis": "x2",
            "yaxis": "y2",
        }

        dos_traces.append(trace_tdos)

        if dos_select == "tot":
            proj_data = {}
        elif dos_select == "ap":
            proj_data = dos.get_element_dos()
        elif dos_select == "op":
            proj_data = dos.get_spd_dos()
        elif "orb" in dos_select:
            proj_data = dos.get_element_spd_dos(Element(dos_select.replace("orb", "")))
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

        for label in proj_data:
            if spin_polarized:
                trace = {
                    dos_axis: -1.0
                    * proj_data[label].densities[Spin.down][dos_min:dos_max],
                    en_axis: dos.energies[dos_min:dos_max] - dos.efermi,
                    "mode": "lines",
                    "name": f"{label} (spin ↓)",
                    "line": dict(width=3, color=colors[count], dash="dot"),
                    "xaxis": "x2",
                    "yaxis": "y2",
                }

                dos_traces.append(trace)
                spin_up_label = f"{label} (spin ↑)"

            else:
                spin_up_label = str(label)

            trace = {
                dos_axis: proj_data[label].densities[Spin.up][dos_min:dos_max],
                en_axis: dos.energies[dos_min:dos_max] - dos.efermi,
                "mode": "lines",
                "name": spin_up_label,
                "line": dict(width=2, color=colors[count]),
                "xaxis": "x2",
                "yaxis": "y2",
            }

            dos_traces.append(trace)

            count += 1

        return dos_traces

    @staticmethod
    def get_figure(
        bs,
        dos,
        path_convention="sc",
        dos_select="ap",
        energy_window=(-6.0, 10.0),
        horizontal_dos=False,
        bs_domain=None,
        dos_domain=None,
    ) -> go.Figure:
        if (not dos) and (not bs):
            empty_plot_style = {
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
            }

            return go.Figure(layout=empty_plot_style)

        # -- Add trace data to plots

        traces = []
        xaxis_style = {}
        yaxis_style = {}
        xaxis_style_dos = {}
        yaxis_style_dos = {}

        y_title = dict(text="E-E<sub>fermi</sub> (eV)", font=dict(size=16))
        if bs:
            bs_traces, bs_data = BandstructureAndDosComponent.get_bandstructure_traces(
                bs, path_convention=path_convention, energy_window=energy_window
            )
            traces += bs_traces

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
                title=y_title,
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

        if dos:
            dos_traces = BandstructureAndDosComponent.get_dos_traces(
                dos,
                dos_select=dos_select,
                energy_window=energy_window,
                horizontal=horizontal_dos,
            )
            traces += dos_traces

            list_max = [
                max(dos_traces[0]["x"]),
                abs(min(dos_traces[0]["x"])),
            ]

            # check the max of the second dos trace only if spin polarized
            spin_polarized = len(dos.densities) == 2
            if spin_polarized:
                list_max.extend(
                    [
                        max(dos_traces[1]["x"]),
                        abs(min(dos_traces[1]["x"])),
                    ]
                )
            rmax = max(list_max)

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
                range=[-rmax * 1.1 * int(len(dos.densities) == 2), rmax * 1.1],
                linecolor="rgb(71,71,71)",
                gridcolor="white",
                zerolinecolor="white",
                zerolinewidth=2,
                anchor="x2" if horizontal_dos else None,
            )

            yaxis_style_dos = dict(
                title=y_title if bs is None or horizontal_dos else None,
                tickfont=dict(size=16),
                showgrid=False,
                showline=True,
                zeroline=True,
                showticklabels=bs is None or horizontal_dos,
                mirror="ticks",
                ticks="inside",
                linewidth=2,
                tickwidth=2,
                zerolinewidth=2,
                range=[-5, 9],
                linecolor="rgb(71,71,71)",
                gridcolor="white",
                zerolinecolor="white",
                matches="y" if not horizontal_dos else None,
                anchor="x2",
            )

            if horizontal_dos:
                xaxis_style_dos, yaxis_style_dos = yaxis_style_dos, xaxis_style_dos

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
            # clickmode="event+select"
        )

        figure = {"data": traces, "layout": layout}

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

        if bs and dos:
            if horizontal_dos:
                # some additional space for the y axis label of the dos
                bs_domain = bs_domain or [0, 0.67]
                dos_domain = dos_domain or [0.73, 1.0]
            else:
                bs_domain = bs_domain or [0, 0.7]
                dos_domain = dos_domain or [0.73, 1.0]
        elif bs:
            bs_domain = bs_domain or [0, 1.0]
            dos_domain = dos_domain or [1.0, 1.0]
        elif dos:
            bs_domain = bs_domain or [0, 0]
            dos_domain = (
                dos_domain or [0, 1.0] if horizontal_dos else dos_domain or [0, 0.3]
            )

        figure["layout"]["xaxis1"]["domain"] = bs_domain
        figure["layout"]["xaxis2"]["domain"] = dos_domain

        return figure

    @staticmethod
    def _get_data_list_dict(bs, dos):
        return {
            "Band Gap": "... eV",
            "Direct Gap": "...",
            "CBM": "...",
            "VBM": "...",
            "Spin Polarization": "...",
        }

    def generate_callbacks(self, app, cache) -> None:
        """Register callback functions for this component."""

        @app.callback(
            Output(self.id("bsdos-div"), "children"), Input(self.id("traces"), "data")
        )
        def update_graph(traces):
            if traces == "error":
                body = MessageBody(
                    dcc.Markdown(
                        "Band structure and density of states not available for this selection."
                    )
                )
                return MessageContainer([body], kind="warning")

            if traces is None:
                raise PreventUpdate

            figure = self.get_figure(bs, dos, path_convention, dos_select)

            return [
                dcc.Graph(
                    figure=figure, config={"displayModeBar": False}, responsive=True
                )
            ]

        @app.callback(
            Output(self.id("label-select"), "value"),
            Output(self.id("label-container"), "style"),
            Input(self.id("mpid"), "data"),
            Input(self.id("path-convention"), "value"),
        )
        def update_label_select(mpid, path_convention):
            if not mpid:
                raise PreventUpdate
            label_value = path_convention
            label_style = {"maxWidth": "200"}

            return label_value, label_style

        @app.callback(
            Output(self.id("dos-select"), "options"),
            Output(self.id("path-convention"), "options"),
            Output(self.id("path-container"), "style"),
            Input(self.id("elements"), "data"),
            Input(self.id("mpid"), "data"),
        )
        def update_select(elements, mpid):
            if elements is None:
                raise PreventUpdate
            if not mpid:
                dos_options = (
                    [{"label": "Element Projected", "value": "ap"}]
                    + [{"label": "Orbital Projected - Total", "value": "op"}]
                    + [
                        {
                            "label": f"Orbital Projected - {ele_label}",
                            "value": f"orb{ele_label}",
                        }
                        for ele_label in elements
                    ]
                )

                path_options = [{"label": "N/A", "value": "sc"}]
                path_style = {"maxWidth": "200", "display": "none"}

                return [dos_options, path_options, path_style]
            dos_options = (
                [{"label": "Element Projected", "value": "ap"}]
                + [{"label": "Orbital Projected - Total", "value": "op"}]
                + [
                    {
                        "label": f"Orbital Projected - {ele_label}",
                        "value": f"orb{ele_label}",
                    }
                    for ele_label in elements
                ]
            )

            path_options = [
                {"label": "Setyawan-Curtarolo", "value": "sc"},
                {"label": "Latimer-Munro", "value": "lm"},
                {"label": "Hinuma et al.", "value": "hin"},
            ]

            path_style = {"maxWidth": "200"}

            return dos_options, path_options, path_style

        @app.callback(
            Output(self.id("traces"), "data"),
            Output(self.id("elements"), "data"),
            Input(self.id(), "data"),
            Input(self.id("path-convention"), "value"),
            Input(self.id("dos-select"), "value"),
            Input(self.id("label-select"), "value"),
        )
        def bs_dos_data(data, path_convention, dos_select, label_select):
            # Obtain bands to plot over and generate traces for bs data:
            energy_window = (-6.0, 10.0)

            traces = []

            if bandstructure_symm_line:
                bs_traces = get_bandstructure_traces(
                    bsml, path_convention, energy_window=energy_window
                )
                traces.append(bs_traces)

            if density_of_states:
                dos_traces = get_dos_traces(
                    density_of_states, energy_window=energy_window, spin_polarized=...
                )
                traces.append(dos_traces)

            # traces = [bs_traces, dos_traces, bs_data]

            return traces, elements


class BandstructureAndDosPanelComponent(PanelComponent):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.bs = BandstructureAndDosComponent()
        self.bs.attach_from(self, this_store_name="mpid")

    @property
    def title(self) -> str:
        return "Band Structure and Density of States"

    @property
    def description(self) -> str:
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
