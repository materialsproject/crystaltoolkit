import pytest
from dash import Dash
from dash.exceptions import PreventUpdate
from pymatgen.core import Lattice, Structure

from crystal_toolkit.components.diffraction_tem import TEMDiffractionComponent

diffsim_dash = pytest.importorskip("quantem.diffsim.dash")

Si = Structure.from_spacegroup("Fd-3m", Lattice.cubic(5.431), ["Si"], [[0, 0, 0]])


def test_settings_callback():
    component = TEMDiffractionComponent(initial_structure=Si)
    app = Dash()
    component.generate_callbacks(app, None)

    # the server callback that writes the settings, and the bundle route from register()
    name = component.id("quantem-diffsim")
    (key,) = [
        key
        for key in app.callback_map
        if name in key and diffsim_dash.SETTINGS_TYPE in key
    ]
    assert any(
        diffsim_dash.BUNDLE_ROUTE in rule.rule
        for rule in app.server.url_map.iter_rules()
    )

    update_settings = app.callback_map[key]["callback"].__wrapped__
    settings = update_settings(Si.as_dict())
    assert settings["zone_axis"] == [0, 0, 1]
    assert settings["mode"] == "nanobeam"
    assert settings["energy_keV"] == 200
    assert settings["structure_name"] == "Si"
    assert "Fd-3m" in settings["cif"]

    with pytest.raises(PreventUpdate):
        update_settings(None)
