import itertools

import numpy as np
import plotly.graph_objs as go
import plotly.subplots as tls
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

from dash_mp_components import CrystalToolkitScene
from pymatgen.ext.matproj import MPRester
from pymatgen.core.periodic_table import Element
from pymatgen.phonon.bandstructure import PhononBandStructureSymmLine
from pymatgen.phonon.dos import CompletePhononDos
from pymatgen.phonon.plotter import PhononBSPlotter

from crystal_toolkit.core.scene import Scene, Lines, Spheres, Convex, Cylinders
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import *

# Author: Jason Munro
# Contact: jmunro@lbl.gov


class PhononBandstructureAndDosComponent(MPComponent):
    def __init__(
        self,
        mpid=None,
        bandstructure_symm_line=None,
        density_of_states=None,
        id=None,
        **kwargs,
    ):

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
    def _sub_layouts(self):

        # defaults
        state = {"label-select": "sc", "dos-select": "ap"}

        bs, dos = PhononBandstructureAndDosComponent._get_ph_bs_dos(self.initial_data["default"])
        fig = PhononBandstructureAndDosComponent.get_figure(bs, dos)
        # Main plot
        graph = Loading(
            [dcc.Graph(figure=fig, config={"displayModeBar": False}, responsive=True,)],
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
                        {"label": "Setyawan-Curtarolo", "value": "sc",},
                    ],
                )
            ],
            style={"width": "200px"}
            if show_path_options
            else {"max-width": "200", "display": "none"},
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
                        {"label": "Setyawan-Curtarolo", "value": "sc",},
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

    def layout(self):
        return html.Div(
            [
                Columns([Column([self._sub_layouts["graph"]])]),
                Columns(
                    [
                        Column(
                            [
                                self._sub_layouts["convention"],
                                self._sub_layouts["label-select"],
                                self._sub_layouts["dos-select"],
                            ]
                        )
                    ]
                ),
                Columns(
                    [
                        Column([Label("Summary"), self._sub_layouts["table"]]),
                        Column([Label("Brillouin Zone"), self._sub_layouts["zone"]]),
                    ]
                ),
            ]
        )

    @staticmethod
    def _get_ph_bs_dos(data):

        data = data or {}

        # this component can be loaded either from mpid or
        # directly from BandStructureSymmLine or CompleteDos objects
        # if mpid is supplied, this is preferred

        mpid = data.get("mpid")
        bandstructure_symm_line = data.get("bandstructure_symm_line")
        density_of_states = data.get("density_of_states")

        if not mpid and (bandstructure_symm_line is None or density_of_states is None):
            return None, None

        if mpid:

            with MPRester() as mpr:

                try:
                    bandstructure_symm_line = mpr.get_phonon_bandstructure_by_material_id(mpid)
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

        # - Strip latex math wrapping for labels
        # TODO: add to string utils in pymatgen
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

        labels = {}
        for k in bs.qpoints:
            if k.label:
                label = k.label
                for orig, new in str_replace.items():
                    label = label.replace(orig, new)
                labels[label] = bz_lattice.get_cartesian_coords(k.frac_coords)
        labels = [
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
        # path_lines = Lines(positions=path, color="#ff4b5c",)
        path_lines = Cylinders(
            positionPairs=cylinder_pairs, color="#5EB1BF", radius=0.01
        )
        ibz_region = Convex(positions=path, opacity=0.2, color="#5EB1BF")

        contents = [zone_lines, zone_surface, path_lines, ibz_region, *labels]

        return Scene(name="brillouin_zone", contents=contents)

    @staticmethod
    def get_ph_bandstructure_traces(bs, freq_range):

        bs_reg_plot = PhononBSPlotter(bs)

        bs_data = bs_reg_plot.bs_plot_data()

        bands = []
        for band_num in range(bs.nb_bands):
            for segment in bs_data["frequency"]:
                if any([v <= freq_range[1] for v in segment[band_num]]) and any(
                     [v >= freq_range[0] for v in segment[band_num]]
                ):
                    bands.append(band_num)

        bstraces = []

        bar_loc = []

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

            bstraces += traces_for_segment

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

        for entry_num in range(len(bs_data["ticks"]["label"])):
            for key in str_replace.keys():
                if key in bs_data["ticks"]["label"][entry_num]:
                    bs_data["ticks"]["label"][entry_num] = bs_data["ticks"]["label"][
                        entry_num
                    ].replace(key, str_replace[key])

        # Vertical lines for disjointed segments
        for dist_val, tick_label in zip(bs_data["ticks"]["distance"], bs_data["ticks"]["label"]): 
            vert_trace = [
                    {
                        "x": [dist_val, dist_val],
                        "y": freq_range,
                        "mode": "lines",
                        "marker": {"color": "#F5F5F5" if "|" not in tick_label else "white"},
                        "line": {"width": 0.5 if "|" not in tick_label else 2},
                        "hoverinfo": "skip",
                        "showlegend": False,
                        "xaxis": "x",
                        "yaxis": "y",
                    } 
                ]
    
            bstraces += vert_trace


        return bstraces, bs_data

    @staticmethod
    def _get_data_list_dict(bs, dos):

        return {}

    @staticmethod
    def get_ph_dos_traces(dos, freq_range):

        dostraces = []

        dos_max = np.abs((dos.frequencies - freq_range[1])).argmin()
        dos_min = np.abs((dos.frequencies - freq_range[0])).argmin()
    
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

        dostraces.append(trace_tdos)

        ele_dos = dos.get_element_dos()
        elements = [str(entry) for entry in ele_dos.keys()]

    
        proj_data = ele_dos

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
            
            spin_up_label = str(label)

            trace = {
                "x": proj_data[label].densities[dos_min:dos_max],
                "y": dos.frequencies[dos_min:dos_max],
                "mode": "lines",
                "name": spin_up_label,
                "line": dict(width=2, color=colors[count]),
                "xaxis": "x2",
                "yaxis": "y2",
            }

            dostraces.append(trace)

            count += 1

        return dostraces

    @staticmethod
    def get_figure(ph_bs, ph_dos, freq_range=(None, None)):
    
        y_range = list(freq_range)
  
        if freq_range[0] is None:
            y_range[0] = np.min(ph_bs.bands)*1.05
            
        if freq_range[1] is None:
            y_range[1] = np.max(ph_bs.bands)*1.05

        if (not ph_dos) and (not ph_bs):

            empty_plot_style = {
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
            }

            return go.Figure(layout=empty_plot_style)

        if ph_bs:
            bstraces, bs_data = PhononBandstructureAndDosComponent.get_ph_bandstructure_traces(
                ph_bs, freq_range=y_range
            )

        if ph_dos:
            dostraces = PhononBandstructureAndDosComponent.get_ph_dos_traces(ph_dos, freq_range=y_range)

        # TODO: add logic to handle if bstraces and/or dostraces not present

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
            title=dict(text="Frequency (THz)", font=dict(size=16)),
            tickfont=dict(size=16),
            showgrid=False,
            showline=True,
            zeroline=True,
            mirror="ticks",
            ticks="inside",
            linewidth=2,
            tickwidth=2,
            zerolinewidth=2,
            range=y_range,
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
            range=[0, rmax * 1.1,],
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
            range=y_range,
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
            # clickmode="event+select"
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

        return figure

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

            figure = self.get_figure(bs, dos)

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
                Input(self.id(), "data"),
                Input(self.id("path-convention"), "value"),
                Input(self.id("dos-select"), "value"),
                Input(self.id("label-select"), "value"),
            ],
        )
        def bs_dos_data(
            data, dos_select, label_select,
        ):

            # Obtain bands to plot over and generate traces for bs data:
            energy_window = (-6.0, 10.0)

            traces = []

            if bandstructure_symm_line:
                bstraces = get_bandstructure_traces(
                    bsml, freq_range=energy_window
                )
                traces.append(bstraces)

            if density_of_states:
                dostraces = get_dos_traces(
                    density_of_states, freq_range=energy_window)
                traces.append(dostraces)

            # traces = [bstraces, dostraces, bs_data]

            return (traces, elements)


class PhononBandstructureAndDosPanelComponent(PanelComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bs = PhononBandstructureAndDosComponent()
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
