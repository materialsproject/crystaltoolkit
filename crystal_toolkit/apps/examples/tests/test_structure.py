from crystal_toolkit.apps.examples.structure import app
import time


def test_structure(dash_duo):

    dash_duo.start_server(app)
    dash_duo.clear_storage()

    time.sleep(5)
    dash_duo.percy_snapshot("example_structure_on_load")

    # click the settings button (second button in the button-bar) to show the settings panel
    # and test the settings options.
    dash_duo.find_elements(".mpc-button-bar .button")[1].click()

    # test changing radius
    el = dash_duo.select_dcc_dropdown("#CTmy_structure_radius_strategy", index=0)
    time.sleep(1)
    dash_duo.percy_snapshot("example_structure_radius_index_0")

    # test changing radius again
    el = dash_duo.select_dcc_dropdown("#CTmy_structure_radius_strategy", index=2)
    time.sleep(1)
    dash_duo.percy_snapshot("example_structure_primitive_radius_index_2")

    assert (
        bool(dash_duo.get_logs()) is False
    ), f"Browser console contains an error: {dash_duo.get_logs()}"
