=======================
A Materials Project App
=======================

MP App Intro
~~~~~~~~~~~~

If you have already made a custom app using ``MPComponent``, it should be fairly straightforward to convert it to a website-ready app. To aid in this process, this documentation walks through the components of the catalysis app as an example (crystal_toolkit/apps/examples/mpcontribs). If you have not already made an app using `MPComponent`, you should also take a look at the documentation provided for it. This documentation also points out some useful helper functions and the location where all helper functions may be found. At a high-level, the most important difference is rather than establishing a subclass of `MPComponent`, you should establish a subclass of `MPApp`. `MPApp` is a subclass of `MPComponent`

Details of the Catalysis App
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The catalysis app has two primary tabs:
1. The search tab
2. The binary visualization tab
For ease of understanding and modularity, each tab has a function defined to get the layout: ``get_search_layout`` and ``get_visualization_layout``. There is a third function called ``get_layout``, which is actually called to establish the layout for the app and calls the two other functions.

The app queries the OC20 dataset from MPContribs. An example of this is within ``get_plot_data`` for the binary visualization.

To support interactivity with the binary visualization, the app uses two different callbacks, which are contained within the ``generate_callbacks`` function. The first, ``update_figure``, handles the querying of data presentation of it in the plot. The second, ``display_click_data`` updates a supplementary table of information when the user clicks on a grid point. ``generate_callbacks`` is a good example of how to establish callbacks, how to use the decorator for callbacks (``@app.callback()``), and how to establish data caching with the ``@cache.memoize()`` decorator when it is advantageous to do so.


Useful helper functions to consider
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
All helper functions may be found in ``crystaltoolkit.helpers.utils``. Some particularly useful ones are highlighted below, but take a look to see if there is anything you can leverage!

Helpful tooltips
^^^^^^^^^^^^^^^^
There is a convenient helper function to add tooltips to text called ``get_box_title``. Help strings are stored in a yaml file which is shared for all apps on the website called ``help.yaml``. To add a tooltip, simply add your tip to the yaml file following the format:
::
  use_point:
    title:
      help: “string that helps the user”
      label: “String of text to appear, which when hovered over will show the help str”
      link: “optional link - otherwise null”


Then call the helper function where desired. This is done with this line in the catalysis app:
::
  additional_data = get_box_title(use_point="CatalysisApp", title="catapp-add-data")

Well formatted tables
^^^^^^^^^^^^^^^^^^^^^
There is a convenient helper function, ``get_data_table`` which takes as input a dataframe and returns a website-ready formatted table

Well formatted matrices
^^^^^^^^^^^^^^^^^^^^^^^
There is a convenient helper function, ``get_matrix_string``, to convert arrays into a string for use in ``mpc.Markdown()`` so they are website-ready.
