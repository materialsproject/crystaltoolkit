# mp-viewer (beta!)

Component for viewing crystallographic structures for the Materials Project.

**The current state of this repo is for testing and debugging, not for end users!**

There is a:

* Python component, `structure_vis_mp.py`, that will be submitted to pymatgen.vis -- in brief, it takes a `Structure` object, computes bonds and polyhedra using a `NearNeighbor` class into a `StructureGraph` and then displays this

* React/JavaScript component inside `src` -- it's quite minimal, the only external dependancies are `Three.js` and `orbit-controls-es6` -- React should not be necessary for the final version, it's just been useful for debugging (TODO: wrap into a `require` package for easy importing)

* A plot.ly Dash based UI, run `python app.py` to test
