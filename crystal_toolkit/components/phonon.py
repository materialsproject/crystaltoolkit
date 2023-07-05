from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, Any

import numpy as np
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Component, Input, Output
from dash.exceptions import PreventUpdate
from dash_mp_components import CrystalToolkitScene
from pymatgen.ext.matproj import MPRester
from pymatgen.phonon.bandstructure import PhononBandStructureSymmLine
from pymatgen.phonon.dos import CompletePhononDos
from pymatgen.phonon.plotter import PhononBSPlotter

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.core.scene import Convex, Cylinders, Lines, Scene, Spheres
from crystal_toolkit.helpers.layouts import (
    Column,
    Columns,
    Label,
    MessageBody,
    MessageContainer,
    get_data_list,
)
from crystal_toolkit.helpers.pretty_labels import pretty_labels

if TYPE_CHECKING:
    from pymatgen.electronic_structure.bandstructure import BandStructureSymmLine
    from pymatgen.electronic_structure.dos import CompleteDos

# Author: Jason Munro, Janosh Riebesell
# Contact: jmunro@lbl.gov, janosh@lbl.gov


# TODOs:
# - look for additional projection methods in phonon DOS (currently only atom
#   projections supported)
# - indicate presence of imaginary frequencies in summary tables
# - highlight high symmetry points in Brillouin zone when hovering corresponding section
#   of bandstructure and vice versa


class PhononBandstructureAndDosComponent(MPComponent):
    def __init__(
        self,
        mpid: str | None = None,
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
        state = {"label-select": "sc", "dos-select": "ap"}

        bs, dos = PhononBandstructureAndDosComponent._get_ph_bs_dos(
            self.initial_data["default"]
        )
        fig = PhononBandstructureAndDosComponent.get_figure(bs, dos)
        # Main plot
        graph = dcc.Graph(
            figure=fig,
            config={"displayModeBar": False},
            responsive=True,
            id=self.id("ph-bsdos-graph"),
        )

        # Brillouin zone
        zone_scene = self.get_brillouin_zone_scene(bs)
        zone = CrystalToolkitScene(data=zone_scene.to_json(), sceneSize="500px")

        # Hide by default if not loaded by mpid, switching between k-paths
        # on-the-fly only supported for bandstructures retrieved from MP
        show_path_options = bool(self.initial_data["default"]["mpid"])

        options = [
            {"label": "Latimer-Munro", "value": "lm"},
            {"label": "Hinuma et al.", "value": "hin"},
            {"label": "Setyawan-Curtarolo", "value": "sc"},
        ]
        # Convention selection for band structure
        convention = html.Div(
            [
                self.get_choice_input(
                    kwarg_label="path-convention",
                    state=state,
                    label="Path convention",
                    help_str="Convention to choose path in k-space",
                    options=options,
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
                    options=options,
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

        summary_dict = self._get_data_list_dict(bs, dos)
        summary_table = get_data_list(summary_dict)

        return {
            "graph": graph,
            "convention": convention,
            "dos-select": dos_select,
            "label-select": label_select,
            "zone": zone,
            "table": summary_table,
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
    def _get_ph_bs_dos(
        data: dict[str, Any] | None
    ) -> tuple[PhononBandStructureSymmLine, CompletePhononDos]:
        data = data or {}

        # this component can be loaded either from mpid or
        # directly from BandStructureSymmLine or CompleteDos objects
        # if mpid is supplied, it takes precedence

        mpid = data.get("mpid")
        bandstructure_symm_line = data.get("bandstructure_symm_line")
        density_of_states = data.get("density_of_states")

        if not mpid and (bandstructure_symm_line is None or density_of_states is None):
            return None, None

        if mpid:
            with MPRester() as mpr:
                try:
                    bandstructure_symm_line = (
                        mpr.get_phonon_bandstructure_by_material_id(mpid)
                    )
                except Exception as exc:
                    print(exc)
                    bandstructure_symm_line = None

                try:
                    density_of_states = mpr.get_phonon_dos_by_material_id(mpid)
                except Exception as exc:
                    print(exc)
                    density_of_states = None

        else:
            if bandstructure_symm_line and isinstance(bandstructure_symm_line, dict):
                bandstructure_symm_line = PhononBandStructureSymmLine.from_dict(
                    bandstructure_symm_line
                )

            if density_of_states and isinstance(density_of_states, dict):
                density_of_states = CompletePhononDos.from_dict(density_of_states)

        return bandstructure_symm_line, density_of_states

    @staticmethod
    def get_brillouin_zone_scene(bs: PhononBandStructureSymmLine) -> Scene:
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
        for qpt in bs.qpoints:
            if qpt.label:
                label = qpt.label
                for orig, new in pretty_labels.items():
                    label = label.replace(orig, new)
                labels[label] = bz_lattice.get_cartesian_coords(qpt.frac_coords)
        label_list = [
            Spheres(positions=[coords], tooltip=label, radius=0.03, color="#5EB1BF")
            for label, coords in labels.items()
        ]

        path = []
        cylinder_pairs = []
        for b in bs.branches:
            start = bz_lattice.get_cartesian_coords(
                bs.qpoints[b["start_index"]].frac_coords
            )
            end = bz_lattice.get_cartesian_coords(
                bs.qpoints[b["end_index"]].frac_coords
            )
            path += [start, end]
            cylinder_pairs += [[start, end]]
        # path_lines = Lines(positions=path, color="#ff4b5c")
        path_lines = Cylinders(
            positionPairs=cylinder_pairs, color="#5EB1BF", radius=0.01
        )
        ibz_region = Convex(positions=path, opacity=0.2, color="#5EB1BF")

        contents = [zone_lines, zone_surface, path_lines, ibz_region, *label_list]

        return Scene(name="brillouin_zone", contents=contents)

    @staticmethod
    def get_ph_bandstructure_traces(bs, freq_range):
        bs_reg_plot = PhononBSPlotter(bs)

        bs_data = bs_reg_plot.bs_plot_data()

        bands = []
        for band_num in range(bs.nb_bands):
            for segment in bs_data["frequency"]:
                if any(v <= freq_range[1] for v in segment[band_num]) and any(
                    v >= freq_range[0] for v in segment[band_num]
                ):
                    bands.append(band_num)  # noqa: PERF401

        bs_traces = []

        for d, dist_val in enumerate(bs_data["distances"]):
            x_dat = dist_val

            traces_for_segment = []

            segment = bs_data["frequency"][d]

            traces_for_segment += [
                {
                    "x": x_dat,
                    "y": segment[band_num],
                    "mode": "lines",
                    "line": {"color": "#1f77b4"},
                    "hoverinfo": "skip",
                    "name": "Total",
                    "hovertemplate": "%{y:.2f} THz",
                    "showlegend": False,
                    "xaxis": "x",
                    "yaxis": "y",
                }
                for band_num in bands
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
                    "y": freq_range,
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

        return bs_traces, bs_data

    @staticmethod
    def _get_data_list_dict(
        bs: PhononBandStructureSymmLine, dos: CompletePhononDos
    ) -> dict[str, str | bool | int]:
        bs_minpoint, bs_min_freq = bs.min_freq()
        min_freq_report = (
            f"{bs_min_freq:.2f} THz at frac. coords. {bs_minpoint.frac_coords}"
        )
        if bs_minpoint.label is not None:
            label = f" ({bs_minpoint.label})"
            for orig, new in pretty_labels.items():
                label = label.replace(orig, new)
            min_freq_report += label

        f" at q-point=${bs_minpoint.label}$ (frac. coords. = {bs_minpoint.frac_coords})"

        summary_dict: dict[str, str | bool | int] = {
            "Number of bands": f"{bs.nb_bands:,}",
            "Number of q-points": f"{bs.nb_qpoints:,}",
            # for NAC see https://phonopy.github.io/phonopy/formulation.html#non-analytical-term-correction
            "Has NAC (see phonopy docs)": bs.has_nac,
            "Has imaginary frequencies": bs.has_imaginary_freq(),
            "Has eigen-displacements": bs.has_eigendisplacements,
            "Min frequency": min_freq_report,
            "max frequency": f"{max(dos.frequencies):.2f} THz",
        }

        return summary_dict

    @staticmethod
    def get_ph_dos_traces(dos: CompletePhononDos, freq_range: tuple[float, float]):
        dos_traces = []

        dos_max = np.abs(dos.frequencies - freq_range[1]).argmin()
        dos_min = np.abs(dos.frequencies - freq_range[0]).argmin()

        tdos_label = "Total DOS"

        # Total DOS
        trace_tdos = {
            "x": dos.densities[dos_min:dos_max],
            "y": dos.frequencies[dos_min:dos_max],
            "mode": "lines",
            "name": tdos_label,
            "line": go.scatter.Line(color="#444444"),
            "fill": "tozerox",
            "fillcolor": "#C4C4C4",
            "legendgroup": "spinup",
            "xaxis": "x2",
            "yaxis": "y2",
        }

        dos_traces.append(trace_tdos)

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

        ele_dos = dos.get_element_dos()  # project DOS onto elements
        for label in ele_dos:
            spin_up_label = str(label)

            trace = {
                "x": ele_dos[label].densities[dos_min:dos_max],
                "y": dos.frequencies[dos_min:dos_max],
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
        ph_bs: PhononBandStructureSymmLine | None = None,
        ph_dos: CompletePhononDos | None = None,
        freq_range: tuple[float | None, float | None] = (None, None),
    ) -> go.Figure:
        if freq_range[0] is None:
            freq_range = (np.min(ph_bs.bands) * 1.05, freq_range[1])

        if freq_range[1] is None:
            freq_range = (freq_range[0], np.max(ph_bs.bands) * 1.05)

        if (not ph_dos) and (not ph_bs):
            empty_plot_style = {
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
            }

            return go.Figure(layout=empty_plot_style)

        if ph_bs:
            (
                bs_traces,
                bs_data,
            ) = PhononBandstructureAndDosComponent.get_ph_bandstructure_traces(
                ph_bs, freq_range=freq_range
            )

        if ph_dos:
            dos_traces = PhononBandstructureAndDosComponent.get_ph_dos_traces(
                ph_dos, freq_range=freq_range
            )

        # TODO: add logic to handle if bs_traces and/or dos_traces not present

        rmax = max(
            [
                max(dos_traces[0]["x"]),
                abs(min(dos_traces[0]["x"])),
                max(dos_traces[1]["x"]),
                abs(min(dos_traces[1]["x"])),
            ]
        )

        # -- Add trace data to plots

        in_common_axis_styles = dict(
            gridcolor="white",
            linecolor="rgb(71,71,71)",
            linewidth=2,
            showgrid=False,
            showline=True,
            tickfont=dict(size=16),
            ticks="inside",
            tickwidth=2,
        )

        xaxis_style = dict(
            **in_common_axis_styles,
            tickmode="array",
            mirror=True,
            range=[0, bs_data["ticks"]["distance"][-1]],
            ticktext=bs_data["ticks"]["label"],
            tickvals=bs_data["ticks"]["distance"],
            title=dict(text="Wave Vector", font=dict(size=16)),
            zeroline=False,
        )

        yaxis_style = dict(
            **in_common_axis_styles,
            mirror="ticks",
            range=freq_range,
            title=dict(text="Frequency (THz)", font=dict(size=16)),
            zeroline=True,
            zerolinecolor="white",
            zerolinewidth=2,
        )

        xaxis_style_dos = dict(
            **in_common_axis_styles,
            title=dict(text="Density of States", font=dict(size=16)),
            zeroline=False,
            mirror=True,
            range=[0, rmax * 1.1],
            zerolinecolor="white",
            zerolinewidth=2,
        )

        yaxis_style_dos = dict(
            **in_common_axis_styles,
            zeroline=True,
            showticklabels=False,
            mirror="ticks",
            zerolinewidth=2,
            range=freq_range,
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
            # clickmode="event+select"
        )

        figure = {"data": bs_traces + dos_traces, "layout": layout}

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

        return figure

    def generate_callbacks(self, app, cache) -> None:
        @app.callback(
            Output(self.id("ph-bsdos-graph"), "figure"),
            Input(self.id("traces"), "data"),
        )
        def update_graph(traces):
            if traces == "error":
                msg_body = MessageBody(
                    dcc.Markdown(
                        "Band structure and density of states not available for this selection."
                    )
                )
                return (MessageContainer([msg_body], kind="warning"),)

            if traces is None:
                raise PreventUpdate

            bs, dos = self._get_ph_bs_dos(self.initial_data["default"])

            figure = self.get_figure(bs, dos)
            return dcc.Graph(
                figure=figure, config={"displayModeBar": False}, responsive=True
            )

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
                            "label": "Orbital Projected - " + str(ele_label),
                            "value": "orb" + str(ele_label),
                        }
                        for ele_label in elements
                    ]
                )

                path_options = [{"label": "N/A", "value": "sc"}]
                path_style = {"maxWidth": "200", "display": "none"}

                return dos_options, path_options, path_style
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
        def bs_dos_data(data, dos_select, label_select):
            # Obtain bands to plot over and generate traces for bs data:
            energy_window = (-6.0, 10.0)

            traces = []

            bsml, density_of_states = self._get_ph_bs_dos(data)

            if self.bandstructure_symm_line:
                bs_traces = self.get_ph_bandstructure_traces(
                    bsml, freq_range=energy_window
                )
                traces.append(bs_traces)

            if self.density_of_states:
                dos_traces = self.get_ph_dos_traces(
                    density_of_states, freq_range=energy_window
                )
                traces.append(dos_traces)

            # traces = [bs_traces, dos_traces, bs_data]

            # TODO: not tested if this is correct way to get element list
            elements = list(map(str, density_of_states.get_element_dos()))

            return traces, elements

        @app.callback(
            Output(self.id("brillouin-zone"), "data"),
            Input(self.id("ph-bsdos-graph"), "hoverData"),
            Input(self.id("ph-bsdos-graph"), "clickData"),
        )
        def highlight_bz_on_hover_bs(hover_data, click_data, label_select):
            """Highlight the corresponding point/edge of the Brillouin Zone when hovering the band
            structure plot.
            """
            # TODO: figure out what to return (CSS?) to highlight BZ edge/point
            return

            # TODO: figure out what to return (CSS?) to highlight BZ edge/point
            return


class PhononBandstructureAndDosPanelComponent(PanelComponent):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.bs = PhononBandstructureAndDosComponent()
        self.bs.attach_from(self, this_store_name="mpid")

    @property
    def title(self) -> str:
        return "Band Structure and Density of States"

    @property
    def description(self) -> str:
        return (
            "Display the band structure and density of states for this structure "
            "if it has been calculated by the Materials Project."
        )

    @property
    def initial_contents(self) -> html.Div:
        return html.Div(
            [
                super().initial_contents,
                html.Div([self.bs.standard_layout], style={"display": "none"}),
            ]
        )

    def update_contents(self, new_store_contents, *args) -> html.Div:
        return self.bs.standard_layout
