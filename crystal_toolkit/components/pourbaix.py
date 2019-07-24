import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objs as go
import plotly.figure_factory as ff
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import numpy as np
import re
from pymatgen import MPRester
from pymatgen.core.composition import Composition
from pymatgen.analysis.pourbaix_diagram import PourbaixDiagram, ELEMENTS_HO

from crystal_toolkit.helpers.layouts import Columns, Column, MessageContainer, \
    MessageBody # layout helpers like `Columns` etc. (most subclass html.Div)
from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent


__author__ = "Joseph Montoya"
__email__ = "joseph.montoya@tri.global"


# TODO: fix bug for Pa, etc.

SUPPORTED_N_ELEMENTS = 3


class PourbaixDiagramComponent(MPComponent):
    def __init__(self, pourbaix_diagram=None, **kwargs):
        super().__init__(**kwargs)
        self.create_store("mpid")
        self.create_store("struct")
        self.create_store("figure")
        self.create_store("pourbaix_entries")
        self.create_store("pourbaix_options")
        for index in range(SUPPORTED_N_ELEMENTS):
            self.create_store("concentration-slider-{}".format(index))
            self.create_store("concentration-slider-{}-div".format(index))

        self.create_store("conc_dict")
        self.create_store("pourbaix_diagram", initial_data=self.to_data(pourbaix_diagram))


    default_plot_style = dict(
        xaxis={
            "title": "pH",
            "anchor": "y",
            "mirror": "ticks",
            "showgrid": False,
            "showline": True,
            "side": "bottom",
            "tickfont": {"size": 16.0},
            "ticks": "inside",
            "titlefont": {"color": "#000000", "size": 24.0},
            "type": "linear",
            "zeroline": False,
            "range": [-2, 16]
        },
        yaxis={
            "title": "Applied Potential (V vs. SHE)",
            "anchor": "x",
            "mirror": "ticks",
            "range": [-2, 4],
            "showgrid": False,
            "showline": True,
            "side": "left",
            "tickfont": {"size": 16.0},
            "ticks": "inside",
            "titlefont": {"color": "#000000", "size": 24.0},
            "type": "linear",
            "zeroline": False,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=550,
        width=500,
        hovermode="closest",
        showlegend=True,
        legend=dict(
            orientation="h",
            traceorder="reversed",
            x=1.0,
            y=1.08,
            xanchor="right",
            tracegroupgap=5,
        ),
        margin=dict(l=80, b=70, t=10, r=20),
    )

    empty_plot_style = {
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
    }

    colorscale = [
        [0.0, "#008d00"],
        [0.1111111111111111, "#4b9f3f"],
        [0.2222222222222222, "#73b255"],
        [0.3333333333333333, "#97c65b"],
        [0.4444444444444444, "#b9db53"],
        [0.5555555555555556, "#ffdcdf"],
        [0.6666666666666666, "#ffb8bf"],
        [0.7777777777777778, "#fd92a0"],
        [0.8888888888888888, "#f46b86"],
        [1.0, "#e24377"],
    ]

    default_table_params = [
        {"col": "Material ID", "edit": False},
        {"col": "Formula", "edit": True},
        {"col": "Formation Energy (eV/atom)", "edit": True},
        {"col": "Energy Above Hull (eV/atom)", "edit": False},
        {"col": "Predicted Stable?", "edit": False},
    ]

    empty_row = {
        "Material ID": None,
        "Formula": "INSERT",
        "Formation Energy (eV/atom)": "INSERT",
        "Energy Above Hull (eV/atom)": None,
        "Predicted Stable": None,
    }

    # TODO: why both plotter and pd
    def figure_layout(self, pourbaix_diagram, pourbaix_options):
        """

        Args:
            pourbaix_diagram (PourbaixDiagram): pourbaix diagram to plot
            pourbaix_options (list): list of pourbaix options

        Returns:
            (dict) figure layout

        """

        shapes = []
        annotations = []

        show_heatmap = "show_heatmap" in (pourbaix_options or [])

        for entry, vertices in pourbaix_diagram._stable_domain_vertices.items():
            formula = entry.name
            clean_formula = self.clean_formula(formula)

            # Info on SVG paths: https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths
            # Move to first point
            path = "M {},{}".format(*vertices[0])
            # Draw lines to each other point
            path += "".join(["L {},{}".format(*vertex) for vertex in vertices[1:]])
            # Close path
            path += "Z"

            # Fill with turquoise if solution
            if not show_heatmap:
                fillcolor = "White" if "Ion" in entry.phase_type else "PaleTurquoise"
            else:
                fillcolor = None

            shape = go.layout.Shape(
                type="path",
                path=path,
                fillcolor=fillcolor,
                line_color="Black"
            )
            shapes.append(shape)

            # Generate annotation
            if "show_labels" in (pourbaix_options or []):
                x, y = np.average(vertices, axis=0)
                annotation = {
                    "align": "center",
                    "font": {"color": "#000000", "size": 15.0},
                    "opacity": 1,
                    "showarrow": False,
                    "text": clean_formula,
                    "x": x,
                    "xanchor": "center",
                    "yanchor": "auto",
                    "xshift": -10,
                    "yshift": -10,
                    "xref": "x",
                    "y": y,
                    "yref": "y",
                }

                annotations.append(annotation)
        layout = self.default_plot_style
        layout.update({"shapes": shapes,
                       "annotations": annotations,
                       })

        return layout

    # TODO: format formula
    @staticmethod
    def clean_formula(formula):
        # Superscript charges
        clean_formula = re.sub(r"\[([0-9+-]+)\]", r"<sup>\1</sup>", formula)

        # Subscript coefficients
        clean_formula = re.sub(r"([A-Za-z\(\)])([\d\.]+)", r"\1<sub>\2</sub>", clean_formula)
        return clean_formula

    @property
    def all_layouts(self):

        options = html.Div(
            [
                dcc.Checklist(
                    options=[{"label": "Show heatmap", "value": "show_heatmap"},
                             {"label": "Show labels", "value": "show_labels"},
                             {"label": "Filter solids", "value": "filter_solids"}
                             ],
                    value = ["filter_solids", "show_labels"],
                    id=self.id("pourbaix_options")
                )
            ]
        )

        graph = html.Div(
            [
                dcc.Graph(
                    figure=go.Figure(layout=PourbaixDiagramComponent.empty_plot_style),
                    id=self.id("graph"),
                    config={"displayModeBar": False, "displaylogo": False},
                )
            ],
            id=self.id("pourbaix-div"),
        )

        sliders = html.Div(
            [
                html.Div(
                    children=[
                        html.Div(
                            "concentration_{}".format(n),
                            id=self.id("concentration_{}_text".format(n))
                        ),
                        dcc.Slider(
                            id=self.id("concentration-slider-{}".format(n)),
                            min=-8,
                            max=1,
                            step=1,
                            value=-4,
                        ),
                    ],
                    id=self.id("concentration-slider-{}-div".format(n)),
                    style={"display": "none"}
                )
                for n in range(SUPPORTED_N_ELEMENTS)
            ],
            id=self.id("slider-div"),
        )

        return {"graph": graph, "options": options, "sliders": sliders}

    @property
    def standard_layout(self):
        return html.Div(
            children=[
                self.all_layouts["options"],
                self.all_layouts["sliders"],
                self.all_layouts["graph"]
            ]
        )

    def generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("pourbaix-div"), "children"), [Input(self.id("figure"), "data")]
        )
        def update_graph(figure):
            if figure is None:
                raise PreventUpdate
            elif figure == "too_many_elements":
                search_error = (
                    MessageContainer(
                        [
                            MessageBody(
                                dcc.Markdown(
                                    "Pourbaix diagrams may only be calculated for materials "
                                    "with {} or fewer non-OH elements".format(SUPPORTED_N_ELEMENTS)
                                )
                            )
                        ],
                        kind="warning",
                    ),
                )
                return search_error

            else:
                plot = [
                    dcc.Graph(
                        figure=figure,
                        config={"displayModeBar": False, "displaylogo": False},
                    )
                ]
                return plot

        @app.callback(Output(self.id("figure"), "data"),
                      [Input(self.id("pourbaix_diagram"), "data"),
                       Input(self.id("pourbaix_options"), "value"),
                       Input(self.id("pourbaix_entries"), "data"),
                       Input(self.id("struct"), "data")
                       ])
        def make_figure(pourbaix_diagram,
                        pourbaix_options,
                        pourbaix_entries,
                        struct
                        ):
            if pourbaix_entries == "too_many_elements":
                return "too_many_elements"

            if pourbaix_diagram is None:
                raise PreventUpdate

            pourbaix_diagram = self.from_data(pourbaix_diagram)
            pourbaix_entries = self.from_data(pourbaix_entries)


            # TODO: fix mpid problem.  Can't attach from mpid without it being a structure.
            if "show_heatmap" in (pourbaix_options or []):
                struct = self.from_data(struct)
                with MPRester() as mpr:
                    # Should probably enable fetching pourbaix entry
                    # by mpid in MPRester
                    heatmap_id = mpr.find_structure(struct)[0]

                # Find entry
                entry = [entry for entry in pourbaix_entries
                         if heatmap_id in entry.entry_id][0]
                ph_range = np.arange(-2, 16.001, 0.1)
                v_range = np.arange(-2, 4.001, 0.1)
                ph_mesh, v_mesh = np.meshgrid(ph_range, v_range)
                decomposition_e = pourbaix_diagram.get_decomposition_energy(entry, ph_mesh, v_mesh)

                # Generate hoverinfo
                hovertexts = []
                for ph_val, v_val, de_val in zip(ph_mesh.ravel(), v_mesh.ravel(), decomposition_e.ravel()):
                    hovertext = ["∆G<sub>pbx</sub>={:.2f}".format(de_val),
                                 "ph={:.2f}".format(ph_val),
                                 "V={:.2f}".format(v_val)]
                    hovertext = "<br>".join(hovertext)
                    hovertexts.append(hovertext)
                hovertexts = np.reshape(hovertexts, list(decomposition_e.shape))

                # Enforce decomposition limit energy
                decomposition_e = np.min([decomposition_e, np.ones(decomposition_e.shape)], axis=0)

                # Plotly needs a list here for validation
                hmap = go.Heatmap(x=list(ph_range), y=list(v_range), z=decomposition_e,
                                                   text=hovertexts, hoverinfo='text',
                                                   colorbar={"title": "∆G<sub>pbx</sub> (eV/atom)",
                                                             "titleside": "right"},
                                                   colorscale="Viridis")

            else:
                hmap = None

            fig = go.Figure(data=hmap)
            fig.layout = self.figure_layout(pourbaix_diagram,
                                            pourbaix_options)

            return fig

        @app.callback(Output(self.id("pourbaix_diagram"), "data"),
                      [Input(self.id("pourbaix_entries"), "data"),
                       Input(self.id("pourbaix_options"), "value"),
                       Input(self.id("conc_dict"), "data"),
                       Input(self.id("struct"), "data")
                       ])
        def create_pbx_object(pourbaix_entries,
                              pourbaix_options,
                              conc_dict,
                              struct
                              ):
            # Pass along element restriction
            if pourbaix_entries == "too_many_elements":
                return "too_many_elements"

            self.logger.debug("Updating entries")
            if pourbaix_entries is None or not pourbaix_entries:
                self.logger.debug("Preventing updating entries")
                raise PreventUpdate

            pourbaix_entries = self.from_data(pourbaix_entries)

            # filter_solids = True
            if pourbaix_options is not None:
                filter_solids = "filter_solids" in pourbaix_options
            else:
                filter_solids = True

            # Get composition from structure
            struct = self.from_data(struct)
            comp_dict = {str(elt): coeff for elt, coeff in struct.composition.items()
                         if elt not in ELEMENTS_HO}
            if conc_dict is not None:
                conc_dict = self.from_data(conc_dict)

            pourbaix_diagram = PourbaixDiagram(pourbaix_entries, comp_dict=comp_dict,
                                               conc_dict=conc_dict, filter_solids=filter_solids)
            self.logger.debug("Generated pourbaix diagram")
            return self.to_data(pourbaix_diagram)

        # Add arbitrary chemsys?
        @app.callback(
            Output(self.id("pourbaix_entries"), "data"),
            [
                Input(self.id("mpid"), "data"),
                Input(self.id("struct"), "data"),
            ],
        )
        def get_chemsys_from_struct_mpid(mpid, struct):
            print("other callback")
            ctx = dash.callback_context

            if ctx is None or not ctx.triggered:
                raise PreventUpdate

            trigger = ctx.triggered[0]

            if trigger["value"] is None:
                raise PreventUpdate

            # mpid trigger
            if trigger["prop_id"] == self.id("mpid") + ".data":
                with MPRester() as mpr:
                    entry = mpr.get_entry_by_material_id(mpid)

                chemsys = [str(elem) for elem in entry.composition.elements]

            # struct trigger
            if trigger["prop_id"] == self.id("struct") + ".data":
                chemsys = [
                    str(elem) for elem in self.from_data(struct).composition.elements
                ]
            if len(set(chemsys) - {"O", "H"}) > SUPPORTED_N_ELEMENTS:
                return "too_many_elements"

            with MPRester() as mpr:
                print("Chemsys is {}".format(chemsys))
                pourbaix_entries = mpr.get_pourbaix_entries(chemsys)

            return self.to_data(pourbaix_entries)

        # This is a hacked way of getting concentration, but haven't found a more sane fix
        # Basically creates 3 persistent sliders and updates the concentration according to
        # their values.  Renders only the necessary ones visible.
        @app.callback(
            [
                Output(self.id("concentration-slider-{}-div".format(index)), "style")
                for index in range(SUPPORTED_N_ELEMENTS)
            ],
            [
                Input(self.id("pourbaix_diagram"), "data"),
                Input(self.id("struct"), "data")
            ],
        )
        def reveal_sliders(pourbaix_diagram, struct):
            if struct is None:
                raise PreventUpdate
            print("updating style")
            struct = self.from_data(struct)
            pbx_elts = [elt for elt in struct.composition.keys()
                        if elt not in ELEMENTS_HO]
            print(pbx_elts)
            nelts = len(pbx_elts)
            styles = [{}] * nelts
            styles += [{"display": 'none'}] * (SUPPORTED_N_ELEMENTS - nelts)
            print(styles)
            return styles

        # @app.callback(
        #     Output(self.id("concentration-slider-2-div"), "style"),
        #     [Input(self.id("pourbaix_diagram"), "data")]
        # )
        # def hide_one_slider(pbx):
        #     print("updating style")
        #     return {"display": "none"}

        @app.callback(
            Output(self.id("conc_dict"), "data"),
            [Input(self.id("struct"), "data")] + \
            [
                Input(self.id("concentration-slider-{}".format(index)), "value")
                for index in range(SUPPORTED_N_ELEMENTS)
            ],
        )
        def update_conc_dict(struct, *args):
            print("updating concentration")
            if args[0] is None:
                print("no concentration")
                raise PreventUpdate

            struct = self.from_data(struct)
            pbx_elts = sorted([str(elt) for elt in struct.composition.keys()
                               if elt not in ELEMENTS_HO])
            conc_dict = {k: 10 ** arg for k, arg
                         in zip(pbx_elts, args[:len(pbx_elts)])}
            print(conc_dict)
            return self.to_data(conc_dict)


class PourbaixDiagramPanelComponent(PanelComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pourbaix_component = PourbaixDiagramComponent()
        self.pourbaix_component.attach_from(self, this_store_name="struct")

    @property
    def title(self):
        return "Pourbaix Diagram"

    @property
    def description(self):
        return (
            "Display the pourbaix diagram for the"
            " chemical system containing this structure (fewer than 3 non-OH species)."
        )

    def update_contents(self, new_store_contents, *args):
        return self.pourbaix_component.standard_layout
