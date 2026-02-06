import dash
from monty.serialization import loadfn

import crystal_toolkit.components as ctc
from crystal_toolkit.helpers.layouts import H3, Container
from crystal_toolkit.settings import SETTINGS

# load example task doc with LOBSTER data

task_doc = loadfn("lobstertaskdoc.json")

# example layout to demonstrate content of component

cohp_component = ctc.CohpAndDosComponent(
    density_of_states=task_doc.dos,
    lobsterpy_text_description={
        "all": task_doc.lobsterpy_text,
        "cation-anion": task_doc.lobsterpy_text_cation_anion,
    },
    calc_quality_description=task_doc.calc_quality_text,
    cohp_plot_data={
        "all": task_doc.lobsterpy_data.cohp_plot_data.data,
        "cation-anion": task_doc.lobsterpy_data_cation_anion.cohp_plot_data.data,
    },
    structure=task_doc.structure,
    obj_icohp=task_doc.icohp_list,
    obj_charge=task_doc.charges,
)

layout = Container([H3("LOBSTER Example"), cohp_component.layout()])

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH, prevent_initial_callbacks=False)  #

ctc.register_crystal_toolkit(app, layout=layout)

if __name__ == "__main__":
    app.run(debug=True, port=8051)
