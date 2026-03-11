import dash
from monty.serialization import loadfn

import crystal_toolkit.components as ctc
from crystal_toolkit.components.localenv import LocalEnvironmentPanel
from crystal_toolkit.helpers.layouts import H3, Container
from crystal_toolkit.settings import SETTINGS

task_doc = loadfn("lobstertaskdoc.json")

local_env_component = LocalEnvironmentPanel(
    default_data={
        "structure": task_doc.structure,
        "obj_icohp": task_doc.icohp_list,
        "obj_charge": task_doc.charges,
    },
)

layout = Container(
    [H3("LocalEnv Example"), local_env_component.panel_layout(open_by_default=False)]
)

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH, prevent_initial_callbacks=False)

ctc.register_crystal_toolkit(app, layout=layout)

if __name__ == "__main__":
    app.run(debug=True, port=8051)
