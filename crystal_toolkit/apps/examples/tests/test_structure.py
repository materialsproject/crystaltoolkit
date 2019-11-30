from crystal_toolkit.apps.examples.structure import app
import time


def test_structure(dash_duo):

    dash_duo.start_server(app)
    dash_duo.clear_storage()
    time.sleep(1)

    dash_duo.percy_snapshot("example_structure-layout")
    dash_duo.take_snapshot("example_structure-layout")

    assert (
        dash_duo.get_logs() == []
    ), f"Browser console contains an error: {dash_duo.get_logs()}"
