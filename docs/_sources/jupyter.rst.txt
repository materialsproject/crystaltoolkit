===================
Jupyter Integration
===================

Crystal Toolkit offers integration with JupyterLab to
allow easy viewing of crystal structures and other Materials Project
data interactively.

Installation
------------

There are two steps to using Crystal Toolkit inside Jupyter:

1. Make sure Jupyter Lab is installed and run using ``jupyter lab``. Crystal Toolkit is
   not supported in the older Jupyter notebooks.

2. Ensure Crystal Toolkit is installed as normal, ``pip install crystal-toolkit --upgrade``

3. Install `pythreejs <https://github.com/jupyter-widgets/pythreejs>`_ following their instructions.
   The most reliable way to do this seems to be ``conda install -c conda-forge pythreejs` for people
   who use the conda package manager.

4. Restart Jupyter Lab from the terminal. You may be asked to perform a "build," click OK and this
   may take a minute. After this it's ready to use!

Usage
-----

To use, simply ``from crystal_toolkit import view`` and use ``view(your_struct)`` for any structure.

.. image:: images/jupyter-demo.gif
  :align: center
  :alt: Demo of Jupyter functionality