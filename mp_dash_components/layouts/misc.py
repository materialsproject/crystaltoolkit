import dash_html_components as html

from dash.dependencies import Input, Output, State


def help_layout(help_message):
    return html.Span([" ? ", html.Span(help_message, className="tooltiptext")],
                     className="tooltip")


def combine_option_dicts(list_of_option_components,
                         output_component, output_component_property, app):

    @app.callback(
        Output(output_component, output_component_property),
        [Input(option_component, 'value')
         for option_component in list_of_option_components],
        [State(output_component, output_component_property)]
    )
    def combine_options(*args):

        # because Dash doesn't (yet) support multiple callbacks
        # to one output, we have to do this

        d = args[-1] or {}

        for opt in args[:-1]:
            d.update(opt)

        return d