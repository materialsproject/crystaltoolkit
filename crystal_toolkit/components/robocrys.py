import dash_html_components as html
from dash.dependencies import Input, Output
from robocrys import StructureCondenser, StructureDescriber
from robocrys import __version__ as robocrys_version

from crystal_toolkit.core.panelcomponent import PanelComponent
from crystal_toolkit.helpers.layouts import MessageContainer, MessageBody, Loading


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

    def contents_layout(self) -> html.Div:

        return Loading(id=self.id("robocrys"))

    def generate_callbacks(self, app, cache):

        super().generate_callbacks(app, cache)

        @app.callback(
            Output(self.id("robocrys"), "children"), [Input(self.id(), "data")]
        )
        @cache.memoize()
        def run_robocrys_analysis(new_store_contents):

            struct = self.from_data(new_store_contents)

            try:

                condenser = StructureCondenser()
                describer = StructureDescriber(fmt="unicode")

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
