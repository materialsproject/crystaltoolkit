from __future__ import annotations

from typing import Protocol

import dash


class DashDuo(Protocol):
    "The dash_duo pytest fixture lives in dash.testing.plugin.dash_duo."

    def start_server(self, start_server) -> None:
        ...

    def find_element(self, selector: str) -> dash.development.base_component.Component:
        ...

    def wait_for_text_to_equal(self, selector: str, text: str, timeout: int) -> None:
        ...

    def get_logs(self) -> list[str]:
        ...
