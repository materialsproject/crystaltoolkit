from dash.testing.application_runners import import_app

from .conftest import DashDuo


def test_example_app(dash_duo: DashDuo):
    # dash_duo is a fixture by dash.testing.plugin.dash_duo.
    # It will load a py file containing a Dash instance named `app`
    # and start it in a thread.
    app = import_app("crystal_toolkit.apps.examples.basic_hello_world")
    dash_duo.start_server(app)
    wrapper_div = dash_duo.find_element("#_dash-app-content")

    assert wrapper_div.text == "_dash-app-content"
