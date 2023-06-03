from __future__ import annotations

from typing import Protocol, Union

import dash

ElemOrSelector = Union[str, dash.development.base_component.Component]


class DashDuo(Protocol):
    """The dash_duo pytest fixture lives in dash.testing.plugin.dash_duo.

    See https://dash.plotly.com/testing#browser-apis
    and https://github.com/plotly/dash/issues/2170
    """

    # driver = ...  # selenium.webdriver.remote.WebDriver

    def start_server(self, start_server) -> None:
        ...

    def find_element(self, selector: str) -> dash.development.base_component.Component:
        ...

    def wait_for_text_to_equal(
        self, selector: str, text: str, timeout: int | None = None
    ) -> None:
        ...

    def get_logs(self) -> list[str]:
        ...

    def clear_storage(self) -> None:
        ...

    def percy_snapshot(self, name: str, wait_for_callbacks: bool = False) -> None:
        ...

    def multiple_click(self, selector: str, clicks: int) -> None:
        ...

    def wait_for_element(self, selector: str, timeout: int | None = None) -> None:
        ...

    def take_snapshot(self, name: str) -> None:
        ...

    def wait_for_page(self, url: str | None = None, timeout: int = 10) -> None:
        ...

    def find_elements(
        self, selector: str
    ) -> list[dash.development.base_component.Component]:
        ...

    def select_dcc_dropdown(
        self,
        elem_or_selector: ElemOrSelector,
        value: str | None = None,
        index: int | None = None,
    ) -> None:
        # https://github.com/plotly/dash/blob/04217e8/dash/testing/browser.py#L409
        ...
