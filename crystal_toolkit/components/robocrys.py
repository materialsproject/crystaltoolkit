import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from crystal_toolkit.components.core import PanelComponent
from crystal_toolkit.helpers.layouts import MessageContainer, MessageBody

from robocrys import StructureCondenser, StructureDescriber
from robocrys import __version__ as robocrys_version


class RobocrysComponent(PanelComponent):
    @property
    def title(self):
        return "Description"

    @property
    def description(self):
        return (
            "Your friendly robocrystallographer tries to describe a structure much "
            "like a human crystallographer would."
        )

    @property
    def loading_text(self):
        return "Robocrystallographer is analyzing your structure, " \
               "this can take up to a minute..."

    def update_contents(self, new_store_contents):

        struct = self.from_data(new_store_contents)

        condenser = StructureCondenser()
        describer = StructureDescriber()

        condensed_structure = condenser.condense_structure(struct)

        description = describer.describe(condensed_structure)

        return MessageContainer(MessageBody(
            [
                f"{description} – ",
                html.A(
                    f"🤖 robocrys v{robocrys_version}",
                    href="https://github.com/hackingmaterials/robocrystallographer",
                    style={"white-space": "nowrap"},
                ),
            ]
        ), kind="dark")
