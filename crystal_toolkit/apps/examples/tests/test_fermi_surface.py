from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

try:
    from crystal_toolkit.apps.examples.fermi_surface import app
except ImportError:
    pytest.skip(
        "IFermi either not installed or newer version of setuptools used.",
        allow_module_level=True,
    )

if TYPE_CHECKING:
    from crystal_toolkit.apps.examples.tests.typing import DashDuo


def test_diffraction(dash_duo: DashDuo) -> None:
    dash_duo.start_server(app)
    dash_duo.clear_storage()

    # make sure the FS component was mounted and is a node with class 'dash-graph'
    node = dash_duo.find_element("#CTfermi_surface_fermi-surface-graph")
    assert "dash-graph" in node.get_attribute("class")

    logs = dash_duo.get_logs()
    assert not logs, f"Unexpected browser {logs=}"
