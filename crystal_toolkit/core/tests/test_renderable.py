from crystal_toolkit.core.renderable import Renderer
import pytest




def test_meta():

    assert Renderer.all_interfaces == {}

    # Enesure register saves the interface
    Renderer.register(dict,lambda x: {"test":"test"})
    assert dict in Renderer.all_interfaces

    # Ensure the right interface is called
    assert Renderer.render({}) == {"test": "test"}

    # Ensure we throw an expcetion when there is no interface
    with pytest.raises(Exception) as expception_info:
        Renderer.render("")

    # Ensure we're clearning the interface list
    Renderer.clear_interfaces()
    with pytest.raises(Exception) as expception_info:
        Renderer.render({})
