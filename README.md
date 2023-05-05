# Crystal Toolkit

## Interested in contributing?

A current list of new contributor issues can be seen [here](https://github.com/materialsproject/crystaltoolkit/labels/new-contributor).
If you would like a new-contributor issue assigned, get in touch with project maintainers!

## Status

[![Tests](https://github.com/materialsproject/crystaltoolkit/actions/workflows/pytest-docs.yml/badge.svg)](https://github.com/materialsproject/crystaltoolkit/actions/workflows/pytest-docs.yml)
[![Visual Regression Test Status](https://percy.io/static/images/percy-badge.svg)](https://percy.io/Materials-Project/crystaltoolkit)
[![Docker Build Status](https://img.shields.io/docker/cloud/build/materialsproject/crystaltoolkit)](https://hub.docker.com/repository/docker/materialsproject/crystaltoolkit/general)
[![Release](https://github.com/materialsproject/crystaltoolkit/actions/workflows/release.yml/badge.svg)](https://github.com/materialsproject/crystaltoolkit/actions/workflows/release.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/materialsproject/crystaltoolkit/main.svg)](https://results.pre-commit.ci/latest/github/materialsproject/crystaltoolkit/main)
[![arXiv link](https://img.shields.io/badge/arXiv-2302.06147-blue)](https://arxiv.org/abs/2302.06147)

## Installation

```sh
pip install crystal-toolkit
```

## Documentation

Documentation can be found at [docs.crystaltoolkit.org](https://docs.crystaltoolkit.org).

## Example Apps

| Description                                                                                                                                                                                                                                                                                                                                                               | &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------ |
| [bandstructure.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/bandstructure.py)<br>  Demonstrates capabilities of the `BandstructureAndDosComponent` component                                                                                                                                                            | [![Launch Codespace]][create codespace]    |
| [basic_hello_structure.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/basic_hello_structure.py)<br>  Uses `StructureMoleculeComponent` to show a simple `pymatgen` structure                                                                                                                                              | [![Launch Codespace]][create codespace]    |
| [basic_hello_structure_interactive.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/basic_hello_structure_interactive.py)<br>  Adds a button to the `basic_hello_structure.py` to toggle between two structures interactively                                                                                               | [![Launch Codespace]][create codespace]    |
| [basic_hello_world.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/basic_hello_world.py)<br>  Bare-bones example showing how to render the text "Hello scientist!" in Dash app                                                                                                                                             | [![Launch Codespace]][create codespace]    |
| [diffraction.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/diffraction.py)<br>  Demonstrates capabilities of the `XRayDiffractionComponent` component                                                                                                                                                                    | [![Launch Codespace]][create codespace]    |
| [diffraction_dynamic.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/diffraction_dynamic.py)<br>  Adds a button to `diffraction.py` to load a new structure on the fly                                                                                                                                                     | [![Launch Codespace]][create codespace]    |
| [diffraction_empty.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/diffraction_empty.py)<br>  Shows `XRayDiffractionComponent` can be mounted without a passing structure                                                                                                                                                  | [![Launch Codespace]][create codespace]    |
| [kwarg_inputs.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/kwarg_inputs.py)<br>  Shows off boolean input (aka toggle), matrix input and slider input components                                                                                                                                                         | [![Launch Codespace]][create codespace]    |
| [phase_diagram.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/phase_diagram.py)<br>  Combines `MPRester.get_entries_in_chemsys()` and the `PhaseDiagram` component to plot the Li-O-Co convex hull                                                                                                                        | [![Launch Codespace]][create codespace]    |
| [pourbaix.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/pourbaix.py)<br>  Combines `MPRester.get_pourbaix_entries()` and the `PourbaixDiagramComponent` to plot the Fe-CO Pourbaix diagram                                                                                                                               | [![Launch Codespace]][create codespace]    |
| [structure.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/structure.py)<br>  Show cases multiple layout options for the `StructureMoleculeComponent`                                                                                                                                                                      | [![Launch Codespace]][create codespace]    |
| [structure_magnetic.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/structure_magnetic.py)<br>  Plots a structure with magnetic moments                                                                                                                                                                                    | [![Launch Codespace]][create codespace]    |
| [matbench_dielectric_structure_on_hover.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/matbench_dielectric_structure_on_hover.py)<br>  Creates a scatter plot hooked up to a `StructureMoleculeComponent` and `DataTable` that show the structure and highlight the table row corresponding to the hovered scatter point. | [![Launch Codespace]][create codespace]    |
| [matbench_dielectric_datatable_xrd.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/matbench_dielectric_datatable_xrd.py)<br>  Renders a `DataTable` hooked up to a `StructureMoleculeComponent` and `XRayDiffractionComponent` so that hovering a table row will show the corresponding structure and its XRD pattern.     | [![Launch Codespace]][create codespace]    |
| [transformations.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/transformations.py)<br>  Combines `StructureMoleculeComponent` and `AllTransformationsComponent` to apply interactive structure transformations                                                                                                           | [![Launch Codespace]][create codespace]    |
| [transformations_minimal.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/transformations_minimal.py)<br>  Shows how to restrict the types of allowed transformations                                                                                                                                                       | [![Launch Codespace]][create codespace]    |
| [write_structure_screenshot_to_file.py](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/write_structure_screenshot_to_file.py)<br>  Shows to save interactive structure views as image files                                                                                                                                   | [![Launch Codespace]][create codespace]    |

[Launch Codespace]: https://img.shields.io/badge/Launch-Codespace-darkblue?logo=github
[create codespace]: https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=98350025

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
* [Janosh Riebesell](https://github.com/janosh) contributed Phonon band structure component, [3 example apps](https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/apps/examples/matbench_dielectric_structure_on_hover.py), tests
* [Stephen Weitzner](https://github.com/sweitzner) contributed POV-Ray integration (in progress)
* [Richard Tran](https://github.com/CifLord) for contributing plotly-powered Wulff shapes to pymatgen, which Crystal Toolkit uses
* [Guy Moore](https://github.com/guymoore13) for contributing magnetic moment visualization
* [Steve Zeltmann](https://github.com/sezelt) for contributing electron diffraction
* [Patrick Huck](https://github.com/tschaume), releases, operations, bugfixes and POC for MP / MPContribs

New contributors are welcome, please see our [Code of Conduct](code-of-conduct.md). If you are a new contributor please modify this README in your Pull Request to add your name to the list.

## Future of This Repository

The Crystal Toolkit repository is home of an object-oriented Python framework for rendering materials science data based on the schema employed by the Materials Project.

The custom Plotly Dash components that power Crystal Toolkit are now maintained in a [separate repository](https://github.com/materialsproject/dash-mp-components) for ease of development, as well as the [custom React components](https://github.com/materialsproject/mp-react-components). These components were formerly included in the Crystal Toolkit repo, and are still considered part of Crystal Toolkit in spirit.

There are some [important issues](https://github.com/materialsproject/crystaltoolkit/issues/265) still to be resolved, as well as general improvements to documentation and test suite planned. Some [currently-private code](https://github.com/materialsproject/crystaltoolkit/issues/264) is also planned to be re-incorporated into the public Crystal Toolkit repo.

## Acknowledgements

Thank you to all the authors and maintainers of the libraries Crystal Toolkit
depends upon, and in particular [pymatgen](http://pymatgen.org) for crystallographic
analysis and [Dash from Plotly](https://plot.ly/products/dash/) for their web app framework.

Thank you to the [NERSC Spin](https://nersc.gov/systems/spin) service for
hosting the app and for their technical support.

## Cite

To cite this work, see <https://arxiv.org/abs/2302.06147> and [citation.cff](citation.cff).

## Contact

Please contact @mkhorton with any queries or add an issue on the [GitHub Issues](https://github.com/materialsproject/crystaltoolkit/issues) page.
