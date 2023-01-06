from __future__ import annotations

from collections import defaultdict

from monty.serialization import loadfn
from pydash import get, set_

from crystal_toolkit.settings import SETTINGS

APP_METADATA = loadfn(SETTINGS.APP_METADATA)

# list of URLs available in the website
_BASE_URL = "https://materialsproject.org/"
_apps_sitemap = []

# Construct a nested dictionary showing the relationship between apps
# based on their urls, used for About page etc.
APP_TREE = {}
for app_class_name, metadata in APP_METADATA.items():
    if metadata["url"] and not metadata["url"].startswith("http"):
        _apps_sitemap.append(_BASE_URL + metadata["url"])
        path = metadata["url"].replace("/", ".")
        if not get(APP_TREE, path):
            set_(APP_TREE, path, {"NAME": app_class_name})
        else:
            get(APP_TREE, path)["NAME"] = app_class_name

# This is currently hard-coded
_MP_APP_CATEGORY_ORDER = [
    "Explore and Search",
    "Analysis Tools",
    "Characterization",
    "Reference Data",
]

MP_APPS_BY_CATEGORY = defaultdict(list)

MP_APPS_BY_CATEGORY = {
    category: MP_APPS_BY_CATEGORY[category] for category in _MP_APP_CATEGORY_ORDER
}
