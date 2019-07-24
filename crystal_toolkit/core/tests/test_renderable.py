from crystal_toolkit.core.renderable import Renderable, RenderableMeta
import pytest


class TestRenderable(Renderable):

    target_type = dict

    def to_scene(cls, obj, **kwargs):
        print(obj)
        return {"test": "test"}


def test_meta():
    # Ensure the interface is found
    assert RenderableMeta.get_interface({}) == TestRenderable

    # Ensure the right interface is called
    assert Renderable.render({}) == {"test": "test"}

    # Ensure we throw an expcetion when there is no interface
    with pytest.raises(Exception) as expception_info:
        Renderable.render("")

    # Ensure we can't call to_scene on the abstract base class
    with pytest.raises(Exception) as expception_info:
        Renderable.to_scene("")

    # Ensure we're clearning the interface list
    RenderableMeta.clear_interfaces()
    with pytest.raises(Exception) as expception_info:
        Renderable.render({})
