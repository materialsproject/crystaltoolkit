from crystal_toolkit.apps.examples.bandstructure import app
import time


def test_bs(dash_duo):

    dash_duo.start_server(app)
    dash_duo.clear_storage()

    time.sleep(5)
    dash_duo.percy_snapshot("example_bsdos_on_load")

    # test choosing elemental projection
    el = dash_duo.select_dcc_dropdown("#_ct_bs_dos_dos-select", index=1)

    time.sleep(3)
    dash_duo.percy_snapshot("example_bsdos_projection_index_1")

    # test selecting total orbital projection
    el = dash_duo.select_dcc_dropdown("#_ct_bs_dos_dos-select", index=2)

    time.sleep(3)
    dash_duo.percy_snapshot("example_bsdos_projection_index_2")

    # assert bool(dash_duo.get_logs()) is False, f"Browser console contains an error: {dash_duo.get_logs()}"
