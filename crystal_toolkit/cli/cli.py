from pathlib import Path

import rich_click as click
from tqdm import tqdm


@click.group()
def cli():
    pass


@cli.command()
@click.argument("input", required=True)
def render(input):
    from pymatgen.analysis.local_env import CrystalNN
    from pymatgen.core.structure import Structure

    from crystal_toolkit.core.scene import Scene
    from crystal_toolkit.helpers.povray.renderer import POVRayRenderer

    input_path = Path(input)
    if input_path.is_file():
        paths = [input_path]  # load CIF
    else:
        paths = list(input_path.glob("*.cif"))

    r = POVRayRenderer()

    structures = {}
    for path in tqdm(paths, desc="Reading structures"):
        try:
            structures[path] = Structure.from_file(path)
        except Exception as exc:
            print(f"Failed to parse {path}: {exc}")

    def _get_scene(struct: Structure) -> Scene:
        # opinionated defaults, would be better to be customizable
        nn = CrystalNN()
        sg = nn.get_bonded_structure(struct)
        return sg.get_scene(explicitly_calculate_polyhedra_hull=True)

    scenes = {}
    for path, structure in tqdm(structures.items(), desc="Preparing scenes"):
        try:
            scenes[path] = _get_scene(structure)
        except Exception as exc:
            print(f"Failed to parse {path}: {exc}")

    for path, scene in tqdm(scenes.items(), desc="Rendering scenes"):
        r.write_scene_to_file(scene, filename=f"{path.stem}.png")


if __name__ == "__main__":
    cli()
