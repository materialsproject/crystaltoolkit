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
   Crystal Toolkit is not supported in the older Jupyter notebooks.

2. Ensure Crystal Toolkit is installed as normal, ``pip install crystal-toolkit --upgrade``

3. Install the Crystal Toolkit extension, ``jupyter labextension install crystaltoolkit-extension``

4. Restart Jupyter Lab completely. You may be asked to perform a "build," click OK and this
   may take a minute. After this it's ready to use!

Usage
-----

To use, simply ``import crystal_toolkit` and use ``pymatgen`` as normal for crystal structures
to be shown using Crystal Toolkit.

.. image:: images/jupyter-demo.gif
  :align: center
  :alt: Demo of Jupyter functionality