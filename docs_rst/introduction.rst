.. image:: images/logo.png
  :align: center
  :alt: Crystal Toolkit Logo
  :target: https://materialsproject.org/#apps/xtaltoolkit

============
Introduction
============

Crystal Toolkit is a web app framework from the `Materials Project <https://materialsproject.org>`_
allowing Python developers to easily make an interactive web app to display materials science information.
As a showcase of the framework's capabilities, the Crystal Toolkit app allows you to import, view, analyze and
transform crystal structures and molecules.


Crystal Toolkit Demonstration App
---------------------------------

The new Materials Project website is powered by the Crystal Toolkit framework, visit it
`here. <https://next-gen.materialsproject.org>`_. This includes the original "Crystal
Toolkit" app `available here <https://next-gen.materialsproject.org/toolkit>`_.


Crystal Toolkit Web Framework
-----------------------------

Crystal Toolkit is designed as a modular, object-oriented suite of UI components
built upon the `Dash framework by Plotly <https://dash.plot.ly>`_. The Crystal Toolkit web app is just
one example of using these components.

The custom Dash components developed for use by Crystal Toolkit are available at
`dash-mp-components <https://github.com/materialsproject/dash-mp-components>`_, and
powered by our custom React components available at
`mp-react-components <https://github.com/materialsproject/mp-react-components>`_. These
can be explored interactively in our
`Storybook <https://materialsproject.github.io/mp-react-components/?path=/story/introduction-mp-react-components--page>`_.
These components can also be installed and used independently of Crystal Toolkit.

Installation
------------

You can ``pip install crystal-toolkit``.

For Jupyter integration, please see the `additional installation steps <jupyter>`_.


Dash 2.x Migration
------------------

Crystal Toolkit works with both Dash 1.x and Dash 2.x. Several design choices were made
before Dash 2.x was developed that may be re-evaluated in future as new functionality
becomes available.


Development Team
----------------

The `Crystal Toolkit Development Team <https://github.com/materialsproject/crystaltoolkit/graphs/contributors>`_ includes:

* `Matthew Horton <https://github.com/mkhorton>`_, project lead

Contributors

* `Cody O'Donnell <https://github.com/codytodonnell>`_ primary developer of custom React components
* `François Chabbey <https://github.com/chabb>`_ for development of React components
* `Jimmy Shen <https://github.com/jmmshn>`_ contributed pythreejs support, surface plotting, initial arrows/axes support, and various bug fixes
* `Joey Montoya <https://github.com/JosephMontoya-TRI>`_ contributed Pourbaix component
* `Shyam Dwaraknath <https://github.com/shyamd>`_ for planned contributions for ellipsoid support and architectural design
* `Donny Winston <https://github.com/dwinston>`_, assisted by `Tyler Huntington <https://github.com/tylerhuntington>`_, for helping embed Crystal Toolkit in a Django app
* `Matt McDermott <https://github.com/mattmcdermott>`_ contributed phase diagram, X-ray Diffraction, X-ray Absorption Spectrum components
* `Jason Munro <https://github.com/munrojm>`_ contributed band structure component
* `Stephen Weitzner <https://github.com/sweitzner>`_ contributed POV-Ray integration (in progress)
* `Richard Tran <https://github.com/CifLord>`_ for contributing plotly-powered Wulff shapes to pymatgen, which Crystal Toolkit uses
* `Guy Moore <https://github.com/guymoore13>`_ for contributing magnetic moment visualization


New contributors are welcome, please see our `Code of Conduct. <https://github.com/materialsproject/crystaltoolkit/blob/master/code-of-conduct.md>`_
