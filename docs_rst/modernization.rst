=============
Modernization
=============

Crystal Toolkit has been able to work with both Dash 1.x and Dash 2. However,
several design choices were made before Dash 2 was developed that can now be
replaced with first-party solutions now provided by Dash 2.

The minimum version required is now Dash 2.11.

Wherever possible, changes will be made gradually and in a backwards-compatible way.
However, please pay attention to deprecation warnings!

The overall goal is to defer to first-party solutions wherever possible, with the
hope of making the Crystal Toolkit codebase leaner and simpler.

Plugin
------

Previously, a `ctc.register_crystal_toolkit()` line was required in every Crystal Toolkit
app. Dash now supports plugins, so the new solution is::

    from crystal_toolkit import CrystalToolkitPlugin

    my_layout = ...  # your initial app layout

    # provide other arguments to Dash constructor as required
    dash = Dash(..., plugins=[CrystalToolkitPlugin(layout=my_layout)])

Jupyter
-------

Previously, Crystal Toolkit supplied its own Jupyter Lab extension. While this is still
installed by default to render ``Scene`` objects, most end users will now use a Dash-based
Jupyter renderer. This will allow for display of Crystal Toolkit components in Jupyter
exactly as in its Dash app counterpart.

Pagination
----------

Crystal Toolkit as developed before first-party support for multipage apps was developed. As
such, there are some limitations for very large Crystal Toolkit apps, which result in a lot of
``dcc.Store`` elements being added to a layout. This design choice can now be reconsidered.
This improvement is pending.


All-in-One Components and Pattern-Matched Callbacks
---------------------------------------------------

Crystal Toolkit as developed before pattern-matched callbacks were available, and before
the "all-in-one" component pattern was established. Many components can now be simplified
to use these features. This improvement is pending.
