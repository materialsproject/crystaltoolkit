====================
Your First Component
====================

This page is intended for **developers of Crystal Toolkit** who want to add
a new ``MPComponent`` to support interactive viewing of an ``MSONable`` object,
such as crystal structures, phase diagrams, etc.

.. Important::
    Crystal Toolkit is built on top of `Dash by Plotly <https://dash.plot.ly>`_.
    Dash is a framework to build rich, interactive web apps purely from Python with
    no JavaScript knowledge required.
    If you're not familiar with the Dash framework, please read their documentation
    and try their example app first.

The basic steps are to:

1. Sub-class `MPComponent <source/crystal_toolkit.core.mpcomponent>`_. Recognize
   that the component comes with a ``dcc.Store`` which contains the ``MSON``
   representation of whatever the component is intended to render.

2. Implement its master ``layout()`` method to return the "default" layout
   for your component. You may also add additional ``..._layout()``
   methods for optional layouts; for example, the ``StructureMoleculeComponent``
   has ``legend_layout()`` to return the legend for the structure or molecule
   being displayed.

   The ``_sub_layouts`` method, which returns a dictionary with values corresponding
   to different parts of your component, is available for book-keeping if your
   component is complex.

4. For interactivity, implement the ``generate_callbacks(app, cache)`` method.
   Inside this method you can define callbacks to be associated with the component.
   *At minimum,* make sure that if the component's main ``dcc.Store`` is updated
   with a new object (for example, a new crystal structure is set for
   ``StructureMoleculeComponent``) that the state of the component is also updated
   appropriately.

   Try to keep the total number of callbacks to a minimum, and
   the size of the data stores small wherever possible, to improve performance of
   your component. Using multiple-output callbacks, and judicious use of
   ``raise PreventUpdate`` and ``return no_update`` can help with this, especially
   if checking for the initial callback firing on page load.

   If you have a long-running callback, or one that *may* be long-running, make
   sure to wrap it in a ``dcc.Loading`` component to improve the user experience.

At this point, the component should be working. It needs a simple **example app**
to be added to ``crystal_toolkit.apps.examples`` and a corresponding **test** that
the example app runs, and finally a short documentation page in ``docs_rst``. Please
copy from the existing examples as necessary.
