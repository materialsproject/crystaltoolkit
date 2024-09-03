===================
Jupyter Integration
===================

Crystal Toolkit offers integration with Jupyter to
allow easy viewing of crystal structures and other Materials Project
data interactively.

Usage
-----

To use, simply ``import crystal_toolkit`` and use ``pymatgen`` as normal for crystal structures
to be shown using Crystal Toolkit.

Caveats
-------

Crystal Toolkit now uses Dash's in-built `Jupyter integration <https://dash.plotly.com/dash-in-jupyter>`_.
Previous versions of Crystal Toolkit used a customer Jupyter extension, but this extension was limited in scope,
difficult to maintain, and restricted usage to specific versions of Jupyter (Jupyter Lab 2+). The new solution
runs a Dash server behind-the-scenes.

Issues might be encountered when running behind a proxy. To fix, try::

   from dash import jupyter_dash

   jupyter_dash.infer_jupyter_proxy_config()

Alternatively, consult the Dash documentation or forums for help. The default port is 8884, but can be modified
by setting the ``CT_JUPYTER_EMBED_PORT`` environment variable.
