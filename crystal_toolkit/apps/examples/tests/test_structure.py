from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING

from crystal_toolkit.apps.examples.structure import app

if TYPE_CHECKING:
    from crystal_toolkit.apps.examples.tests.typing import DashDuo


def test_structure(dash_duo: DashDuo) -> None:
    dash_duo.start_server(app)
    dash_duo.clear_storage()

    dash_duo.percy_snapshot("example_structure_on_load")
    sleep(1)

    # click the settings button (second button in the button-bar) to show the settings panel
    # and test the settings options.
    dash_duo.find_element(".mpc-button-bar .button[data-for*=settings]").click()

    # make sure changing unit cell works
    for idx in range(3):
        dash_duo.select_dcc_dropdown("#CTmy_structure_unit-cell-choice", index=idx)
        dash_duo.percy_snapshot(f"example_structure_unit-cell_index_{idx}")

    # test changing radius
    dash_duo.select_dcc_dropdown("#CTmy_structure_radius_strategy", index=0)
    dash_duo.percy_snapshot("example_structure_radius_index_0")
    sleep(1)

    # test changing radius again
    dash_duo.select_dcc_dropdown("#CTmy_structure_radius_strategy", index=2)
    dash_duo.percy_snapshot("example_structure_primitive_radius_index_2")
    sleep(1)

    logs = dash_duo.get_logs()
    assert logs == [], f"Unexpected browser {logs=}"
