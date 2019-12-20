from crystal_toolkit.apps.main_app import crystal_toolkit_app
import time


def test_main_app_startup(dash_duo):

    dash_duo.start_server(crystal_toolkit_app)
    # dash_duo.clear_storage()

    dash_duo.wait_for_element("#StructureMoleculeComponent_title", timeout=4)
    time.sleep(10)

    dash_duo.percy_snapshot("main_app_startup-layout")
    dash_duo.take_snapshot("main_app_startup-layout")

    assert (
        dash_duo.get_logs() == []
    ), f"Browser console contains an error: {dash_duo.get_logs()}"
