"""Export wrapper for POV-Ray.

For creating publication quality plots.
"""

from __future__ import annotations

import os
import shutil
from tempfile import TemporaryDirectory
from warnings import warn
import subprocess
from pathlib import Path

import numpy as np
from jinja2 import Environment  # TODO: add to requirements
from matplotlib.colors import to_hex

from crystal_toolkit.settings import SETTINGS, MODULE_PATH
from crystal_toolkit.core.scene import Scene, Primitive, Spheres, Cylinders, Lines


class POVRayRenderer:
    """
    A class to interface with the POV-Ray command line tool (ray tracer).
    """

    _TEMPLATES = {
        path.stem: path.read_text()
        for path in (MODULE_PATH / "helpers" / "povray" / "templates").glob("*")
    }
    _ENV = Environment()

    def write_scene_to_file(self, scene: Scene, filename: str | Path):
        """
        Render a Scene to a PNG file using POV-Ray.
        """

        current_dir = Path.cwd()

        with TemporaryDirectory() as temp_dir:

            os.chdir(temp_dir)

            self.write_povray_input_scene_and_settings(
                scene, image_filename="crystal_toolkit_scene.png"
            )
            self.call_povray()

            shutil.copy("crystal_toolkit_scene.png", current_dir / filename)

        os.chdir(current_dir)

        return

    @staticmethod
    def call_povray(
        povray_args: tuple[str] = ("render.ini",),
        povray_path: str = SETTINGS.POVRAY_PATH,
    ):
        """
        Run POV-Ray. Prefer `render_scene` method unless advanced user.
        """

        povray_args = [povray_path, *povray_args]

        with subprocess.Popen(
            povray_args,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            close_fds=True,
        ) as proc:
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(
                    f"{povray_path} exit code: {proc.returncode}, error: {stderr!s}."
                    f"\nstdout: {stdout!s}. Please check your POV-Ray installation."
                )

    @staticmethod
    def write_povray_input_scene_and_settings(
        scene,
        scene_filename="crystal_toolkit_scene.pov",
        settings_filename="render.ini",
        image_filename="crystal_toolkit_scene.png",
    ):
        """
        Prefer `render_scene` method unless advanced user.
        """

        with open(scene_filename, "w") as f:

            scene_str = POVRayRenderer.scene_to_povray(scene)

            f.write(POVRayRenderer._TEMPLATES["header"])
            f.write(POVRayRenderer._TEMPLATES["camera"])
            f.write(POVRayRenderer._TEMPLATES["lights"])
            f.write(scene_str)

        render_settings = POVRayRenderer._ENV.from_string(
            POVRayRenderer._TEMPLATES["render"]
        ).render(filename=scene_filename, image_filename=image_filename)
        with open(settings_filename, "w") as f:
            f.write(render_settings)

    @staticmethod
    def scene_to_povray(scene: Scene) -> str:

        povray_str = ""

        for item in scene.contents:

            if isinstance(item, Primitive):
                povray_str += POVRayRenderer.primitive_to_povray(obj=item)

            elif isinstance(item, Scene):
                povray_str += POVRayRenderer.scene_to_povray(scene=item)

        return povray_str

    @staticmethod
    def primitive_to_povray(obj: Primitive) -> str:

        vect = "{:.4f},{:.4f},{:.4f}"

        if isinstance(obj, Spheres):

            positions = obj.positions
            positions = [vect.format(*pos) for pos in positions]
            color = POVRayRenderer._format_color_to_povray(obj.color)

            return POVRayRenderer._ENV.from_string(
                POVRayRenderer._TEMPLATES["sphere"]
            ).render(positions=positions, radius=obj.radius, color=color)

        elif isinstance(obj, Cylinders):

            position_pairs = [
                [vect.format(*ipos), vect.format(*fpos)]
                for ipos, fpos in obj.positionPairs
            ]
            color = POVRayRenderer._format_color_to_povray(obj.color)
            return POVRayRenderer._ENV.from_string(
                POVRayRenderer._TEMPLATES["cylinder"]
            ).render(posPairs=position_pairs, color=color)

        elif isinstance(obj, Lines):
            pos1, pos2 = (
                obj.positions[0::2],
                obj.positions[1::2],
            )
            cylCaps = {tuple(pos) for pos in obj.positions}
            cylCaps = [vect.format(*pos) for pos in cylCaps]
            position_pairs = [
                [vect.format(*ipos), vect.format(*fpos)]
                for ipos, fpos in zip(pos1, pos2)
            ]
            return POVRayRenderer._ENV.from_string(
                POVRayRenderer._TEMPLATES["line"]
            ).render(posPairs=position_pairs, cylCaps=cylCaps)

        elif isinstance(obj, Primitive):
            warn(
                f"Skipping {type(obj)}, not yet implemented. Submit PR to add support."
            )

    @staticmethod
    def _format_color_to_povray(color: str) -> str:
        vect = "{:.4f},{:.4f},{:.4f}"
        color = to_hex(color)
        color = color.replace("#", "")
        color = tuple(int(color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
        color = f"rgb<{vect.format(*color)}>"
        return color
