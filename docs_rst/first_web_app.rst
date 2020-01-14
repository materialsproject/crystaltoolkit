==============
Your First App
==============

This page is intended for users who want to make their own web app
to explore materials science data.

.. Important::
    Crystal Toolkit is built on top of `Dash by Plotly <https://dash.plot.ly>`_.
    Dash is a framework to build rich, interactive web apps purely from Python with
    no JavaScript knowledge required.
    If you're not familiar with the Dash framework, please read their documentation
    and try their example app first.

Example App
~~~~~~~~~~~

Each component has a self-contained example app in the
`crystal_toolkit.apps.examples <https://github.com/materialsproject/crystaltoolkit/tree/master/crystal_toolkit/apps/examples>`_
folder. If you prefer to learn by seeing, take a look at one of these!
Otherwise, building an app is explained step-by-step below.

Preamble
~~~~~~~~

Every Crystal Toolkit app needs the following basic structure:

::

    # standard Dash imports
    import dash
    import dash_html_components as html
    import dash_core_components as dcc

    # standard Crystal Toolkit import
    import crystal_toolkit.components as ctc

    # create Dash app as normal
    app = dash.Dash()

    # tell Crystal Toolkit about the app
    ctc.register_app(app)

    # create your layout
    my_layout = html.Div(["Hello scientist!"])

    # wrap your app.layout with crystal_toolkit_layout()
    # to ensure all necessary components are loaded into layout
    app.layout = ctc.crystal_toolkit_layout(my_layout)

    # allow app to be run using "python app.py"
    # in production, deploy behind gunicorn or similar
    # see Dash documentation for more information
    if __name__ == "__main__":
        app.run_server(debug=True, port=8050)

Save this code as ``app.py`` and it can be run with ``python app.py``.

Visiting `<http://localhost:8050>`_ in your web browser should then
give a blank page with the text "Hello scientist!".

Adding an MPComponent
~~~~~~~~~~~~~~~~~~~~~

To display information such as crystal structures or phase diagrams, we
have to add an `MPComponent <source/crystal_toolkit.core.mpcomponent>`_ to our layout. To illustrate, we'll use a simple
crystal structure.

::

    # as explained in "preamble" section in documentation
    import dash
    import dash_html_components as html
    import dash_core_components as dcc
    import crystal_toolkit.components as ctc

    app = dash.Dash()
    ctc.register_app(app)

    # create our crystal structure using pymatgen
    from pymatgen import Structure, Lattice
    structure = Structure(Lattice.cubic(4.2), ["Na", "K"], [[0, 0, 0], [0.5, 0.5, 0.5]])

    # create the Crystal Toolkit component
    structure_component = ctc.StructureMoleculeComponent(structure)

    # add the component's layout to our app's layout
    my_layout = html.Div([structure_component.layout()])

    # as explained in "preamble" section in documentation
    app.layout = ctc.crystal_toolkit_layout(my_layout)
    if __name__ == "__main__":
        app.run_server(debug=True, port=8050)

The important thing here is that we instantiated the ``structure_component`` outside
the layout, and then called its ``.layout()`` method to get the Dash layout to insert
as part of the ``app.layout``.

All ``MPComponents`` follow this basic structure:

* They can be instantiated with an ``MSONable`` object as their only argument.
  Here, it was a ``Structure`` object. There may be additional arguments to customize
  the component.
* They have at least one ``.layout()`` method to generate the Dash layout for that
  component, although some components have additional (optional) ``layout`` methods.

Interactivity
~~~~~~~~~~~~~

For the purposes of interactivity, we can use callbacks as in any other Dash app.

The important addition from an ``MPComponent`` is that they an ``id()`` method to access the
ids of the component itself or of any sub-layouts inside that component. The canonical
layout is a `dcc.Store() <https://dash.plot.ly/dash-core-components/store>`_ containing
the serialized representation of your Python object, such as the crystallographic structure.
By updating the contents of this store with a new object, the

This is best illustrated by example. We will add a button that shows a random crystal
structure when clicked.

::

    # as above
    import dash
    import dash_html_components as html
    import dash_core_components as dcc
    import crystal_toolkit.components as ctc

    # standard Dash imports for callbacks (interactivity)
    from dash.dependencies import Input, Output, State

    # so we can pick a structure at random
    from random import choice
    from pymatgen import Structure, Lattice

    app = dash.Dash()
    ctc.register_app(app)

    # prevent static checking of your layout ahead-of-time
    # otherwise errors can be raised in certain instances
    # see discussion below
    app.config["suppress_callback_exceptions"] = True

    # now we give a list of structures to pick from
    structures = [
        Structure(Lattice.cubic(4), ["Na", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]]),
        Structure(Lattice.cubic(5), ["K", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]]),
        Structure(Lattice.cubic(6), ["Li", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]])
    ]

    # we show the first structure by default
    structure_component = ctc.StructureMoleculeComponent(structures[0])

    # and we create a button for user interaction
    my_button = html.Button("Randomize!", id="random_button")

    # now we have two entries in our app layout,
    # the structure component's layout and the button
    my_layout = html.Div([structure_component.layout(), my_button])
    app.layout = ctc.crystal_toolkit_layout(my_layout)

    # for the interactivity, we use a standard Dash callback
    @app.callback(
        Output(structure_component.id(), "data"),
        [Input("random_button", "n_clicks")]
    )
    def update_structure(n_clicks):
        return choice(structures)

    # as above
    if __name__ == "__main__":
        app.run_server(debug=True, port=8050)

The two features here that make this slightly different from a regular Dash app are:

1. The structure object is stored and accessed via ``structure_component.id()``
   and its ``data`` prop. The `.id()` method ensures that each Dash component
   has a unique id, even if multiple of the same MPComponent are present on the
   same page.
2. We can return the object directly (as a ``Structure`` object) via the callback,
   without needing to serialize or deserialize it.

Finally, it is important to mention why we have set ``supress_callback_exceptions``
to ``True``. In a Dash app, the layout is walked on first load to make sure that all
interactive elements are actually in your app. This is to prevent common errors for
first-time users, for example creating a callback to an ``id`` that doesn't exist.
However, in Crystal Toolkit, many components have optional additional interactive
elements. In the case of the structure component, this includes things like displaying
a legend, or providing controls to modify the color scheme. Since we haven't included
these optional elements in this example, callback exceptions would be raised if this
setting wasn't enabled.

Caching
~~~~~~~

.. note::
   This section is optional for getting an app working.

Long-running callbacks (> 0.1ms) can make a web app feel slow and sluggish.
Since callbacks do not rely on any external state, they are easy to cache.

Caching is supported by many Crystal Toolkit components, but the cache
backend has to be registered first. Any `Flask-Caching <https://pythonhosted.org/Flask-Caching/>`_
backend is supported, but we recommend either:

1. ``SimpleCache`` for easy testing:

::

    # ... define your Dash "app" variable first

    from flask_caching import Cache
    cache = Cache(app.server, config={'CACHE_TYPE': 'simple'})

    from crystal_toolkit.components import register_cache
    register_cache(cache)

2. ``RedisCache`` for production:

::

   # ... define your Dash "app" variable first

   from flask_caching import Cache

   cache = Cache(
       crystal_toolkit_app.server,
       config={
           "CACHE_TYPE": "redis",
           "CACHE_REDIS_URL": os.environ.get("REDIS_URL", "localhost:6379"),
       },
   )

   from crystal_toolkit.components import register_cache
   register_cache(cache)