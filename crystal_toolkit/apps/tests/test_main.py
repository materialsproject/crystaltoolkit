from __future__ import annotations

import time
from typing import TYPE_CHECKING

from crystal_toolkit.apps.main import app

if TYPE_CHECKING:
    from crystal_toolkit.apps.examples.tests.typing import DashDuo


def test_main_app_startup(dash_duo: DashDuo):
    dash_duo.start_server(app)
    # dash_duo.clear_storage()

    dash_duo.wait_for_element("#StructureMoleculeComponent_title", timeout=4)
    time.sleep(10)

    dash_duo.percy_snapshot("main_app_startup-layout")
    dash_duo.take_snapshot("main_app_startup-layout")

    logs = dash_duo.get_logs()
    assert logs == [], f"Unexpected browser {logs=}"
