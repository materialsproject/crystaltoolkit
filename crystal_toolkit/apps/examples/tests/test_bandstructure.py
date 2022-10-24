import time

from crystal_toolkit.apps.examples.bandstructure import app
from crystal_toolkit.apps.examples.tests.typing import DashDuo


def test_bs(dash_duo: DashDuo) -> None:
    dash_duo.start_server(app)
    dash_duo.clear_storage()

    time.sleep(5)
    dash_duo.percy_snapshot("example_bsdos_on_load")

    # # test choosing elemental projection
    # el = dash_duo.select_dcc_dropdown(
    #     '{"component_id":"CTbs_dos","hint":"literal","idx":"False","kwarg_label":"dos-select"}',
    #     index=1,
    # )
    #
    # time.sleep(3)
    # dash_duo.percy_snapshot("example_bsdos_projection_index_1")
    #
    # # test selecting total orbital projection
    # el = dash_duo.select_dcc_dropdown("#CTbs_dos_dos-select", index=2)
    #
    # time.sleep(3)
    # dash_duo.percy_snapshot("example_bsdos_projection_index_2")

    logs = dash_duo.get_logs()
    assert logs == [], f"Browser console should not contain errors: {logs}"
