===================
Jupyter Integration
===================

Crystal Toolkit offers integration with JupyterLab to
allow easy viewing of crystal structures and other Materials Project
data interactively.

Installation
------------

There are two steps to using Crystal Toolkit inside Jupyter:

1. Make sure Jupyter Lab is installed and run using ``jupyter lab``, version 3.x.
   Crystal Toolkit is not supported in the older Jupyter notebooks or older versions
   of Jupyter Lab.

2. Ensure Crystal Toolkit is installed as normal, ``pip install crystal-toolkit --upgrade``

3. Restart Jupyter Lab completely. You be asked to perform a "build," click OK and it's normal
   for this to take a minute. After this it's ready to use!

The extension may still work on Jupyter Lab 2.x by additionally running:

   ``jupyter labextension install crystaltoolkit-extension``

However 2.x is no longer supported, and this command does not need to be run with Jupyter Lab 3.x

Usage
-----

To use, simply ``import crystal_toolkit`` and use ``pymatgen`` as normal for crystal structures
to be shown using Crystal Toolkit.
