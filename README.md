# Crystal Toolkit

# Call for new contributors

Crystal Toolkit is an academic project. A manuscript is in preparation to detail the design goals of Crystal Toolkit and achievements to date.

**If you are interested in getting involved in Crystal Toolkit and are not already, it is not too late to be included in this manuscript, but please get in touch with mkhorton@lbl.gov ASAP.** Include information on the specific contributions that you would like to make (e.g. this may include adding features, addressing bugs, writing documentation, manuscript preparation, community engagement, writing tests, and the like), and if these align with the project we can formally add you to the development team.

Following a discussion with a potential contributor, "new contributor" issues are assigned. A current list of new contributor issues can be seen [here](https://github.com/materialsproject/crystaltoolkit/labels/new-contributor).

## Status

[![Pytest Status](https://github.com/materialsproject/crystaltoolkit/workflows/pytest_and_docs/badge.svg)](https://github.com/materialsproject/crystaltoolkit/actions?query=workflow%3Apytest_and_docs)
[![Visual Regression Test Status](https://percy.io/static/images/percy-badge.svg)](https://percy.io/Materials-Project/crystaltoolkit)
[![Docker Build Status](https://img.shields.io/docker/cloud/build/materialsproject/crystaltoolkit)](https://hub.docker.com/repository/docker/materialsproject/crystaltoolkit/general)
[![Release](https://github.com/materialsproject/crystaltoolkit/workflows/release/badge.svg)](https://github.com/materialsproject/crystaltoolkit/actions?query=workflow%3Arelease)

## Documentation

[Documentation can be found at docs.crystaltoolkit.org](https://docs.crystaltoolkit.org)

## Example Apps

|                                             |                                                                                                                                                                 |                                                                                                                                                       |                                                                                                                                                                                   |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`bandstructure.py`**                      | [![Launch Binder]](https://mybinder.org/v2/gh/materialsproject/crystaltoolkit/main?labpath=crystal_toolkit/apps/examples/bandstructure.py)                      | [![View on GitHub]](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/bandstructure.py)                      | [![Open in Google Colab]](https://colab.research.google.com/github/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/bandstructure.py)                      |
| **`basic_hello_structure.py`**              | [![Launch Binder]](https://mybinder.org/v2/gh/materialsproject/crystaltoolkit/main?labpath=crystal_toolkit/apps/examples/basic_hello_structure.py)              | [![View on GitHub]](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/basic_hello_structure.py)              | [![Open in Google Colab]](https://colab.research.google.com/github/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/basic_hello_structure.py)              |
| **`basic_hello_structure_interactive.py`**  | [![Launch Binder]](https://mybinder.org/v2/gh/materialsproject/crystaltoolkit/main?labpath=crystal_toolkit/apps/examples/basic_hello_structure_interactive.py)  | [![View on GitHub]](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/basic_hello_structure_interactive.py)  | [![Open in Google Colab]](https://colab.research.google.com/github/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/basic_hello_structure_interactive.py)  |
| **`basic_hello_world.py`**                  | [![Launch Binder]](https://mybinder.org/v2/gh/materialsproject/crystaltoolkit/main?labpath=crystal_toolkit/apps/examples/basic_hello_world.py)                  | [![View on GitHub]](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/basic_hello_world.py)                  | [![Open in Google Colab]](https://colab.research.google.com/github/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/basic_hello_world.py)                  |
| **`diffraction.py`**                        | [![Launch Binder]](https://mybinder.org/v2/gh/materialsproject/crystaltoolkit/main?labpath=crystal_toolkit/apps/examples/diffraction.py)                        | [![View on GitHub]](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/diffraction.py)                        | [![Open in Google Colab]](https://colab.research.google.com/github/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/diffraction.py)                        |
| **`diffraction_dynamic.py`**                | [![Launch Binder]](https://mybinder.org/v2/gh/materialsproject/crystaltoolkit/main?labpath=crystal_toolkit/apps/examples/diffraction_dynamic.py)                | [![View on GitHub]](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/diffraction_dynamic.py)                | [![Open in Google Colab]](https://colab.research.google.com/github/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/diffraction_dynamic.py)                |
| **`diffraction_empty.py`**                  | [![Launch Binder]](https://mybinder.org/v2/gh/materialsproject/crystaltoolkit/main?labpath=crystal_toolkit/apps/examples/diffraction_empty.py)                  | [![View on GitHub]](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/diffraction_empty.py)                  | [![Open in Google Colab]](https://colab.research.google.com/github/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/diffraction_empty.py)                  |
| **`kwarg_inputs.py`**                       | [![Launch Binder]](https://mybinder.org/v2/gh/materialsproject/crystaltoolkit/main?labpath=crystal_toolkit/apps/examples/kwarg_inputs.py)                       | [![View on GitHub]](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/kwarg_inputs.py)                       | [![Open in Google Colab]](https://colab.research.google.com/github/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/kwarg_inputs.py)                       |
| **`phase_diagram.py`**                      | [![Launch Binder]](https://mybinder.org/v2/gh/materialsproject/crystaltoolkit/main?labpath=crystal_toolkit/apps/examples/phase_diagram.py)                      | [![View on GitHub]](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/phase_diagram.py)                      | [![Open in Google Colab]](https://colab.research.google.com/github/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/phase_diagram.py)                      |
| **`pourbaix.py`**                           | [![Launch Binder]](https://mybinder.org/v2/gh/materialsproject/crystaltoolkit/main?labpath=crystal_toolkit/apps/examples/pourbaix.py)                           | [![View on GitHub]](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/pourbaix.py)                           | [![Open in Google Colab]](https://colab.research.google.com/github/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/pourbaix.py)                           |
| **`structure.py`**                          | [![Launch Binder]](https://mybinder.org/v2/gh/materialsproject/crystaltoolkit/main?labpath=crystal_toolkit/apps/examples/structure.py)                          | [![View on GitHub]](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/structure.py)                          | [![Open in Google Colab]](https://colab.research.google.com/github/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/structure.py)                          |
| **`structure_magnetic.py`**                 | [![Launch Binder]](https://mybinder.org/v2/gh/materialsproject/crystaltoolkit/main?labpath=crystal_toolkit/apps/examples/structure_magnetic.py)                 | [![View on GitHub]](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/structure_magnetic.py)                 | [![Open in Google Colab]](https://colab.research.google.com/github/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/structure_magnetic.py)                 |
| **`transformations.py`**                    | [![Launch Binder]](https://mybinder.org/v2/gh/materialsproject/crystaltoolkit/main?labpath=crystal_toolkit/apps/examples/transformations.py)                    | [![View on GitHub]](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/transformations.py)                    | [![Open in Google Colab]](https://colab.research.google.com/github/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/transformations.py)                    |
| **`transformations_minimal.py`**            | [![Launch Binder]](https://mybinder.org/v2/gh/materialsproject/crystaltoolkit/main?labpath=crystal_toolkit/apps/examples/transformations_minimal.py)            | [![View on GitHub]](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/transformations_minimal.py)            | [![Open in Google Colab]](https://colab.research.google.com/github/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/transformations_minimal.py)            |
| **`write_structure_screenshot_to_file.py`** | [![Launch Binder]](https://mybinder.org/v2/gh/materialsproject/crystaltoolkit/main?labpath=crystal_toolkit/apps/examples/write_structure_screenshot_to_file.py) | [![View on GitHub]](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/write_structure_screenshot_to_file.py) | [![Open in Google Colab]](https://colab.research.google.com/github/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/write_structure_screenshot_to_file.py) |

[Launch Binder]: https://mybinder.org/badge_logo.svg
[View on GitHub]: https://img.shields.io/badge/View-GitHub-darkblue?logo=github
[Open in Google Colab]: https://colab.research.google.com/assets/colab-badge.svg

## Team and Contribution Policy

The [Crystal Toolkit Development Team](https://github.com/materialsproject/crystaltoolkit/graphs/contributors) includes:

* [Matthew Horton](https://github.com/mkhorton), lead
* [François Chabbey](<https://github.com/chabb>) for React components
* [Jimmy Shen](https://github.com/jmmshn) contributed pythreejs support, surface plotting, initial arrows/axes support, and various bug fixes
* [Joey Montoya](https://github.com/JosephMontoya-TRI) contributed Pourbaix component
* [Shyam Dwaraknath](https://github.com/shyamd) for planned contributions for ellipsoid support and architectural design
* [Donny Winston](https://github.com/dwinston), assisted by [Tyler Huntington](https://github.com/tylerhuntington), for helping embed Crystal Toolkit in a Django app
* [Matt McDermott](https://github.com/mattmcdermott) contributed phase diagram, X-ray Diffraction, X-ray Absorption Spectrum components
* [Jason Munro](https://github.com/munrojm) contributed band structure component
* [Stephen Weitzner](https://github.com/sweitzner) contributed POV-Ray integration (in progress)
* [Richard Tran](https://github.com/CifLord) for contributing plotly-powered Wulff shapes to pymatgen, which Crystal Toolkit uses
* [Guy Moore](https://github.com/guymoore13) for contributing magnetic moment visualization

New contributors are welcome, please see our [Code of Conduct.](code-of-conduct.md) If you are a new contributor please modify this README in your Pull Request to add your name to the list.

## Future of This Repository

The Crystal Toolkit repository is home of an object-oriented Python framework for rendering materials science data based on the schema employed by the Materials Project.

The custom Plotly Dash components that power Crystal Toolkit are now maintained in a [separate repository](https://github.com/materialsproject/dash-mp-components) for ease of development, as well as the [custom React components](https://github.com/materialsproject/mp-react-components). These components were formerly included in the Crystal Toolkit repo, and are still considered part of Crystal Toolkit in spirit.

There are some [important issues](https://github.com/materialsproject/crystaltoolkit/issues/265) still to be resolved, as well as general improvements to documentation and test suite planned. Some [currently-private code](https://github.com/materialsproject/crystaltoolkit/issues/264) is also planned to be re-incorporated into the public Crystal Toolkit repo.

## Acknowledgements

Thank you to all the authors and maintainers of the libraries Crystal Toolkit
depends upon, and in particular [pymatgen](http://pymatgen.org) for crystallographic
analysis and [Dash from Plotly](https://plot.ly/products/dash/) for their web app framework.

Thank you to the [NERSC Spin](https://www.nersc.gov/systems/spin) service for
hosting the app and for their technical support.

Cross-browser Testing Platform and Open Source <3 generously provided by [Sauce Labs](https://saucelabs.com)

## Contact

Please contact @mkhorton with any queries or add an issue on the [GitHub Issues](https://github.com/materialsproject/crystaltoolkit/issues) page.
