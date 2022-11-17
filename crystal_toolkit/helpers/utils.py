import re
from fractions import Fraction
from typing import Any, Optional
from uuid import uuid4

import dash_mp_components as mpc
import numpy as np
from dash import dash_table as dt
from dash import dcc, html
from flask import has_request_context, request
from monty.serialization import loadfn
from mpcontribs.client import Client as MPContribsClient

from crystal_toolkit import MODULE_PATH
from crystal_toolkit.defaults import _DEFAULTS
from crystal_toolkit.settings import SETTINGS


def update_object_args(d_args, object_name, allowed_args):
    """Read default properties and overwrite them if user input exists.

    Arguments:
        d_args {dict} -- User defined properties
        object_name {str} -- Name of object
        allowed_kwargs {List[str]} -- Used to limit the data that is passed to pythreejs

    Returns:
        Dictionary -- Properties of object after userinput and default values are considered
    """
    obj_args = {k: v for k, v in (_DEFAULTS["scene"][object_name] or {}).items()}
    obj_args.update(
        {k: v for k, v in (d_args or {}).items() if k in allowed_args and v is not None}
    )
    return obj_args


def is_logged_in() -> bool:
    """
    Check if user is logged in using request headers.
    For testing on localhost, will return True if SETTINGS.DEV_LOGIN_DISABLED=True.
    """
    is_dev_login_disabled = SETTINGS.DEV_LOGIN_DISABLED and is_localhost()
    return bool(is_dev_login_disabled or is_logged_in_user())


def is_logged_in_user(consumer=None) -> bool:
    """
    Check if the client has the necessary headers for an authenticated user
    """
    if not consumer:
        consumer = get_consumer()
    return bool(
        not consumer.get("X-Anonymous-Consumer") and consumer.get("X-Consumer-Id")
    )


def is_localhost() -> bool:
    """
    Returns True if the host in the web address starts with
    any of the following local names: localhost, 127.0.0.1, or 0.0.0.0
    """
    if not has_request_context():
        return True

    host = request.headers.get("Host", "")
    return bool(
        host.startswith("localhost:")
        or host.startswith("127.0.0.1:")
        or host.startswith("0.0.0.0:")
    )


def get_consumer():

    if not has_request_context():
        return {}

    names = [
        "X-Consumer-Id",  # kong internal uuid
        "X-Consumer-Custom-Id",  # api key
        "X-Consumer-Username",  # <provider>:<email>
        "X-Anonymous-Consumer",  # is anonymous user?
        "X-Authenticated-Groups",  # groups this user belongs to
        "X-Consumer-Groups",  # same as X-Authenticated-Groups
    ]
    headers = {}
    for name in names:
        value = request.headers.get(name)
        if value is not None:
            headers[name] = value
    return headers


def is_url(s):
    return s.startswith("http://") or s.startswith("https://")


def get_user_api_key(consumer=None) -> Optional[str]:
    """
    Get the api key that belongs to the current user
    If running on localhost, api key is obtained from
    the environment variable MP_API_KEY
    """
    if not consumer:
        consumer = get_consumer()

    if is_localhost():
        return SETTINGS.API_KEY
    elif is_logged_in_user(consumer):
        return consumer["X-Consumer-Custom-Id"]
    else:
        return None


def get_contribs_client():
    """
    Get an instance of the MPContribsClient that will work
    in either production or a dev environment.
    Client uses MPCONTRIBS_API_HOST by default.
    """
    headers = get_consumer()

    if is_localhost():
        return MPContribsClient(apikey=get_user_api_key())
    else:
        return MPContribsClient(headers=headers)


def get_contribs_api_base_url(request_url=None, deployment="contribs"):
    """Get the MPContribs API endpoint for a specific deployment"""
    if is_localhost() and SETTINGS.API_EXTERNAL_ENDPOINT:
        return f"https://{deployment}-api.materialsproject.org"

    if has_request_context() and (not request_url):
        request_url = request.url

    return parse_request_url(request_url, f"{deployment}-api")


def parse_request_url(request_url, subdomain):
    parsed_url = urllib.parse.urlparse(request_url)
    pre, suf = parsed_url.netloc.split("next-gen")
    netloc = pre + subdomain + suf
    scheme = "http" if netloc.startswith("localhost.") else "https"
    base_url = f"{scheme}://{netloc}"
    return base_url


HELP_STRINGS = loadfn(MODULE_PATH / "apps/help.yaml")
if SETTINGS.DEBUG_MODE:
    for k, v in HELP_STRINGS.items():
        if len(v["help"]) > 280:
            # TODO: add a debug logger here instead
            logger.debug(
                f"⚠️ HELP STRING WARNING. Help for {k} is too long, please re-write: {v}"
            )


def get_box_title(use_point: str, title: str, id=None):
    """
    Convenience method to wrap box titles in H5 tags and
    conditionally add a tooltip from HELP_STRINGS.
    :param use_point: name indicating where the help string is used (top level key)
    :param title: text that displays as title and maps to property in HELP_STRINGS
    :return: H5 title with or without a tooltip
    """
    args = {}
    if id is not None:
        args["id"] = id

    if use_point not in HELP_STRINGS:
        return html.H5(title, className="title is-6 mb-2", **args)
    else:
        div = html.H5(
            get_tooltip(
                tooltip_label=HELP_STRINGS[use_point][title]["label"],
                tooltip_text=HELP_STRINGS[use_point][title]["help"],
                className="has-tooltip-multiline",
            ),
            className="title is-6 mb-2",
            **args,
        )
        if link := HELP_STRINGS[use_point][title]["link"]:
            div = html.A(div, href=link)
        return div


def get_tooltip(
    tooltip_label: Any,
    tooltip_text: str,
    underline: bool = True,
    tooltip_id: str = "",
    wrapper_class: str = None,
    **kwargs,
):
    """
    Uses the tooltip component from dash-mp-components to add a tooltip, typically for help text.
    This component uses react-tooltip under the hood.
    :param tooltip_label: text or component to display and apply hover behavior to
    :param tooltip_text: text to show on hover
    :param tooltip_id: unique id of the tooltip (will generate one if not supplied)
    :param wrapper_class: class to add to the span that wraps all the returned tooltip components (label + content)
    :param kwargs: additional props added to Tooltip component. See the components js file in dash-mp-components for a full list of props.
    :return: html.Span
    """
    if not tooltip_id:
        tooltip_id = uuid4().hex

    tooltip_class = "tooltip-label" if underline else None
    return html.Span(
        [
            html.Span(
                tooltip_label,
                className=tooltip_class,
                **{"data-tip": True, "data-for": tooltip_id},
            ),
            mpc.Tooltip(tooltip_text, id=tooltip_id, **kwargs),
        ],
        className=wrapper_class,
    )


def get_reference_button(cite_text=None, hover_text=None, doi=None, icon="book"):

    if (not doi) or cite_text:
        # TODO: This will get removed, due to addition of new PublicationButton
        if cite_text:
            button_contents = [ctl.Icon(kind=icon), html.Span(cite_text)]
        else:
            button_contents = ctl.Icon(kind=icon)
        button = html.Form(
            [
                ctl.Button(
                    button_contents,
                    size="small",
                    kind="link",
                )
            ],
            # action=f"https://dx.doi.org/{doi}",
            # method="get",
            # target="_blank",
            style={
                "display": "inline-block",
                "cursor": "not-allowed",
                "opacity": "0.5",
                "textDecoration": "none",
            },
        )

    if doi:
        # set an id based on the doi, if you don't set a unique id
        # then React will not update the button appropriately if the
        # doi is changed via a callback; this may be a bug
        button = mpc.PublicationButton(doi=doi, id=uuid4().hex)

    if hover_text:
        button = get_tooltip(button, tooltip_text=hover_text)
    return button


# TODO: move to crystal-toolkit when stable
def get_data_table(
    df=None, virtualized=True, columns=None, column_widths=None, **kwargs
):
    """
    Returns a nicely styled DataTable with sensible defaults
    for re-use.
    :param df: optional pandas DataFrame to populate DataTable
    :param virtualized: used for large tables, adds filter options
    :param columns: list of dicts with keys id and name
    :param column_widths: dict of column id to column width, e.g. "50px"
    :param kwargs: kwargs to pass to dt.DataTable
    :return: dt.DataTable
    """

    datatable_kwargs = dict(
        sort_action="native",
        row_selectable="single",
        style_as_list_view=True,
        # style_table={"width": "800px"},
        style_cell={
            "fontFamily": "Helvetica Neue",
            "textAlign": "left",
            "whitespace": "normal",
        },
    )

    if virtualized:
        datatable_kwargs["virtualization"] = True
        datatable_kwargs["filter_action"] = "native"

    if not columns:
        columns = [{"id": column, "name": column} for column in df.columns]
    datatable_kwargs["columns"] = columns

    for k, v in kwargs.items():
        if k in datatable_kwargs:
            if isinstance(datatable_kwargs[k], dict):
                datatable_kwargs[k].update(v)
            elif isinstance(datatable_kwargs[k], list):
                datatable_kwargs[k].append(v)
            else:
                datatable_kwargs[k] = v
        else:
            datatable_kwargs[k] = v

    if df is not None:
        datatable_kwargs["data"] = df.to_dict("records")

    if column_widths:
        style_data_conditional = [
            {"if": {"column_id": column_id}, "width": column_width}
            for column_id, column_width in column_widths.items()
        ]
        if "style_data_conditional" not in datatable_kwargs:
            datatable_kwargs["style_data_conditional"] = []
        datatable_kwargs["style_data_conditional"] += style_data_conditional

    if virtualized:
        return html.Div(
            [
                dt.DataTable(**datatable_kwargs),
                html.Small(
                    dcc.Markdown(
                        'Table columns can be filtered by typing in the "filter data..." box. '
                        "Filter operators `<`, `>`, `=` and `!=` are also supported.",
                        className="mt-2",
                    )
                ),
            ]
        )
    else:
        return dt.DataTable(**datatable_kwargs)


def get_section_heading(title, dois=None, docs_url=None, app_button_id=None):
    """
    Helper function to build section headings with docs button.
    This is used inside of a section layout to build heading section using section data.
    The app_button_id should be used inside a callback in the section code to populate
    the app button with its computed button/link (e.g. see synthesis section).
    """

    app_link = (
        dcc.Link(
            [],
            id=app_button_id,
            className="section-heading-offset-link is-hidden-mobile",
            href="",
        )
        if app_button_id
        else None
    )

    # TODO: move method buttons into a dropdown
    methods_button = (
        html.Div(
            [
                mpc.Dropdown(
                    [
                        html.Div(
                            get_reference_button("Methods paper", doi=doi),
                            className="dropdown-item no-hover",
                        )
                        for doi in dois
                    ],
                    triggerLabel="Methods",
                    triggerIcon="fa fa-book",
                    triggerClassName="button is-small",
                    isRight=True,
                ),
            ],
            className="level-item",
        )
        if dois
        else None
    )

    docs_item = (
        dcc.Link(
            "Understand this Section",
            className="dropdown-item is-nowrap",
            href=docs_url,
            target="_blank",
        )
        if docs_url
        else None
    )

    section_actions = mpc.Dropdown(
        [
            docs_item,
            mpc.ModalContextProvider(
                [
                    mpc.ModalTrigger("Methods", className="dropdown-item"),
                    mpc.Modal(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        f"{title} Methods", className="panel-heading"
                                    ),
                                    html.Div(
                                        [
                                            ctl.Box(mpc.CrossrefCard(identifier=doi))
                                            for doi in dois
                                        ],
                                        className="panel-content",
                                    ),
                                ],
                                className="panel",
                            )
                        ]
                    ),
                ]
            ),
            html.Div("Calculations", className="dropdown-item"),
            app_link,
        ],
        triggerIcon="fa fa-ellipsis-h",
        triggerClassName="button is-small",
        isArrowless=True,
        closeOnSelection=False,
    )

    docs_button = (
        get_tooltip(
            dcc.Link(
                ctl.Icon(kind="info-circle"),
                href=docs_url,
                target="_blank",
                className="inherit-color",
            ),
            f"Go to {title} documentation page",
            underline=False,
            wrapper_class="ml-2 is-inline-block",
        )
        if docs_url
        else None
    )

    return ctl.H4([title, docs_button, app_link])


def get_matrix_string(matrix, variable_name=None, decimals=4):
    """
    Returns a string for use in mpc.Markdown() to render a matrix
    or vector.
    :param matrix: list or numpy array
    :param variable_name: LaTeX-formatted variable name
    :param decimals: number of decimal places to round to
    :return: LaTeX-formatted string
    """

    if decimals:
        matrix = np.round(matrix, decimals=decimals) + 0
    else:
        matrix = np.array(matrix)

    header = "$$\n"
    if variable_name:
        header += f"{variable_name} = \\begin{{bmatrix}}\n"
    else:
        header += "\\begin{bmatrix}\n"

    footer = "\\end{bmatrix}\n$$"

    matrix_string = ""

    assert hasattr(matrix, "__iter__"), "The matrix provided was not iterable"

    for row in matrix:
        row_string = ""
        for idx, value in enumerate(row):
            row_string += f"{value:.4g}"
            if idx != len(row) - 1:
                row_string += " & "
        row_string += " \\\\ \n"
        matrix_string += row_string

    return header + matrix_string + footer


def update_css_class(kwargs, class_name):
    """
    Convenience function to update className while respecting
    any additional classNames already set.
    """
    if "className" in kwargs:
        kwargs["className"] += f" {class_name}"
    else:
        kwargs["className"] = class_name


def is_mpid(value: str):
    """
    Determine if a string is in the MP ID syntax.
    Checks if the string starts with 'mp-' or 'mvc-'
    and is followed by only numbers.
    """
    if re.match(r"(mp|mvc)\-\d+$", value):
        return value
    else:
        return False


def pretty_frac_format(x):
    """
    Formats a float to a fraction, if the fraction can be
    expressed without a large denominator.
    """

    x = x % 1
    fraction = Fraction(x).limit_denominator(8)
    if np.allclose(x, 1):
        x_str = "0"
    elif not np.allclose(x, float(fraction)):
        x = np.around(x, decimals=2)
        x_str = f"{x:.3g}"
    else:
        x_str = str(fraction)
    return x_str
