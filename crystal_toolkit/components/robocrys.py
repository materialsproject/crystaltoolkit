import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State


from crystal_toolkit.core.panelcomponent import PanelComponent, PanelComponent2
from crystal_toolkit.helpers.layouts import MessageContainer, MessageBody

from robocrys import StructureCondenser, StructureDescriber
from robocrys import __version__ as robocrys_version


class RobocrysComponent(PanelComponent2):
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
        return (
            "Robocrystallographer is analyzing your structure, "
            "this can take up to a minute"
        )

    def generate_callbacks(self, app, cache):

        super().generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("inner_contents"), "children"), [Input(self.id(), "data")]
        )
        def run_robocrys_analysis(new_store_contents):

            print("Robocrys callback fired")

            struct = self.from_data(new_store_contents)

            try:

                condenser = StructureCondenser()
                describer = StructureDescriber()

                condensed_structure = condenser.condense_structure(struct)

                description = describer.describe(condensed_structure)

            except Exception as exc:

                description = str(exc)

            return MessageContainer(
                MessageBody(
                    [
                        f"{description} – ",
                        html.A(
                            f"🤖 robocrys v{robocrys_version}",
                            href="https://github.com/hackingmaterials/robocrystallographer",
                            style={"white-space": "nowrap"},
                        ),
                    ]
                ),
                kind="dark",
            )
