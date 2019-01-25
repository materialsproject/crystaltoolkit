# Crystal Toolkit

**Crystal Toolkit is not ready for the public yet! Please wait for a release announcement soon, thank you :-)** 

# [Readme not ready yet]

## Table of Contents

## Installation and use

To use Crystal Toolkit, simply visit [https://viewer.materialsproject.org](https://viewer.materialsproject.org) (address subject to change).


If you would like to test Crystal Toolkit on your own computer, download and run our [Docker image from DockerHub](https://hub.docker.com/r/materialsproject/crystal_toolkit):

```python
docker container run -p 8000:8000 -e PMG_MAPI_KEY=YOUR_API_KEY_HERE materialsproject/crystal_toolkit
```

and then visit [http://localhost:8000](http://localhost:8000).

If you would like to use Crystal Toolkit for its library of UI components
for your own Dash app, you can pip install it:

```python
pip install crystal-toolkit
```

### Easy viewing of crystal structures and molecules from Python

Installing Crystal Toolkit via pip also gives you the useful command `view`:

```python
from crystal_toolkit import view_online
view_online(my_struct)  # returns https://viewer.materialsproject.org/?token=...
```

This will generate a link to view your crystal structure or molecule online. 

In future, support for online, interactive viewing of other classes are planned, 
in addition to inline viewing in a Jupyter notebook.

## Contributing

Contributions are welcome! [We have an open and inclusive contribution policy](...).

Please use the [Issues]() page to report bugs and feature requests, pull requests are also welcome.
This is the first significant web app we've developed using Dash and we're still figuring out 
best practices, so comments on architectural choices are also welcome.

Technical guidelines on contributions are as follows:

### Contribute an MPComponent

An `MPComponent` is designed to render an instance of an "MSONable"
object from a Materials Project software code.

Currently there are MPComponents for the following classes:

- `pymatgen.core.Structure`
- `pymatgen.core.Molecule`
- `pymatgen.analysis.graphs.StructureGraph`
- `pymatgen.analysis.graphs.MoleculeGraph`

See the current [Issues](???) page for any components that still need implementing.

Before using any MPComponents in your app, you must register your app object and cache
(if applicable) with Crystal Toolkit.

```python
import crystal_toolkit as ct
ct.register_app() # Optional, but required for interactivity
ct.register_cache() # Optional, but often useful for performance
```

To use an MPComponent, the standard initializer takes an `id` like any other Dash component and `contents`
which can be an instance of the corresponding MSONable class or `None`.

For example,

```python
import crystal_toolkit as ct
struct_component = ct.StructureMoleculeComponent(my_struct, id="my_structure_visualizer")
```

Then, you can add its default layout to your `app` using `struct_component.default_layout`
or, if you want more customizability, you can `print(struct_component)` and see
what other layouts it supports (for example, it might have an optional set of controls associated
with it).

#### Implementing an MPComponent

...

### Contribute a Crystal Toolkit Panel

A `PanelComponent` is a sub-class

#### Implementing a PanelComponent

### Contribute a React component

Some `MPComponents` require functionality not offered by core Dash components, 
for example the crystal viewer itself which requires 3D rendering capabilities.

If you need an additional React component, you will first need to set up 
your development environment using `npm install  ...`

...simply create `YourComponent.react.js`
in `~/src/components/`, import it in `~/src/index.js`, and run:

`builder...`

If you have any new dependencies, add them using `npm install -S ...`.

### Tests

Tests are ideal, however tests are not required to start contributing 
to Crystal Toolkit. Since Crystal Toolkit itself does not itself contain any new 
scientific analysis capabilities, but instead builds upon other libraries 
like [pymatgen](http://pymatgen.org), comprehensive testing isn't as 
mission critical. *However, tests are still encouraged wherever possible* 
and the long-term health of this project will rely on good testing.

New React components should have an example added to usage.py and edit `tests/?`

New subclasses of `MPComponent` and `PanelComponent` can have tests
written purely in Python, a good test for a `PanelComponent` would be to
test the output of `update_contents()`.

## Acknowledgements

Thank you to all the authors and maintainers of the libraries Crystal Toolkit 
depends upon, and in particular [pymatgen](http://pymatgen.org) for crystallographic 
analysis and [Dash from Plotly](https://plot.ly/products/dash/) for their web app framework. Thank you 
to the [NERSC Spin](http://www.nersc.gov/users/data-analytics/spin/) service for hosting the app and
for technical support.

## Contact

Please contact @mkhorton with any queries.
