import pandas as pd
import plotly.express as px
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
    (Structure.from_dict(step["structure"]), step["e_fr_energy"])
    for calc in reversed(task_doc.calcs_reversed)
    for step in calc.output["ionic_steps"]
]
struct_traj, energies = zip(*steps)
assert len(steps) == 99

e_col = "energy (eV/atom)"
spg_col = "spacegroup"
df_traj = pd.DataFrame(
    {e_col: energies, spg_col: [s.get_space_group_info() for s in struct_traj]}
)


def plot_energy(df: pd.DataFrame, step: int) -> go.Figure:
    """Plot energy as a function of relaxation step."""
    href = f"https://materialsproject.org/materials/{mp_id}"
    title = f"<a {href=}>{mp_id}</a> - {spg_col} = {df[spg_col][step]}"
    fig = px.line(df, y=e_col, template="plotly_white", title=title)
    fig.add_vline(x=step, line=dict(dash="dash", width=1))
    return fig


struct_comp = ctc.StructureMoleculeComponent(
    id="structure", struct_or_mol=struct_traj[0]
)

step_size = max(1, len(struct_traj) // 20)  # ensure slider has max 20 steps
slider = dcc.Slider(
    id="slider",
    min=0,
    max=len(struct_traj) - 1,
    value=0,
    step=step_size,
    updatemode="drag",
)

graph = dcc.Graph(id="fig", figure=plot_energy(df_traj, 0), style={"maxWidth": "50%"})

app = Dash(prevent_initial_callbacks=True, assets_folder=SETTINGS.ASSETS_PATH)
app.layout = html.Div(
    [
        html.H1(
            "Structure Relaxation Trajectory", style=dict(margin="1em", fontSize="2em")
        ),
        html.P("Drag slider to see structure at different relaxation steps."),
        slider,
        html.Div([struct_comp.layout(), graph], style=dict(display="flex", gap="2em")),
    ],
    style=dict(
        margin="2em auto", placeItems="center", textAlign="center", maxWidth="1000px"
    ),
)

ctc.register_crystal_toolkit(app=app, layout=app.layout)


@app.callback(
    Output(struct_comp.id(), "data"), Output(graph, "figure"), Input(slider, "value")
)
def update_structure(step: int) -> tuple[Structure, go.Figure]:
    """Update the structure displayed in the StructureMoleculeComponent and the
    dashed vertical line in the figure when the slider is moved.
    """
    return struct_traj[step], plot_energy(df_traj, step)


app.run_server(port=8050, debug=True)
