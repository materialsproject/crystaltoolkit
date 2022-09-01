=======
Helpers
=======

The ``helpers`` submodule in Crystal Toolkit contains a few utilities
that are useful for making your app.

Inputs
------

The `inputs <source/crystal_toolkit.helpers.layouts>`_ submodule contains various
controls for inputting floating point numbers, matrices, boolean values, etc. with labels
attached.

Layouts
-------

The Crystal Toolkit app makes heavy use of the
`Bulma CSS Framework <https://bulma.io>`_ for styling. The
`layouts <source/crystal_toolkit.helpers.layouts>`_ submodule contains
a few wrappers for ``html.Div`` with these styles pre-applied, such as
``Columns``, ``Box``, ``Footer``, etc.

Renderers
---------

Three-dimensional scenes created using the
`Scene <source/crystal_toolkit.core.scene>`_ class can be rendered
by the ``Simple3DScene`` Dash component, but also other tools including
pythreejs (for Jupypter integration), POV-Ray (for high-quality rendering) and
asymptote (for LaTeX integration).
