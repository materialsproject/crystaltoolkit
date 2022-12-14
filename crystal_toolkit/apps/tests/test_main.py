import time

from crystal_toolkit.apps.examples.tests.typing import DashDuo
from crystal_toolkit.apps.main import app


def test_main_app_startup(dash_duo: DashDuo):
    dash_duo.start_server(app)
    # dash_duo.clear_storage()

    dash_duo.wait_for_element("#StructureMoleculeComponent_title", timeout=4)
    time.sleep(10)

    dash_duo.percy_snapshot("main_app_startup-layout")
    dash_duo.take_snapshot("main_app_startup-layout")

    logs = dash_duo.get_logs()
    assert logs == [], f"Unexpected browser {logs=}"
