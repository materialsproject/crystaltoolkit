from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING

from selenium.webdriver.common.keys import Keys

from crystal_toolkit.apps.examples.diffraction import app

if TYPE_CHECKING:
    from crystal_toolkit.apps.examples.tests.typing import DashDuo


def test_diffraction(dash_duo: DashDuo) -> None:
    dash_duo.start_server(app)
    dash_duo.clear_storage()

    # make sure the XRD component was mounted and is a node with class 'dash-graph'
    node = dash_duo.find_element("#CTXRayDiffractionComponent_xrd-plot")
    assert "dash-graph" in node.get_attribute("class")

    sleep(1)
    # select 'Shape Factor' and 'Peak Profile' inputs and increment their values
    # to ensure they throw no errors
    input_nodes = dash_duo.find_elements("input[type=number]")
    input_nodes[0].send_keys(Keys.ARROW_UP)
    sleep(1)
    input_nodes[1].send_keys(Keys.ARROW_UP)
    sleep(1)
    # focus the other input since component only updates on blur
    input_nodes[0].send_keys(Keys.ARROW_UP)

    logs = dash_duo.get_logs()
    assert logs == [], f"Unexpected browser {logs=}"
