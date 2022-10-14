from crystal_toolkit.core.mpcomponent import MPComponent
from crystal_toolkit.helpers.layouts import Loading, dcc, html


class FermiSurfaceComponent(MPComponent):
    def __init__(
        self,
        fermi_surface=None,
        id=None,
        **kwargs,
    ):
        super().__init__(id=id, default_data=fermi_surface, **kwargs)

    def layout(self):
        from ifermi.plot import FermiSurfacePlotter

        fermi_surface = self.initial_data["default"]
        plotter = FermiSurfacePlotter(fermi_surface)
        figure = plotter.get_plot(plot_type="plotly")

        # ensure the plot has a transparent background
        figure.layout["paper_bgcolor"] = "rgba(0,0,0,0)"
        figure.layout["plot_bgcolor"] = "rgba(0,0,0,0)"
        figure.layout["scene"]["xaxis"]["backgroundcolor"] = "rgba(0,0,0,0)"
        figure.layout["scene"]["yaxis"]["backgroundcolor"] = "rgba(0,0,0,0)"
        figure.layout["scene"]["zaxis"]["backgroundcolor"] = "rgba(0,0,0,0)"

        # remove mouseover grid
        figure.layout["scene"]["xaxis"]["showspikes"] = False
        figure.layout["scene"]["yaxis"]["showspikes"] = False
        figure.layout["scene"]["zaxis"]["showspikes"] = False
        for data in figure.data:
            data["hoverinfo"] = "skip"

        # remove LaTeX from high-symmetry labels
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
        for label in figure.layout["scene"]["annotations"]:
            for find, replace in str_replace.items():
                label["text"] = label["text"].replace(find, replace)

        return html.Div(
            [
                Loading(
                    [
                        dcc.Graph(
                            figure=figure,
                            config={"displayModeBar": False},
                            responsive=True,
                        )
                    ],
                    id=self.id("fermi-surface-div"),
                )
            ]
        )
