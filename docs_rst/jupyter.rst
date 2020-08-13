===================
Jupyter Integration
===================

Crystal Toolkit offers integration with JupyterLab to
allow easy viewing of crystal structures and other Materials Project
data interactively.

Installation
------------

There are two steps to using Crystal Toolkit inside Jupyter:

1. Make sure Jupyter Lab is installed and run using ``jupyter lab``, version 2.x.
   Crystal Toolkit is not supported in the older Jupyter notebooks or older versions 
   of Jupyter Lab.

2. Ensure Crystal Toolkit is installed as normal, ``pip install crystal-toolkit --upgrade``

3. Install the Crystal Toolkit extension in the same environment you run ``jupyter lab`` from using
   ``jupyter labextension install crystaltoolkit-extension``

4. Restart Jupyter Lab completely. You be asked to perform a "build," click OK and it's normal 
   for this to take a minute. After this it's ready to use!

Usage
-----

To use, simply ``import crystal_toolkit`` and use ``pymatgen`` as normal for crystal structures
to be shown using Crystal Toolkit.
