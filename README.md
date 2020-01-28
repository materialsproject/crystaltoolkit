# Crystal Toolkit

**Crystal Toolkit is not ready for the public yet! Please wait for a release announcement soon, thank you :-)**   

[![Pytest Status](https://github.com/materialsproject/crystaltoolkit/workflows/pytest_and_docs/badge.svg)](https://github.com/materialsproject/crystaltoolkit/actions?query=workflow%3Apytest_and_docs)
[![Visual Regression Test Status](https://percy.io/static/images/percy-badge.svg)](https://percy.io/Materials-Project/crystaltoolkit)
[![Docker Build Status](https://img.shields.io/docker/cloud/build/materialsproject/crystaltoolkit)](https://hub.docker.com/repository/docker/materialsproject/crystaltoolkit/general)
[![Release](https://github.com/materialsproject/crystaltoolkit/workflows/release/badge.svg)](https://github.com/materialsproject/crystaltoolkit/actions?query=workflow%3Arelease)

## Documentation

[Documentation can be found at docs.crystaltoolkit.org](https://docs.crystaltoolkit.org)

## Team and Contribution Policy

The [Crystal Toolkit Development Team](https://github.com/materialsproject/crystaltoolkit/graphs/contributors) includes:

* [Matthew Horton](https://github.com/mkhorton), lead
* [Jimmy Shen](https://github.com/jmmshn) contributed pythreejs support, surface plotting, initial arrows/axes support, and various bug fixes
* [Joey Montoya](https://github.com/JosephMontoya-TRI) contributed Pourbaix component
* [Shyam Dwaraknath](https://github.com/shyamd) for planned contributions for ellipsoid support and architectural design
* [Donny Winston](https://github.com/dwinston), assisted by [Tyler Huntington](https://github.com/tylerhuntington), for helping embed Crystal Toolkit in a Django app
* [Matt McDermott](https://github.com/mattmcdermott) contributed phase diagram, X-ray Diffraction, X-ray Absorption Spectrum components
* [Jason Munro](https://github.com/munrojm) contributed band structure component
* [Stephen Weitzner](https://github.com/sweitzner) contributed POV-Ray integration (in progress)
* [Richard Tran](https://github.com/richardtran415) for planned contribution of Wulff shape component

New contributors are welcome, please see our [Code of Conduct.](code-of-conduct.md) If you are a new contributor please modify this README in your Pull Request to add your name to the list.

## Future of This Repository

The Crystal Toolkit repo currently contains three major parts:

* An object-orientated Python framework for rendering materials science data based on the schema employed by the Materials Proejct
* A few custom Plotly Dash components (Simple3DSceneComponent, JSONComponent, GraphComponent)
* Some example apps using these components

It is likely the custom Plotly Dash components might be spun off into a separate repo at some point to reduce the complexity of the Crystal Toolkit repo itself.

## Acknowledgements

Thank you to all the authors and maintainers of the libraries Crystal Toolkit 
depends upon, and in particular [pymatgen](http://pymatgen.org) for crystallographic 
analysis and [Dash from Plotly](https://plot.ly/products/dash/) for their web app framework.

Thank you to the [NERSC Spin](http://www.nersc.gov/users/data-analytics/spin/) service for
hosting the app and for their technical support.

Cross-browser Testing Platform and Open Source <3 generously provided by [Sauce Labs](https://saucelabs.com)

## Contact

Please contact @mkhorton with any queries or add an issue on the [GitHub Issues](https://github.com/materialsproject/crystaltoolkit/issues) page.
