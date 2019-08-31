import base64
import zlib
import urllib.parse
import requests
import warnings
from json.decoder import JSONDecodeError
from json import dumps


def view(struct_or_mol, host="http://localhost:8050"):
    """
    Generate a temporary link to view your structure online using Material Project's
    Crystal Toolkit.

    Note that your structure or molecule is sent to the remote host to be viewed.
    Structures or molecules are not stored permanently or otherwise processed, but
    only retained for the purposes of visualization for the user who requested the link.
    The full source code of the viewer is available online.

    Links expire by default after 7 days of last being viewed, but no guarantees
    are provided while this service is currently in beta.
    """

    warnings.warn("This feature is currently in beta.")

    try:
        req = requests.request("GET", urllib.parse.urljoin(host, "/version"))
    except:
        raise ConnectionError(
            "Could not get a response from Crystal Toolkit, it may be offline "
            "or down for maintenance, or you may need to upgrade pymatgen."
        )

    if req.status_code != 200:
        raise ConnectionError(
            "Could not get correct response from Crystal Toolkit, it may be "
            "offline or down for maintenance, or you may need to upgrade crystal-toolkit."
        )

    try:
        json = req.json()
    except JSONDecodeError:
        raise ConnectionError(
            "Could not get correct reponse from Crystal Toolkit, the version "
            "deployed online may need to be upgraded."
        )

    if json.get("crystal_toolkit_api_version", None) != 1:
        raise RuntimeError(
            "Crystal Toolkit version has changed, you may need to upgrade "
            "pymatgen for view function to work correctly."
        )

    try:
        payload = dumps(struct_or_mol.as_dict(verbosity=0))
    except TypeError:
        # TODO: remove this, necessary for Slab(?), some structure subclasses don't have verbosity
        payload = dumps(struct_or_mol.as_dict())

    req = requests.post(urllib.parse.urljoin(host, "/generate_token"), json=payload)

    if req.status_code != 200:
        raise ConnectionError(
            "Could not get correct response from Crystal Toolkit, it may be "
            "offline or down for maintenance, or you may need to upgrade crystal-toolkit."
        )

    try:
        json = req.json()
    except JSONDecodeError:
        raise Exception(
            "Could not get correct reponse from Crystal Toolkit, the version "
            "deployed online may need to be upgraded or this may be a bug."
        )

    if json.get("error", None):
        raise Exception(json["error"])
    else:
        token = json["token"]

    url = urllib.parse.urljoin(host, f"/?token={token}")

    try:
        if get_ipython().__class__.__name__ == "ZMQInteractiveShell":
            in_jupyter = True
        else:
            in_jupyter = False
    except NameError:
        in_jupyter = False

    if in_jupyter:
        from IPython.core.display import display, HTML

        display(
            HTML(
                "<a href='{}' target='_blank'>Click to open structure or "
                "molecule in viewer.</a>".format(url)
            )
        )
    else:
        print(url)
