import json
import os
from setuptools import setup, find_packages


with open(os.path.join("crystal_toolkit", "package.json")) as f:
    package = json.load(f)

package_name = package["name"].replace(" ", "_").replace("-", "_")


def requirements(fname):
    with open(fname, "r") as f:
        reqs = f.read().splitlines()
    reqs = [
        r.strip().split()[0]
        for r in reqs
        if r.strip() and not r.strip().startswith("#")
    ]
    reqs = [r.replace("==", ">=") for r in reqs if ">=" in r or "==" in r]
    return reqs


setup(
    name=package_name,
    version=package["version"],
    author=package["author"],
    packages=find_packages(),
    package_data={"": ["*.json", "*.js", "*.yaml"]},
    include_package_data=True,
    license=package["license"],
    description=package["description"] if "description" in package else package_name,
    install_requires=requirements("requirements.txt"),
    python_requires=">=3.7",
)
