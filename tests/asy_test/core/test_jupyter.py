import plotly.express as px
from monty.json import MSONable

from crystal_toolkit.core.jupyter import patch_msonable
from crystal_toolkit.core.scene import Scene


def test_patch_msonable():
    patch_msonable()

    class GetSceneClass(MSONable):
        def get_scene(self):
            return Scene(name="test_scene")

    class GetPlotClass(MSONable):
        def get_plot(self):
            """Dummy plotly object"""
            return px.scatter(x=[1, 2, 3], y=[1, 2, 3])

    class AsDictClass(MSONable):
        def __init__(self, a: int) -> None:
            self.a = a

    # The output of _ipython_display_ is None
    # However, the logic for the creating the different output
    # dictionaries should be executed so the following tests
    # are still valuable.
    as_dict_class = AsDictClass(1)
    assert as_dict_class._ipython_display_() is None

    get_scene_class = GetSceneClass()
    assert get_scene_class._ipython_display_() is None

    get_plot_class = GetPlotClass()
    assert get_plot_class._ipython_display_() is None
