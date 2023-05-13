import json
import os


def _fetch_version():
    HERE = os.path.abspath(os.path.dirname(__file__))

    for folder, _, _ in os.walk(HERE):
        try:
            with open(os.path.join(folder, "package.json")) as file:
                return json.load(file)["version"]
        except FileNotFoundError:
            pass

    raise FileNotFoundError(f"Could not find package.json under dir {HERE}")


__version__ = _fetch_version()
__all__ = ["__version__"]
