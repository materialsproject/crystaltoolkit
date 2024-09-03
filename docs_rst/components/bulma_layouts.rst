Bulma Layouts
-------------

`Bulma <https://bulma.io>`_ is a popular CSS-only web framework which can make it easier to build responsive web interfaces.
This is an alternative to other frameworks, such as Bootstrap, which require additional JavaScript to be loaded.

Crystal Toolkit provides wrappers around the in-built Dash HTML components with Bulma CSS styles pre-applied.

To use::

    from crystal_toolkit import ctl

    # a simple two-column layout
    my_layout = ctl.Columns([
        ctl.Column([]),
        ctl.Column([])
    ])

Most Bulma styles are supported and fully type-hinted in Python. It is recommended to keep the Bulma docs open when
using these components to make it easier to understand how to achieve specific layouts!
