import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from pymatgen.core import Structure
from pymatgen.ext.matproj import MPRester

import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS

mp_id = "mp-1033715"
with MPRester(monty_decode=False) as mpr:
    [task_doc] = mpr.tasks.search(task_ids=[mp_id])

steps = [
    (
        Structure.from_dict(step["structure"]),
        step["e_fr_energy"],
        np.linalg.norm(step["forces"], axis=1).mean(),
    )
    for calc in reversed(task_doc.calcs_reversed)
    for step in calc.output["ionic_steps"]
]
assert len(steps) == 99

e_col = "Energy (eV)"
force_col = "Force (eV/Å)"
spg_col = "Spacegroup"
struct_col = "Structure"

df_traj = pd.DataFrame(steps, columns=[struct_col, e_col, force_col])
df_traj[spg_col] = df_traj[struct_col].map(Structure.get_space_group_info)


def plot_energy_and_forces(
    df: pd.DataFrame,
    step: int,
    e_col: str,
    force_col: str,
    title: str,
) -> go.Figure:
    """Plot energy and forces as a function of relaxation step."""
    fig = go.Figure()
    # energy trace = primary y-axis
    fig.add_trace(go.Scatter(x=df.index, y=df[e_col], mode="lines", name="Energy"))

    # forces trace = secondary y-axis
    fig.add_trace(
        go.Scatter(x=df.index, y=df[force_col], mode="lines", name="Forces", yaxis="y2")
    )

    fig.update_layout(
        template="plotly_white",
        title=title,
        xaxis={"title": "Relaxation Step"},
        yaxis={"title": e_col},
        yaxis2={"title": force_col, "overlaying": "y", "side": "right"},
        legend=dict(yanchor="top", y=1, xanchor="right", x=1),
    )

    # vertical line at the specified step
    fig.add_vline(x=step, line={"dash": "dash", "width": 1})

    return fig


if "struct_comp" not in locals():
    struct_comp = ctc.StructureMoleculeComponent(
        id="structure", struct_or_mol=df_traj[struct_col][0]
    )

step_size = max(1, len(steps) // 20)  # ensure slider has max 20 steps
slider = dcc.Slider(
    id="slider", min=0, max=len(steps) - 1, value=0, step=step_size, updatemode="drag"
)


def make_title(spg: tuple[str, int]) -> str:
    """Return a title for the figure."""
    href = f"https://materialsproject.org/materials/{mp_id}/"
    return f"<a {href=}>{mp_id}</a> - {spg[0]} ({spg[1]})"


title = make_title(df_traj[spg_col][0])
graph = dcc.Graph(
    id="fig",
    figure=plot_energy_and_forces(df_traj, 0, e_col, force_col, title),
    style={"maxWidth": "50%"},
)

app = Dash(prevent_initial_callbacks=True, assets_folder=SETTINGS.ASSETS_PATH)
app.layout = html.Div(
    [
        html.H1(
            "Structure Relaxation Trajectory", style=dict(margin="1em", fontSize="2em")
        ),
        html.P("Drag slider to see structure at different relaxation steps."),
        slider,
        html.Div(
            [struct_comp.layout(), graph],
            style=dict(display="flex", gap="2em", placeContent="center"),
        ),
    ],
    style=dict(margin="auto", textAlign="center", maxWidth="1000px", padding="2em"),
)

ctc.register_crystal_toolkit(app=app, layout=app.layout)


@app.callback(
    Output(struct_comp.id(), "data"), Output(graph, "figure"), Input(slider, "value")
)
def update_structure(step: int) -> tuple[Structure, go.Figure]:
    """Update the structure displayed in the StructureMoleculeComponent and the
    dashed vertical line in the figure when the slider is moved.
    """
    title = make_title(df_traj[spg_col][step])
    fig = plot_energy_and_forces(df_traj, step, e_col, force_col, title)

    return df_traj[struct_col][step], fig


# https://stackoverflow.com/a/74918941
is_jupyter = "ipykernel" in sys.modules

app.run(port=8050, debug=True, use_reloader=not is_jupyter)
