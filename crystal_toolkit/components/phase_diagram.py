import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from pprint import pprint

from pymatgen import MPRester
from pymatgen.core.structure import Structure
from pymatgen.analysis.phase_diagram import PhaseDiagram, PDPlotter

from crystal_toolkit.helpers.layouts import *  # layout helpers like `Columns` etc. (most subclass html.Div)
from crystal_toolkit.components.core import MPComponent, PanelComponent


class PhaseDiagramComponent(MPComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_store("mpid")
        self.create_store("struct")
        self.create_store("chemsys")
        self.create_store("figure")

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
            "title": "Fraction",
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

    empty_plot_style = {
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
    }

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
    )

    default_table_params = [
        "Material ID",
        "Formula",
        "Formation Energy (eV/atom)",
        "Energy Above Hull (eV/atom)",
        "Stable?",
    ]

    def figure_layout(self, plotter, pd):

        dim = pd.dim

        if dim == 2:
            annotations_list = []

            for entry in plotter.pd_plot_data[1]:
                x, y = entry[0], entry[1]

                formula = list(
                    plotter.pd_plot_data[1][entry].composition.reduced_formula
                )
                text = []
                for char in formula:
                    if char.isdigit():
                        text.append("<sub>" + char + "</sub>")
                    else:
                        text.append(char)
                clean_formula = ""
                clean_formula = clean_formula.join(text)

                new_annotation = {
                    "align": "center",
                    "font": {"color": "#000000", "size": 20.0},
                    "opacity": 1,
                    "showarrow": False,
                    "text": clean_formula + "  ",
                    "x": x,
                    "xanchor": "right",
                    "yanchor": "auto",
                    "xref": "x",
                    "y": y,
                    "yref": "y",
                }

                annotations_list.append(new_annotation)

                layout = self.default_binary_plot_style
                layout["annotations"] = annotations_list
            return layout

        elif dim == 3:
            annotations_list = []

            for entry in plotter.pd_plot_data[1]:
                x, y = entry[0], entry[1]

                formula = list(
                    plotter.pd_plot_data[1][entry].composition.reduced_formula
                )
                text = []
                for char in formula:
                    if char.isdigit():
                        text.append("<sub>" + char + "</sub>")
                    else:
                        text.append(char)
                clean_formula = ""
                clean_formula = clean_formula.join(text)

                new_annotation = {
                    "align": "center",
                    "font": {"color": "#000000", "size": 18.0},
                    "opacity": 1,
                    "showarrow": False,
                    "text": clean_formula + "  ",
                    "x": x,
                    "xanchor": "right",
                    "yanchor": "top",
                    "xref": "x",
                    "y": y,
                    "yref": "y",
                }

                annotations_list.append(new_annotation)

                layout = self.default_ternary_plot_style
                layout["annotations"] = annotations_list
            return layout

        elif dim == 4:
            annotations_list = []

            for entry in plotter.pd_plot_data[1]:
                x, y, z = entry[0], entry[1], entry[2]

                formula = list(
                    plotter.pd_plot_data[1][entry].composition.reduced_formula
                )
                text = []
                for char in formula:
                    if char.isdigit():
                        text.append("<sub>" + char + "</sub>")
                    else:
                        text.append(char)
                clean_formula = ""
                clean_formula = clean_formula.join(text)

                new_annotation = {
                    "align": "center",
                    "font": {"color": "#000000", "size": 18.0},
                    "opacity": 1,
                    "showarrow": False,
                    "text": clean_formula,
                    "x": x,
                    "y": y,
                    "z": z,
                    "xshift": 25,
                    "yshift": 10,
                }

                annotations_list.append(new_annotation)

                layout = self.default_quaternary_plot_style
                layout["scene"] = dict(
                    annotations=annotations_list,
                    xaxis=dict(
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
                    ),
                    yaxis=dict(
                        title=None,
                        visible=False,
                        autorange=True,
                        showgrid=False,
                        zeroline=False,
                        showline=False,
                        showaxeslabels=False,
                        ticks="",
                        showticklabels=False,
                        showspikes=False,
                    ),
                    zaxis=dict(
                        title=None,
                        visible=False,
                        autorange=True,
                        showgrid=False,
                        zeroline=False,
                        showline=False,
                        showaxeslabels=False,
                        ticks="",
                        showticklabels=False,
                        showspikes=False,
                    ),
                )
            return layout

        else:
            raise ValueError("Dimension of phase diagram must be 2, 3, or 4")

    def create_markers(self, plotter, pd):
        x_list = []
        y_list = []
        z_list = []
        text = []
        dim = pd.dim

        for entry in plotter.pd_plot_data[1]:
            energy = round(
                pd.get_form_energy_per_atom(plotter.pd_plot_data[1][entry]), 3
            )
            mpid = plotter.pd_plot_data[1][entry].entry_id
            formula = plotter.pd_plot_data[1][entry].composition.reduced_formula
            s = []
            for char in formula:
                if char.isdigit():
                    s.append("<sub>" + char + "</sub>")
                else:
                    s.append(char)
            clean_formula = "".join(s)

            x_list.append(entry[0])
            y_list.append(entry[1])
            if dim == 4:
                z_list.append(entry[2])
            text.append(
                clean_formula + " (" + mpid + ")" + "<br>" + str(energy) + " eV"
            )

        if dim == 2 or dim == 3:
            marker_plot = go.Scatter(
                x=x_list,
                y=y_list,
                mode="markers",
                name="Stable",
                marker=dict(color="#0562AB", size=11),
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
                marker=dict(color="#0562AB", size=8),
                hoverinfo="text",
                hoverlabel=dict(font=dict(size=14)),
                hovertext=text,
            )
        return marker_plot

    @staticmethod
    def create_table_content(pd):
        data = [{
            "Material ID": entry.entry_id,
            "Formula": entry.name,
            "Formation Energy (eV/atom)": round(
                pd.get_form_energy_per_atom(entry), 3
            ),
            "Energy Above Hull (eV/atom)": round(
                pd.get_e_above_hull(entry), 3
            ),
            "Predicted Stable?": (
                "Yes" if pd.get_e_above_hull(entry) == 0 else "No"
            )
        } for entry in pd.all_entries]
        return data

    @property
    def all_layouts(self):
        # Main plot
        graph = html.Div(
            [
                dcc.Graph(
                    figure=PhaseDiagramComponent.empty_plot_style,
                    id=self.id("graph"),
                    config={"displayModeBar": False, "displaylogo": False},
                )
            ]
        )
        table = html.Div(
            [
                dash_table.DataTable(
                    id=self.id("entry-table"),
                    columns=([{'id': p, 'name': p} for p in self.default_table_params]),
                    data=[],
                    style_table={"maxHeight": "400", "overflowY": "scroll"},
                    n_fixed_rows=1,
                    sorting=True,
                )
            ]
        )

        return {"graph": graph, "table": table}

    @property
    def standard_layout(self):
        return html.Div(
            [
                Columns([Column(self.all_layouts["graph"])], centered=True),
                Columns([Column(self.all_layouts["table"])]),
            ]
        )

    def _generate_callbacks(self, app, cache):
        @app.callback(
            Output(self.id("graph"), "figure"), [Input(self.id("figure"), "data")]
        )
        def update_graph(figure):
            return figure

        @app.callback(
            Output(self.id(), "data"),
             [Input(self.id("mpid"),"modified_timestamp"),
              Input(self.id("struct"),"modified_timestamp"),
              Input(self.id("chemsys"), "modified_timestamp")],
            [State(self.id("mpid"), "data"),
             State(self.id("struct"), "data"),
             State(self.id("chemsys"), "data")]
        )
        def generate_pd(mp_time,struct_time, chemsys_time, mpid, struct, chemsys):

            if (struct_time is None) or (mp_time is None) or (chemsys_time is None):
                raise PreventUpdate

            if struct_time > mp_time and struct_time > chemsys_time:
                if struct is None:
                    raise PreventUpdate
                chemsys = [
                    str(elem) for elem in self.from_data(struct).composition.elements
                ]

            elif mp_time >= struct_time and mp_time >= chemsys_time:
                if mpid is None:
                    raise PreventUpdate
                mpid = mpid["mpid"]

                with MPRester() as mpr:
                    entry = mpr.get_entry_by_material_id(mpid)

                chemsys = [str(elem) for elem in entry.composition.elements]

            with MPRester() as mpr:
                entries = mpr.get_entries_in_chemsys(
                    chemsys
                )  # use MPRester to acquire all entries in chem system

            pd = PhaseDiagram(entries)
            return self.to_data(pd)

        @app.callback(Output(self.id("figure"), "data"), [Input(self.id(), "data")])
        def make_figure(pd):
            pd = self.from_data(pd)
            dim = pd.dim

            plotter = PDPlotter(pd)  # create plotter object using pymatgen
            # print(pd.stable_entries)

            if dim not in [2, 3, 4]:
                raise ValueError(
                    "Structure contains {} components."
                    " Phase diagrams can only be created with 2, 3, or 4 components".format(
                        str(dim)
                    )
                )
            data = []  # initialize plot data list
            if dim == 2:
                for line in plotter.pd_plot_data[0]:
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
                x_list = []
                y_list = []
                text_list = []
                unstable_xy_list = list(plotter.pd_plot_data[2].values())
                unstable_entry_list = list(plotter.pd_plot_data[2].keys())

                for unstable_xy, unstable_entry in zip(
                    unstable_xy_list, unstable_entry_list
                ):
                    x_list.append(unstable_xy[0])
                    y_list.append(unstable_xy[1])
                    mpid = unstable_entry.entry_id
                    formula = list(unstable_entry.composition.reduced_formula)
                    e_above_hull = round(pd.get_e_above_hull(unstable_entry), 3)

                    # add formula subscripts
                    s = []
                    for char in formula:
                        if char.isdigit():
                            s.append("<sub>" + char + "</sub>")
                        else:
                            s.append(char)
                    clean_formula = ""
                    clean_formula = clean_formula.join(s)

                    energy = round(pd.get_form_energy_per_atom(unstable_entry), 3)
                    text_list.append(
                        f"{clean_formula} ({mpid})<br>"
                        f"{energy} eV ({e_above_hull} eV)"
                    )

                data.append(
                    go.Scatter(
                        x=x_list,
                        y=y_list,
                        mode="markers",
                        hoverinfo="text",
                        hovertext=text_list,
                        visible="legendonly",
                        name="Unstable",
                        marker=dict(color="#ff0000", size=12, symbol="x"),
                    )
                )

            elif dim == 3:
                for line in plotter.pd_plot_data[0]:
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
                x_list = []
                y_list = []
                xy_list = []
                text_list = []
                unstable_xy_list = list(plotter.pd_plot_data[2].values())
                unstable_entry_list = list(plotter.pd_plot_data[2].keys())

                for unstable_xy, unstable_entry in zip(
                    unstable_xy_list, unstable_entry_list
                ):
                    mpid = unstable_entry.entry_id
                    formula = unstable_entry.composition.reduced_formula
                    energy = round(pd.get_form_energy_per_atom(unstable_entry), 3)
                    e_above_hull = round(pd.get_e_above_hull(unstable_entry), 3)

                    s = []
                    for char in formula:
                        if char.isdigit():
                            s.append("<sub>" + char + "</sub>")
                        else:
                            s.append(char)
                    clean_formula = ""
                    clean_formula = clean_formula.join(s)

                    if unstable_xy not in xy_list:
                        x_list.append(unstable_xy[0])
                        y_list.append(unstable_xy[1])
                        xy_list.append(unstable_xy)
                        text_list.append(
                            clean_formula + " (" + mpid + ")"
                            "<br>"
                            + str(energy)
                            + " eV"
                            + " ("
                            + str(e_above_hull)
                            + " eV"
                            + ")"
                        )
                    else:
                        index = xy_list.index(unstable_xy)
                        text_list[index] += (
                            "<br>"
                            + clean_formula
                            + "<br>"
                            + str(energy)
                            + " eV"
                            + " ("
                            + str(e_above_hull)
                            + " eV"
                            + ")"
                        )

                data.append(
                    go.Scatter(
                        x=x_list,
                        y=y_list,
                        mode="markers",
                        hoverinfo="text",
                        hovertext=text_list,
                        visible="legendonly",
                        name="Unstable",
                        marker=dict(color="#ff0000", size=12, symbol="x"),
                    )
                )
            elif dim == 4:
                for line in plotter.pd_plot_data[0]:
                    data.append(
                        go.Scatter3d(
                            x=list(line[0]),
                            y=list(line[1]),
                            z=list(line[2]),  # create all phase diagram lines
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
                x_list = []
                y_list = []
                z_list = []
                xyz_list = []
                text_list = []
                unstable_xyz_list = list(plotter.pd_plot_data[2].values())
                unstable_entry_list = list(plotter.pd_plot_data[2].keys())

                for unstable_xyz, unstable_entry in zip(
                    unstable_xyz_list, unstable_entry_list
                ):
                    mpid = unstable_entry.entry_id
                    formula = unstable_entry.composition.reduced_formula
                    energy = round(pd.get_form_energy_per_atom(unstable_entry), 3)
                    e_above_hull = round(pd.get_e_above_hull(unstable_entry), 3)

                    s = []
                    for char in formula:
                        if char.isdigit():
                            s.append("<sub>" + char + "</sub>")
                        else:
                            s.append(char)
                    clean_formula = ""
                    clean_formula = clean_formula.join(s)

                    if unstable_xyz not in xyz_list:
                        x_list.append(unstable_xyz[0])
                        y_list.append(unstable_xyz[1])
                        z_list.append(unstable_xyz[2])
                        xyz_list.append(unstable_xyz)
                        text_list.append(
                            clean_formula
                            + " ("
                            + mpid
                            + ")"
                            + "<br>"
                            + str(energy)
                            + " eV"
                            + " ("
                            + str(e_above_hull)
                            + " eV"
                            + ")"
                        )
                    else:
                        index = xyz_list.index(unstable_xyz)
                        text_list[index] += (
                            "<br>"
                            + clean_formula
                            + "<br>"
                            + str(energy)
                            + " eV"
                            + " ("
                            + str(e_above_hull)
                            + " eV"
                            + ")"
                        )

                data.append(
                    go.Scatter3d(
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
                )
            data.append(self.create_markers(plotter, pd))
            fig = go.Figure(data=data)
            fig.layout = self.figure_layout(plotter, pd)
            return fig

        @app.callback(
            Output(self.id("entry-table"), "data"), [Input(self.id(), "data")]
        )
        def update_table(pd):
            pd = self.from_data(pd)
            table_content = self.create_table_content(pd)
            return table_content


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

    @property
    def initial_contents(self):

        return html.Div(
            [
                super().initial_contents,
                # necessary to include for the callbacks from PhaseDiagramComponent to work
                html.Div([self.pd_component.standard_layout]),
            ]
        )

    def update_contents(self, new_store_contents, *args):
        return self.pd_component.standard_layout
