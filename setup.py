# -*- coding: utf-8 -*-
from setuptools import find_namespace_packages, setup
from crystal_toolkit._version import __version__ as fallback_version

if "+" in fallback_version:
    fallback_version = fallback_version.split("+")[0]

setup(
    name="crystal_toolkit",
    use_scm_version={
        "root": ".",
        "relative_to": __file__,
        "write_to": "crystal_toolkit/_version.py",
        "write_to_template": '__version__ = "{version}"',
        "fallback_version": fallback_version,
        "search_parent_directories": True,
    },
    setup_requires=["setuptools_scm"],
    description="""Crystal Toolkit is a web app framework from the Materials Project allowing Python
    developers to easily make an interactive web app to display materials science information. As a
    showcase of the framework’s capabilities, the Crystal Toolkit app allows you to import, view,
    analyze and transform crystal structures and molecules.""",
    author="Matthew Horton",
    author_email="mkhorton@lbl.gov",
    url="https://github.com/materialsproject/crystaltoolkit",
    packages=find_namespace_packages(include=["crystal_toolkit.*"]),
    install_requires=[
        "pymatgen",
        "webcolors",
        "crystaltoolkit-extension",
        "shapely",
        "scikit-learn",
        "scikit-image"
    ],
    extras_require={
        "server": [
            "dash<2.6",
            "dash-daq",
            "gunicorn[gevent]",
            "redis",
            "Flask-Caching",
            "dash-mp-components",
            "robocrys",
            "habanero",
            "hiphive",
            "dscribe",
            "dash-extensions<=0.1.5",
        ],
        "fermi": ["ifermi", "pyfftw"],
        "vtk": ["dash-vtk"],
        "localenv": ["dscribe"],
        "figures": ["kaleido"],
        "dev": [
            "black",
            "pre-commit",
            "dash[testing]<2.6",
            "sphinx_rtd_theme",
            "recommonmark",
            "dephell",
            "jinja2<3.1"

        ]
    },
    python_requires=">=3.8,<3.11",
    license="modified BSD",
    zip_safe=False,
)
