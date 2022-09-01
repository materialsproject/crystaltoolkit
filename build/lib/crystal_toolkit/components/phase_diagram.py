from typing import Optional

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from pymatgen.ext.matproj import MPRester
from pymatgen.analysis.phase_diagram import PDEntry, PDPlotter, PhaseDiagram
from pymatgen.core.composition import Composition

from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import *  # layout helpers like `Columns` etc. (most subclass html.Div)

# Author: Matthew McDermott
# Contact: mcdermott@lbl.gov


class PhaseDiagramComponent(MPComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_store("mpid")
        self.create_store("chemsys-internal")
        self.create_store("chemsys-external")
        self.create_store("figure")
        self.create_store("entries")

    # Default plot layouts for Binary (2), Ternary (3), Quaternary (4) phase diagrams
    default_binary_plot_style = dict(
        xaxis={
            "title": "Fraction",
            "anchor": "y",
            "mirror": "ticks",
            "nticks": 8,
            "showgrid": False,
            "showline": True,
            "side": "bottom",
            "tickfont": {"size": 16.0},
            "ticks": "inside",
            "titlefont": {"color": "#000000", "size": 24.0},
            "type": "linear",
            "zeroline": False,
        },
        yaxis={
            "title": "Formation energy (eV/fu)",
            "anchor": "x",
            "mirror": "ticks",
            "nticks": 7,
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

    default_ternary_plot_style = dict(
        xaxis=dict(
            title=None,
            autorange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks="",
            showticklabels=False,
        ),
        yaxis=dict(
            title=None,
            autorange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks="",
            showticklabels=False,
        ),
        autosize=True,
        height=450,
        width=500,
        hovermode="closest",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(b=30, l=30, pad=0, t=0, r=20),
        showlegend=True,
        legend=dict(
            orientation="h",
            traceorder="reversed",
            x=1.0,
            y=1.08,
            xanchor="right",
            tracegroupgap=5,
        ),
    )

    default_3d_axis = dict(
        title=None,
        visible=False,
        autorange=True,
        showgrid=False,
        zeroline=False,
        showline=False,
        ticks="",
        showaxeslabels=False,
        showticklabels=False,
        showspikes=False,
    )

    default_quaternary_plot_style = dict(
        autosize=True,
        height=450,
        hovermode="closest",
        margin=dict(b=30, l=30, pad=0, t=0, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(
            orientation="h",
            traceorder="reversed",
            x=1.0,
            y=1.08,
            xanchor="right",
            tracegroupgap=5,
        ),
        scene=dict(xaxis=default_3d_axis, yaxis=default_3d_axis, zaxis=default_3d_axis),
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

    def figure_layout(self, plotter, pd):
        dim = pd.dim

        if dim not in [2, 3, 4]:
            raise ValueError("Phase diagram must be for 2, 3, or 4 components!")

        annotations_list = []

        for coords, entry in plotter.pd_plot_data[1].items():
            x, y = coords[0], coords[1]

            if dim == 4:
                if not entry.composition.is_element:
                    continue
                else:
                    z = coords[2]

            formula = list(entry.composition.reduced_formula)

            clean_formula = self.clean_formula(formula)

            annotation = {
                "align": "center",
                "font": {"color": "#000000", "size": 20.0},
                "opacity": 1,
                "showarrow": False,
                "text": clean_formula,
                "x": x,
                "xanchor": "right",
                "yanchor": "auto",
                "xshift": -10,
                "yshift": -10,
                "xref": "x",
                "y": y,
                "yref": "y",
            }

            if dim == 3:
                annotation.update({"font": {"color": "#000000", "size": 18.0}})
            elif dim == 4:
                annotation.update({"z": z})
                for d in ["xref", "yref"]:
                    annotation.pop(d)  # Scatter3d cannot contain xref, yref

            annotations_list.append(annotation)

            if dim == 2:
                layout = self.default_binary_plot_style
                layout["annotations"] = annotations_list
            elif dim == 3:
                layout = self.default_ternary_plot_style
                layout["annotations"] = annotations_list
            elif dim == 4:
                layout = self.default_quaternary_plot_style
                layout["scene"].update(
                    {
                        "annotations": annotations_list,
                        "camera": dict(
                            up=dict(x=0, y=0, z=1),
                            center=dict(x=-0.15, y=-0.2, z=0),
                            eye=dict(x=1.25, y=1.25, z=1.25),
                        ),
                    }
                )
        return layout

    def create_markers(self, plotter, pd):
        x_list = []
        y_list = []
        z_list = []
        text = []
        energy_list = []

        dim = pd.dim

        for coord, entry in plotter.pd_plot_data[1].items():
            energy = round(pd.get_form_energy_per_atom(entry), 3)
            energy_list.append(energy)
            mpid = entry.attribute
            formula = entry.composition.reduced_formula

            clean_formula = self.clean_formula(formula)

            x_list.append(coord[0])
            y_list.append(coord[1])

            if dim == 4:
                z_list.append(coord[2])
            text.append(f"{clean_formula} ({mpid})<br> {str(energy)} eV")

        if dim == 2 or dim == 3:
            marker_plot = go.Scatter(
                x=x_list,
                y=y_list,
                mode="markers",
                name="Stable",
                marker=dict(
                    color=energy_list,
                    size=11,
                    colorscale=self.colorscale,
                    line=dict(width=2, color="#000000"),
                ),
                hoverinfo="text",
                hoverlabel=dict(font=dict(size=14)),
                showlegend=True,
                hovertext=text,
            )
        if dim == 4:
            marker_plot = go.Scatter3d(
                x=x_list,
                y=y_list,
                z=z_list,
                mode="markers",
                name="Stable",
                marker=dict(
                    color=energy_list,
                    size=8,
                    colorscale=self.colorscale,
                    line=dict(width=2, color="#000000"),
                ),
                hoverinfo="text",
                hoverlabel=dict(font=dict(size=14)),
                hovertext=text,
                showlegend=True,
            )
        return marker_plot

    def create_unstable_markers(self, plotter, pd):
        x_list = []
        y_list = []
        z_list = []
        text_list = []

        dim = pd.dim

        for (unstable_entry, unstable_coord) in plotter.pd_plot_data[2].items():
            x_list.append(unstable_coord[0])
            y_list.append(unstable_coord[1])
            if dim == 4:
                z_list.append(unstable_coord[2])

            mpid = unstable_entry.attribute
            formula = list(unstable_entry.composition.reduced_formula)
            e_above_hull = round(pd.get_e_above_hull(unstable_entry), 3)

            clean_formula = self.clean_formula(formula)

            energy = round(pd.get_form_energy_per_atom(unstable_entry), 3)
            text_list.append(
                f"{clean_formula} ({mpid})<br>" f"{energy} eV (+{e_above_hull} eV)"
            )

        if dim == 2 or dim == 3:
            unstable_marker_plot = go.Scatter(
                x=x_list,
                y=y_list,
                mode="markers",
                hoverinfo="text",
                hovertext=text_list,
                visible="legendonly",
                name="Unstable",
                marker=dict(color="#ff0000", size=12, symbol="x"),
            )

        elif dim == 4:
            unstable_marker_plot = go.Scatter3d(
                x=x_list,
                y=y_list,
                z=z_list,
                mode="markers",
                hoverinfo="text",
                hovertext=text_list,
                visible="legendonly",
                name="Unstable",
                marker=dict(color="#ff0000", size=4, symbol="x"),
            )

        return unstable_marker_plot

    @staticmethod
    def create_table_content(pd):
        data = []

        for entry in pd.all_entries:
            try:
                mpid = entry.entry_id
            except:
                mpid = entry.attribute  # accounting for custom entry

            try:
                data.append(
                    {
                        "Material ID": mpid,
                        "Formula": entry.name,
                        "Formation Energy (eV/atom)": round(
                            pd.get_form_energy_per_atom(entry), 3
                        ),
                        "Energy Above Hull (eV/atom)": round(
                            pd.get_e_above_hull(entry), 3
                        ),
                        "Predicted Stable?": (
                            "Yes" if pd.get_e_above_hull(entry) == 0 else "No"
                        ),
                    }
                )

            except:
                data.append({})
        return data

    @staticmethod
    def clean_formula(formula):
        s = []
        for char in formula:
            if char.isdigit():
                s.append(f"<sub>{char}</sub>")
            else:
                s.append(char)

        clean_formula = "".join(s)

        return clean_formula

    @staticmethod
    def ternary_plot(plot_data):
        """
        Return a ternary phase diagram in a two-dimensional plot.

        Args:
            plot_data: plot data from PDPlotter

        Returns: go.Figure
        """

        go.Scatterternary(
            {
                "mode": "markers",
                "a": list_of_a_comp,
                "b": ...,
                "c": ...,
                "text": ...,
                "marker": {
                    "symbol": 100,
                    "color": ...,
                    "size": ...,
                    "line": {"width": 2},
                },
            }
        )

        go.Scatterternary({"mode": "lines", "a": ..., "b": ..., "c": ..., "line": ...})

        go.Layout(
            {
                "title": "Ternary Scatter Plot",
                "ternary": {
                    "sum": 1,
                    "aaxis": {
                        "title": "X",
                        "min": 0.01,
                        "linewidth": 2,
                        "ticks": "outside",
                    },
                    "baxis": {
                        "title": "W",
                        "min": 0.01,
                        "linewidth": 2,
                        "ticks": "outside",
                    },
                    "caxis": {
                        "title": "S",
                        "min": 0.01,
                        "linewidth": 2,
                        "ticks": "outside",
                    },
                },
                "showlegend": False,
            }
        )

        return go.Figure()

    @property
    def _sub_layouts(self):

        graph = html.Div(
            [
                dcc.Graph(
                    figure=go.Figure(layout=PhaseDiagramComponent.empty_plot_style),
                    id=self.id("graph"),
                    config={"displayModeBar": False, "displaylogo": False},
                )
            ],
            id=self.id("pd-div"),
        )
        table = html.Div(
            [
                html.Div(
                    dash_table.DataTable(
                        id=self.id("entry-table"),
                        columns=(
                            [
                                {
                                    "id": p["col"],
                                    "name": p["col"],
                                    "editable": p["edit"],
                                }
                                for p in self.default_table_params
                            ]
                        ),
                        style_table={
                            "maxHeight": "450px",
                            "overflowY": "auto",
                            "border": "thin lightgrey solid",
                        },
                        # n_fixed_rows=1,
                        sort_action="native",
                        editable=True,
                        row_deletable=True,
                        style_header={
                            "backgroundColor": "rgb(230, 249, 255)",
                            "fontWeight": "bold",
                        },
                        style_cell={
                            "fontFamily": "IBM Plex Sans",
                            "textAlign": "centered",
                            "whiteSpace": "normal",
                        },
                        css=[
                            {
                                "selector": ".dash-cell div.dash-cell-value",
                                "rule": "display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;",
                            }
                        ],
                        style_cell_conditional=[
                            {"if": {"column_id": "Material ID"}, "width": "20%"},
                            {"if": {"column_id": "Formula"}, "width": "20%"},
                        ],
                    )
                ),
                Button(
                    "Add Custom Entry",
                    id=self.id("editing-rows-button"),
                    kind="primary",
                    n_clicks=0,
                ),
                html.P("Enter composition and formation energy per atom."),
            ]
        )

        return {"graph": graph, "table": table}

    def layout(self):
        return html.Div(
            [
                Columns(
                    [
                        Column(self._sub_layouts["graph"]),
                        Column(self._sub_layouts["table"]),
                    ],
                    centered=True,
                )
            ]
        )

    def generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("pd-div"), "children"), [Input(self.id("figure"), "data")]
        )
        def update_graph(figure):
            if figure is None:
                raise PreventUpdate
            elif figure == "error":
                search_error = (
                    MessageContainer(
                        [
                            MessageBody(
                                dcc.Markdown(
                                    "Plotting is only available for phase diagrams containing 2-4 components."
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

        @app.callback(Output(self.id("figure"), "data"), [Input(self.id(), "data")])
        def make_figure(pd):
            if pd is None:
                raise PreventUpdate

            pd = self.from_data(pd)
            dim = pd.dim

            if dim not in [2, 3, 4]:
                return "error"

            plotter = PDPlotter(pd)

            data = []
            for line in plotter.pd_plot_data[0]:
                if dim == 2 or dim == 3:
                    data.append(
                        go.Scatter(
                            x=list(line[0]),
                            y=list(line[1]),  # create all phase diagram lines
                            mode="lines",
                            hoverinfo="none",
                            line={
                                "color": "rgba (0, 0, 0, 1)",
                                "dash": "solid",
                                "width": 3.0,
                            },
                            showlegend=False,
                        )
                    )

                elif dim == 4:
                    data.append(
                        go.Scatter3d(
                            x=list(line[0]),
                            y=list(line[1]),
                            z=list(line[2]),
                            mode="lines",
                            hoverinfo="none",
                            line={
                                "color": "rgba (0, 0, 0, 1)",
                                "dash": "solid",
                                "width": 3.0,
                            },
                            showlegend=False,
                        )
                    )

            data.append(self.create_unstable_markers(plotter, pd))
            data.append(self.create_markers(plotter, pd))

            fig = go.Figure(data=data)
            fig.layout = self.figure_layout(plotter, pd)

            return fig

        @app.callback(Output(self.id(), "data"), [Input(self.id("entries"), "data")])
        def create_pd_object(entries):
            if entries is None or not entries:
                raise PreventUpdate

            entries = self.from_data(entries)

            return PhaseDiagram(entries)

        @app.callback(
            Output(self.id("entries"), "data"),
            [Input(self.id("entry-table"), "derived_virtual_data")],
        )
        def update_entries_store(rows):
            if rows is None:
                raise PreventUpdate
            entries = []
            for row in rows:
                try:
                    comp = Composition(row["Formula"])
                    energy = row["Formation Energy (eV/atom)"]
                    if row["Material ID"] is None:
                        attribute = "Custom Entry"
                    else:
                        attribute = row["Material ID"]
                    # create new entry object containing mpid as attribute (to combine with custom entries)
                    entry = PDEntry(
                        comp, float(energy) * comp.num_atoms, attribute=attribute
                    )
                    entries.append(entry)
                except:
                    continue

            if not entries:
                raise PreventUpdate

            return entries

        @app.callback(
            Output(self.id("entry-table"), "data"),
            [
                Input(self.id("chemsys-internal"), "data"),
                Input(self.id(), "modified_timestamp"),
                Input(self.id("editing-rows-button"), "n_clicks"),
            ],
            [State(self.id(), "data"), State(self.id("entry-table"), "data")],
        )
        def create_table(chemsys, pd_time, n_clicks, pd, rows):

            ctx = dash.callback_context

            if ctx is None or not ctx.triggered or chemsys is None:
                raise PreventUpdate

            trigger = ctx.triggered[0]

            # PD update trigger
            if trigger["prop_id"] == self.id() + ".modified_timestamp":
                table_content = self.create_table_content(self.from_data(pd))
                return table_content
            elif trigger["prop_id"] == self.id("editing-rows-button") + ".n_clicks":
                if n_clicks > 0 and rows:
                    rows.append(self.empty_row)
                    return rows

            with MPRester() as mpr:
                entries = mpr.get_entries_in_chemsys(chemsys)

            pd = PhaseDiagram(entries)
            table_content = self.create_table_content(pd)

            return table_content

        @app.callback(
            Output(self.id("chemsys-internal"), "data"),
            [
                Input(self.id("mpid"), "data"),
                Input(self.id("chemsys-external"), "data"),
            ],
        )
        def get_chemsys_from_mpid_or_chemsys(mpid, chemsys_external: str):
            """
            :param mpid: mpid
            :param chemsys_external: chemsys, e.g. "Co-O"
            :return: chemsys
            """
            ctx = dash.callback_context

            if ctx is None or not ctx.triggered:
                raise PreventUpdate

            trigger = ctx.triggered[0]

            if trigger["value"] is None:
                raise PreventUpdate

            chemsys = None

            # get entries by mpid
            if trigger["prop_id"] == self.id("mpid") + ".data":
                with MPRester() as mpr:
                    entry = mpr.get_entry_by_material_id(mpid)

                chemsys = entry.composition.chemical_system

            # get entries by chemsys
            if trigger["prop_id"] == self.id("chemsys-external") + ".data":
                chemsys = chemsys_external

            return chemsys


class PhaseDiagramPanelComponent(PanelComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pd_component = PhaseDiagramComponent()
        self.pd_component.attach_from(self, this_store_name="struct")

    @property
    def title(self):
        return "Phase Diagram"

    @property
    def description(self):
        return (
            "Display the compositional phase diagram for the"
            " chemical system containing this structure (between 2–4 species)."
        )

    def update_contents(self, new_store_contents, *args):
        return self.pd_component.layout
