# crystaltoolkit-extension

A JupyterLab extension for rendering blah files.

## Prerequisites

* JupyterLab 1.0 or later

## Installation

```bash
jupyter labextension install crystaltoolkit-extension
```

## Development

For a development install (requires npm version 4 or later), do the following in the repository directory:

```bash
npm install
jupyter labextension link .
```

To rebuild the package and the JupyterLab app:

```bash
npm run build
jupyter lab build
```

