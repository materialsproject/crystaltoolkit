from __future__ import annotations

from typing import Protocol

import dash


class DashDuo(Protocol):
    "The dash_duo pytest fixture lives in dash.testing.plugin.dash_duo."

    def start_server(self, start_server) -> None:
        ...

    def find_element(self, selector: str) -> dash.development.base_component.Component:
        ...

    def wait_for_text_to_equal(
        self, selector: str, text: str, timeout: int = None
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

    def wait_for_element(self, selector: str, timeout: int = None) -> None:
        ...

    def take_snapshot(self, name: str) -> None:
        ...

    def wait_for_page(self, url: str = None, timeout: int = 10) -> None:
        ...
