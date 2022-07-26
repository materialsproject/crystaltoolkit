from crystal_toolkit import _DEFAULTS
from flask import request, has_request_context

from dash import html
from dash import dcc

from crystal_toolkit.helpers.utils import is_url
from crystal_toolkit.apps.constants import MP_APPS_BY_CATEGORY, APP_METADATA


def update_object_args(d_args, object_name, allowed_args):
    """Read default properties and overwrite them if user input exists

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


def get_mp_app_icon(icon_class_name, is_active=False, mini=False):
    """
    Get an MP app icon. This function is for prototyping and intended to be replaced.
    """
    if mini:
        size = "medium"
    else:
        size = "large"

    return html.Span(
        [html.I(className=icon_class_name)], className=f"mp-icon icon is-{size}"
    )


def get_breadcrumb(links):
    """
    Creates a styled breadcrumb navbar from a dictionary
    :param parts: dictionary of link names and link paths
    :return: html.Nav with breadcrumb links
    """
    if not links:
        return html.Div()

    breadcrumbs = html.Nav(
        html.Ul(
            [
                html.Li(
                    link,
                    className=(None if idx != len(links) - 1 else "is-active"),
                )
                for idx, link in enumerate(links)
            ]
        ),
        className="breadcrumb",
    )

    return breadcrumbs


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

def get_login_endpoints():
    """
    Returns the login and logout endpoints in a tuple
    The login endpoint lives in SETTINGS.LOGIN_ENDPOINT.
    """
    if SETTINGS.LOGIN_ENDPOINT:
        return SETTINGS.LOGIN_ENDPOINT, SETTINGS.LOGIN_ENDPOINT + "/logout"
    else:
        logger.error(
            "Could not find a login endpoint. Please set the MP_LOGIN_ENDPOINT environment variable to the login url."
        )
        return None, None
    
def is_url(s):
    return s.startswith("http://") or s.startswith("https://")


def get_apps_sidebar_item(app_name, current_app):
    app = APP_METADATA[app_name]
    is_full_url = is_url(app["url"])
    item_content = [
        html.Span(html.I(className=app["icon"]), className="icon"),
        html.Span(app["name"], className="ellipsis"),
    ]
    if is_full_url:
        item = dcc.Link(
            item_content,
            href=app["url"],
            target=f"_blank",
            className=f"mp-sidebar-item {'is-active' if current_app == app['name'] else ''}",
        )
    else:
        item = dcc.Link(
            item_content,
            href=f'/{app["url"]}',
            className=f"mp-sidebar-item {'is-active' if current_app == app['name'] else ''}",
        )

    return item


def get_apps_sidebar(current_app):
    """
    Generate the sidebar to be displayed while on an app page.
    This is a function and not a static variable because the current_app name must
    be passed to the layout to dynamically highlight the active app.
    Sidebar items are ultimately pulled from APP_METADATA. If an app has a category, it will be included here.
    """
    sidebar_items = [get_apps_sidebar_item("OverviewPage", current_app)]
    for (category, apps) in MP_APPS_BY_CATEGORY.items():
        sidebar_items.append(
            html.Div(
                [
                    html.Span("—", className="icon"),
                    html.Span(category, className="menu-label"),
                ],
                className="mp-sidebar-item is-label",
            )
        )
        for app_name in apps:
            item = get_apps_sidebar_item(app_name, current_app)
            sidebar_items.append(item)

    return html.Div(
        html.Div(
            html.Div(sidebar_items, className="mp-sidebar-items"),
            className="mp-sidebar-items-container",
        ),
        className="mp-sidebar is-hidden-touch",
    )