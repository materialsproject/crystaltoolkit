from __future__ import annotations

from crystal_toolkit.helpers.asymptote_renderer import (
    ASY_OBJS,
    _read_color,
    _read_properties,
)


def test_read_properties(standard_scenes):
    def _set_and_read_properties(scene):
        # make sure the _meta["asy"] attribute is set
        scene._meta = scene._meta or {}
        scene._meta["asy"] = scene._meta.get("asy", {})

        scene.prop0 = "scene"
        scene._meta["prop0"] = "meta"
        user_setting = {scene.type: {"prop0": "user"}}
        p0 = _read_properties(scene, property="prop0", user_settings=user_setting)
        assert p0 == "user"

        scene.prop1 = "scene"
        scene._meta["asy"]["prop1"] = "meta"
        p1 = _read_properties(scene, property="prop1")
        assert p1 == "meta"

    for val in standard_scenes.values():
        _set_and_read_properties(val)
        # Default color is used
        assert _read_color(val) is not None


def test_asymptote_renderer(standard_scenes):
    for key in ["lines", "spheres", "cylinders", "surface"]:
        asy_obj = ASY_OBJS[key].from_ctk(standard_scenes[key])
        assert "draw" in str(asy_obj).lower()
