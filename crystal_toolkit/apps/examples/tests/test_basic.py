from crystal_toolkit.apps.examples.basic_hello_world import app as hello_world_app
from crystal_toolkit.apps.examples.basic_hello_structure import (
    app as hello_structure_app,
)
from crystal_toolkit.apps.examples.basic_hello_structure_interactive import (
    app as hello_structure_interactive_app,
)

import time


def test_hello_scientist(dash_duo):

    dash_duo.start_server(hello_world_app)
    dash_duo.clear_storage()

    time.sleep(1)
    dash_duo.percy_snapshot("hello_scientist")

    logs = dash_duo.get_logs()
    # assert bool(logs) is False, f"Browser console contains an error: {logs}"


def test_hello_structure(dash_duo):
    dash_duo.start_server(hello_structure_app)
    dash_duo.clear_storage()

    time.sleep(1)
    dash_duo.percy_snapshot("hello_structure")

    logs = dash_duo.get_logs()
    # assert bool(logs) is False, f"Browser console contains an error: {logs}"


def test_hello_structure_interactive(dash_duo):
    dash_duo.start_server(hello_structure_interactive_app)
    dash_duo.clear_storage()

    time.sleep(1)
    dash_duo.percy_snapshot("hello_structure_interactive_on_load")

    dash_duo.multiple_click("#change_structure_button", 1)

    time.sleep(1)
    dash_duo.percy_snapshot("hello_structure_interactive_on_click")

    logs = dash_duo.get_logs()
    # assert bool(logs) is False, f"Browser console contains an error: {logs}"
