from __future__ import annotations

import itertools
from copy import deepcopy
from typing import TYPE_CHECKING, Any

import numpy as np
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Component, Input, Output, State
from dash.exceptions import PreventUpdate
from dash_mp_components import CrystalToolkitAnimationScene, CrystalToolkitScene

# crystal animation algo
from pymatgen.analysis.graphs import StructureGraph
from pymatgen.analysis.local_env import CrystalNN
from pymatgen.ext.matproj import MPRester
from pymatgen.phonon.bandstructure import PhononBandStructureSymmLine
from pymatgen.phonon.dos import CompletePhononDos
from pymatgen.phonon.plotter import PhononBSPlotter
from pymatgen.transformations.standard_transformations import SupercellTransformation

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.core.scene import Convex, Cylinders, Lines, Scene, Spheres
from crystal_toolkit.helpers.layouts import Column, Columns, Label, get_data_list
from crystal_toolkit.helpers.pretty_labels import pretty_labels

if TYPE_CHECKING:
    from pymatgen.electronic_structure.bandstructure import BandStructureSymmLine
    from pymatgen.electronic_structure.dos import CompleteDos

DISPLACE_COEF = [0, 1, 0, -1, 0]
MARKER_COLOR = "red"
MARKER_SIZE = 12
MARKER_SHAPE = "x"
MAX_MAGNITUDE = 300
MIN_MAGNITUDE = 0

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

        bs, _ = PhononBandstructureAndDosComponent._get_ph_bs_dos(
            self.initial_data["default"]
        )
        self.create_store("bs-store", bs)
        self.create_store("bs", None)
        self.create_store("dos", None)

    @property
    def _sub_layouts(self) -> dict[str, Component]:
        # defaults
        state = {"label-select": "sc", "dos-select": "ap"}

        fig = PhononBandstructureAndDosComponent.get_figure(None, None)
        # Main plot
        graph = dcc.Graph(
            figure=fig,
            config={"displayModeBar": False},
            responsive=False,
            id=self.id("ph-bsdos-graph"),
        )

        # Brillouin zone
        zone_scene = self.get_brillouin_zone_scene(None)
        zone = CrystalToolkitScene(
            data=zone_scene.to_json(), sceneSize="500px", id=self.id("zone")
        )

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
            style=(
                {"width": "200px"}
                if show_path_options
                else {"maxWidth": "200", "display": "none"}
            ),
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
            style=(
                {"width": "200px"}
                if show_path_options
                else {"width": "200px", "display": "none"}
            ),
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

        summary_dict = self._get_data_list_dict(None, None)
        summary_table = get_data_list(summary_dict)

        # crystal visualization

        tip = html.H5(
            "💡 Tips: Click different q-points and bands in the dispersion diagram to see the crystal vibration!",
        )

        crystal_animation = html.Div(
            CrystalToolkitAnimationScene(
                data={},
                sceneSize="500px",
                id=self.id("crystal-animation"),
                settings={"defaultZoom": 1.2},
                axisView="SW",
                showControls=False,  # disable download for now
            ),
            style={"width": "60%"},
        )

        crystal_animation_controls = html.Div(
            [
                html.Br(),
                html.Div(tip, style={"textAlign": "center"}),
                html.Br(),
                html.H5("Control Panel", style={"textAlign": "center"}),
                html.H6("Supercell modification"),
                html.Br(),
                html.Div(
                    [
                        self.get_numerical_input(
                            kwarg_label="scale-x",
                            default=1,
                            is_int=True,
                            label="x",
                            min=1,
                            style={"width": "5rem"},
                        ),
                        self.get_numerical_input(
                            kwarg_label="scale-y",
                            default=1,
                            is_int=True,
                            label="y",
                            min=1,
                            style={"width": "5rem"},
                        ),
                        self.get_numerical_input(
                            kwarg_label="scale-z",
                            default=1,
                            is_int=True,
                            label="z",
                            min=1,
                            style={"width": "5rem"},
                        ),
                        html.Button(
                            "Update",
                            id=self.id("supercell-controls-btn"),
                            style={"height": "40px"},
                        ),
                    ],
                    style={"display": "flex"},
                ),
                html.Br(),
                html.Div(
                    self.get_slider_input(
                        kwarg_label="magnitude",
                        default=0.5,
                        step=0.01,
                        domain=[0, 1],
                        label="Vibration magnitude",
                    )
                ),
            ],
        )

        return {
            "graph": graph,
            "convention": convention,
            "dos-select": dos_select,
            "label-select": label_select,
            "zone": zone,
            "table": summary_table,
            "crystal-animation": crystal_animation,
            "tip": tip,
            "crystal-animation-controls": crystal_animation_controls,
        }

    def _get_animation_panel(self):
        sub_layouts = self._sub_layouts
        return Columns(
            [
                Column(
                    [
                        Columns(
                            [
                                sub_layouts["crystal-animation"],
                                sub_layouts["crystal-animation-controls"],
                            ]
                        )
                    ]
                ),
            ]
        )

    def layout(self) -> html.Div:
        sub_layouts = self._sub_layouts
        crystal_animation = self._get_animation_panel()
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
                Column([Label("Summary"), sub_layouts["table"]], id=self.id("table")),
                Column([Label("Brillouin Zone"), sub_layouts["zone"]]),
            ]
        )

        return html.Div([graph, crystal_animation, controls, brillouin_zone])

    @staticmethod
    def _get_eigendisplacement(
        ph_bs: BandStructureSymmLine,
        json_data: dict,
        band: int = 0,
        qpoint: int = 0,
        precision: int = 15,
        magnitude: int = MAX_MAGNITUDE / 2,
        total_repeat_cell_cnt: int = 1,
    ) -> dict:
        if not ph_bs or not json_data:
            return {}

        assert json_data["contents"][0]["name"] == "atoms"
        assert json_data["contents"][1]["name"] == "bonds"
        rdata = deepcopy(json_data)

        def calc_max_displacement(idx: int) -> list:
            """
            Retrieve the eigendisplacement for a given atom index from `ph_bs` and compute its maximum displacement.

            Parameters:
                idx (int): The atom index.

            Returns:
                list: The maximum displacement vector in the form [x_max_displacement, y_max_displacement, z_max_displacement]

            This function extracts the real component of the atom's eigendisplacement,
            scales it by the specified magnitude, and returns the resulting vector.
            """

            # get the atom index
            assert total_repeat_cell_cnt != 0

            modified_idx = (
                int(idx // total_repeat_cell_cnt) if total_repeat_cell_cnt else idx
            )

            return [
                round(complex(vec).real * magnitude, precision)
                for vec in ph_bs.eigendisplacements[band][qpoint][modified_idx]
            ]

        def calc_animation_step(max_displacement: list, coef: int) -> list:
            """
            Calculate the displacement for an animation frame based on the given coefficient.

            Parameters:
                max_displacement (list): A list of maximum displacements along each axis,
                    formatted as [x_max_displacement, y_max_displacement, z_max_displacement].
                coef (int): A coefficient indicating the motion direction.
                    - 0: no movement
                    - 1: forward movement
                    - -1: backward movement

            Returns:
                list: The displacement vector [x_displacement, y_displacement, z_displacement].

            This function generates oscillatory motion by scaling the maximum displacement
            with the provided coefficient.
            """
            return [round(coef * md, precision) for md in max_displacement]

        # Compute per-frame atomic motion.
        # `rcontent["animate"]` stores the displacement (distance difference) from the previous coordinates.
        contents0 = json_data["contents"][0]["contents"]
        for cidx, content in enumerate(contents0):
            max_displacement = calc_max_displacement(content["_meta"][0])
            rcontent = rdata["contents"][0]["contents"][cidx]
            # put animation frame to the given atom index
            rcontent["animate"] = [
                calc_animation_step(max_displacement, coef) for coef in DISPLACE_COEF
            ]
            rcontent["keyframes"] = list(range(len(DISPLACE_COEF)))
            rcontent["animateType"] = "displacement"
        # Compute per-frame bonding motion.
        # Explanation:
        # Each bond connects two atoms, `u` and `v`, represented as (u)----(v)
        # To model the bond motion, it is divided into two segments:
        # from `u` to the midpoint and from the midpoint to `v`, i.e., (u)--(mid)--(v)
        # Thus, two cylinders are created: one for (u)--(mid) and another for (v)--(mid).
        # For each cylinder, displacements are assigned to the endpoints — for example,
        # the (u)--(mid) cylinder uses:
        # [
        #   [u_x_displacement, u_y_displacement, u_z_displacement],
        #   [mid_x_displacement, mid_y_displacement, mid_z_displacement]
        # ].
        contents1 = json_data["contents"][1]["contents"]

        for cidx, content in enumerate(contents1):
            bond_animation = []
            assert len(content["_meta"]) == len(content["positionPairs"])

            for atom_idx_pair in content["_meta"]:
                max_displacements = list(
                    map(calc_max_displacement, atom_idx_pair)
                )  # max displacement for u and v

                u_to_middle_bond_animation = []

                for coef in DISPLACE_COEF:
                    # Calculate the midpoint displacement between atom u and v for each animation frame.
                    u_displacement, v_displacement = [
                        np.array(calc_animation_step(max_displacement, coef))
                        for max_displacement in max_displacements
                    ]
                    middle_end_displacement = np.add(u_displacement, v_displacement) / 2

                    u_to_middle_bond_animation.append(
                        [
                            u_displacement,  # u atom displacement
                            [
                                round(dis, precision) for dis in middle_end_displacement
                            ],  # middle point displacement
                        ]
                    )

                bond_animation.append(u_to_middle_bond_animation)

            rdata["contents"][1]["contents"][cidx]["animate"] = bond_animation
            rdata["contents"][1]["contents"][cidx]["keyframes"] = list(
                range(len(DISPLACE_COEF))
            )
            rdata["contents"][1]["contents"][cidx]["animateType"] = "displacement"

        # remove unused sense
        for i in range(2, 4):
            rdata["contents"][i]["visible"] = False

        return rdata

    @staticmethod
    def _get_ph_bs_dos(
        data: dict[str, Any] | None,
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
                    "customdata": [[di, band_num] for di in range(len(x_dat))],
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
        if (not bs) and (not dos):
            return {}

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
            Label(
                [
                    "Has ",
                    html.A(
                        "NAC",
                        href="https://phonopy.github.io/phonopy/formulation.html#non-analytical-term-correction",
                        target="blank",
                    ),
                ]
            ): ("Yes" if bs.has_nac else "No"),
            "Has imaginary frequencies": "Yes" if bs.has_imaginary_freq() else "No",
            "Has eigen-displacements": "Yes" if bs.has_eigendisplacements else "No",
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
        if isinstance(dos, CompletePhononDos):
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
            for count, label in enumerate(ele_dos):
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

        return dos_traces

    @staticmethod
    def get_figure(
        ph_bs: PhononBandStructureSymmLine | None = None,
        ph_dos: CompletePhononDos | None = None,
        freq_range: tuple[float | None, float | None] = (None, None),
    ) -> go.Figure:
        if (not ph_dos) and (not ph_bs):
            empty_plot_style = {
                "height": 500,
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
            }

            return go.Figure(layout=empty_plot_style)

        if freq_range[0] is None:
            freq_range = (np.min(ph_bs.bands) * 1.05, freq_range[1])

        if freq_range[1] is None:
            freq_range = (freq_range[0], np.max(ph_bs.bands) * 1.05)

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

        rmax_list = [
            max(dos_traces[0]["x"]),
            abs(min(dos_traces[0]["x"])),
        ]
        if len(dos_traces) > 1 and "x" in dos_traces[1] and dos_traces[1]["x"].any():
            rmax_list += [
                max(dos_traces[1]["x"]),
                abs(min(dos_traces[1]["x"])),
            ]

        rmax = max(rmax_list)

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
            clickmode="event+select",
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
            Output(self.id("zone"), "data"),
            Output(self.id("table"), "children"),
            Input(self.id("ph_bs"), "data"),
            Input(self.id("ph_dos"), "data"),
            Input(self.id("ph-bsdos-graph"), "clickData"),
        )
        def update_graph(bs, dos, nclick):
            if isinstance(bs, dict):
                bs = PhononBandStructureSymmLine.from_dict(bs)
            if isinstance(dos, dict):
                dos = CompletePhononDos.from_dict(dos)

            figure = self.get_figure(bs, dos)

            # remove marker if there is one
            figure["data"] = [
                t for t in figure["data"] if t.get("name") != "click-marker"
            ]

            x_click = nclick["points"][0]["x"] if nclick else 0
            y_click = nclick["points"][0]["y"] if nclick else 0
            pt = nclick["points"][0] if nclick else {}

            qpoint, band_num = pt.get("customdata", [0, 0])

            figure["data"].append(
                {
                    "type": "scatter",
                    "mode": "markers",
                    "x": [x_click],
                    "y": [y_click],
                    "marker": {
                        "color": MARKER_COLOR,
                        "size": MARKER_SIZE,
                        "symbol": MARKER_SHAPE,
                    },
                    "name": "click-marker",
                    "showlegend": False,
                    "customdata": [[qpoint, band_num]],
                    "hovertemplate": (
                        "band: %{customdata[1]}<br>q-point: %{customdata[0]}<br>"
                    ),
                }
            )

            zone_scene = self.get_brillouin_zone_scene(bs)

            summary_dict = self._get_data_list_dict(bs, dos)
            summary_table = get_data_list(summary_dict)

            return figure, zone_scene.to_json(), summary_table

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

        @app.callback(
            Output(self.id("crystal-animation"), "data"),
            Input(self.id("ph-bsdos-graph"), "clickData"),
            Input(self.id("ph_bs"), "data"),
            Input(self.id("supercell-controls-btn"), "n_clicks"),
            Input(self.get_kwarg_id("magnitude"), "value"),
            State(self.get_kwarg_id("scale-x"), "value"),
            State(self.get_kwarg_id("scale-y"), "value"),
            State(self.get_kwarg_id("scale-z"), "value"),
            # prevent_initial_call=True
        )
        def update_crystal_animation(
            cd, bs, sueprcell_update, magnitude_fraction, scale_x, scale_y, scale_z
        ):
            # Avoids using `get_all_kwargs_id` for all `Input`; instead, uses `State` to prevent flickering when users modify `scale_x`, `scale_y`, or `scale_z` fields,
            # ensuring updates occur only after the `supercell-controls-btn`` is clicked.

            if not bs:
                raise PreventUpdate

            # Since `self.get_kwarg_id()` uses dash.dependencies.ALL, it returns a list of values.
            # Although we could use `magnitude_fraction = magnitude_fraction[0]` to get the first value,
            # this approach provides better clarity and readability.
            kwargs = self.reconstruct_kwargs_from_state()
            magnitude_fraction = kwargs.get("magnitude")
            scale_x = kwargs.get("scale-x")
            scale_y = kwargs.get("scale-y")
            scale_z = kwargs.get("scale-z")

            if isinstance(bs, dict):
                bs = PhononBandStructureSymmLine.from_dict(bs)

            struct = bs.structure
            total_repeat_cell_cnt = 1
            # update structure if the controls got triggered
            if sueprcell_update:
                total_repeat_cell_cnt = scale_x * scale_y * scale_z

                # create supercell
                trans = SupercellTransformation(
                    ((scale_x, 0, 0), (0, scale_y, 0), (0, 0, scale_z))
                )
                struct = trans.apply_transformation(struct)

            struc_graph = StructureGraph.from_local_env_strategy(struct, CrystalNN())
            scene = struc_graph.get_scene(
                draw_image_atoms=False,
                bonded_sites_outside_unit_cell=False,
                site_get_scene_kwargs={"retain_atom_idx": True},
            )
            json_data = scene.to_json()

            qpoint = 0
            band_num = 0

            if cd and cd.get("points"):
                pt = cd["points"][0]
                qpoint, band_num = pt.get("customdata", [0, 0])

            # magnitude
            magnitude = (
                MAX_MAGNITUDE - MIN_MAGNITUDE
            ) * magnitude_fraction + MIN_MAGNITUDE

            return PhononBandstructureAndDosComponent._get_eigendisplacement(
                ph_bs=bs,
                json_data=json_data,
                band=band_num,
                qpoint=qpoint,
                total_repeat_cell_cnt=total_repeat_cell_cnt,
                magnitude=magnitude,
            )


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
