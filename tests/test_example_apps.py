from importlib import import_module
from pathlib import Path

import pytest
from dash import Dash


@pytest.fixture(scope="session")
def example_apps():
    """Return paths to example app files."""
    examples_dir = Path(__file__).parent.parent / "example_apps"
    return list(examples_dir.glob("*.py"))


def test_example_apps(example_apps):
    """Check each app is a valid Dash instance and can handle a basic request."""
    for app_path in example_apps:
        # Import the app module
        relative_path = app_path.relative_to(app_path.parent.parent)
        module_name = str(relative_path.with_suffix("")).replace("/", ".")
        module = import_module(module_name)

        # Check app exists and is a Dash app
        app = getattr(module, "app", None)
        assert app is not None, f"No 'app' object found in {app_path}"
        assert isinstance(app, Dash), f"'app' object in {app_path} is not a Dash app"

        # Use Flask's test client instead of running the server
        with app.server.test_client() as client:
            response = client.get("/")
            assert response.status_code in (200, 302)  # OK or redirect are both fine
