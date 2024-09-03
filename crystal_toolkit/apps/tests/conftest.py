import pytest
from playwright.sync_api import Page


@pytest.fixture(autouse=True)
def _assert_no_console_errors(page: Page):
    logs = []
    page.on("console", lambda msg: logs.append(msg))

    page.goto("http://127.0.0.1:8050")

    yield

    errors = [msg.text for msg in logs if msg.type == "error"]
    assert len(errors) == 0, f"Unexpected browser {errors=}"
