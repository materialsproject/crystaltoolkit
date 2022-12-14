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

.. literalinclude:: ../crystal_toolkit/apps/examples/basic_hello_world.py

Save this code as ``app.py`` and it can be run with ``python app.py``.

Visiting `<http://localhost:8050>`_ in your web browser should then
give a blank page with the text "Hello scientist!".

Adding an MPComponent
~~~~~~~~~~~~~~~~~~~~~

To display information such as crystal structures or phase diagrams, we
have to add an `MPComponent <source/crystal_toolkit.core.mpcomponent>`_ to our layout. To illustrate, we'll use a simple
crystal structure.

.. literalinclude:: ../crystal_toolkit/apps/examples/basic_hello_structure.py

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
By updating the contents of this store with a new object, the visual state of the component
will also be updated.

This is best illustrated by example. We will add a button that shows a random crystal
structure when clicked.

.. literalinclude:: ../crystal_toolkit/apps/examples/basic_hello_structure_interactive.py

The two features here that make this slightly different from a regular Dash app are:

1. The structure object is stored and accessed via ``structure_component.id()``
   and its ``data`` prop. The `.id()` method ensures that each Dash component
   has a unique id, even if multiple of the same MPComponent are present on the
   same page.
2. We can return the object directly (as a ``Structure`` object) via the callback,
   without needing to serialize or deserialize it.

Note that due to the dynamic nature of a Crystal Toolkit app, callback exceptions are
suppressed on app load. For debugging of static layouts,
you might want to re-enable callback exceptions.

Linking Components Together
~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ToDo

Running in Production
~~~~~~~~~~~~~~~~~~~~~

.. note::
   This section is optional for getting an app working.

Long-running callbacks (> 0.1 ms) can make a web app feel slow and sluggish.
Since callbacks do not rely on any external state, they are easy to cache.

Caching is supported by many Crystal Toolkit components, but by default
caching is in-memory only and not thread safe.

Any `Flask-Caching <https://pythonhosted.org/Flask-Cache>`_
backend is supported, we recommend ``RedisCache``:

::

   # ... define your Dash "app" variable first

   from flask_caching import Cache

   cache = Cache(
       app.server,
       config={
           "CACHE_TYPE": "redis",
           "CACHE_REDIS_URL": os.environ.get("REDIS_URL", "localhost:6379"),
       },
   )

   # and tell crystal toolkit about the cache
   ctc.register_crystal_toolkit(app, layout, cache=cache)

Additionally, you should run the app using ``gunicorn`` rather than using ``python app.py``
directly so that there are multiple workers available to handle callbacks --
this will result in a huge performance improvement.

All of the recommendations in the main `Dash documentation <https://dash.plot.ly>`_ also apply.
