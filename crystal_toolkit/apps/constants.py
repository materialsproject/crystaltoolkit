from collections import defaultdict
from monty.serialization import loadfn
from crystal_toolkit import MODULE_PATH
from pydash import set_, get

APP_METADATA = loadfn(MODULE_PATH / "apps/app_metadata.yaml")

# List of URLs available in the website
_BASE_URL = "https://materialsproject.org/"
_apps_sitemap = []

# Construct a nested dictionary showing the relationship between apps
# based on their urls, used for About page etc.
APP_TREE = {}
for app_class_name, metadata in APP_METADATA.items():
    if metadata["url"] and (not metadata["url"].startswith("http")):
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
