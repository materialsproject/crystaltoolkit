"""Export wrapper for POV-Ray.

For creating publication quality plots.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import ClassVar
from warnings import warn

from jinja2 import Environment  # TODO: add to requirements
from matplotlib.colors import to_hex
import numpy as np

from crystal_toolkit.core.scene import Cylinders, Lines, Primitive, Scene, Spheres
from crystal_toolkit.settings import MODULE_PATH, SETTINGS


class POVRayRenderer:
    """A class to interface with the POV-Ray command line tool (ray tracer)."""

    _TEMPLATES: ClassVar[dict[str, str]] = {
        path.stem: path.read_text()
        for path in (MODULE_PATH / "helpers" / "povray" / "templates").glob("*")
    }
    _ENV: ClassVar[Environment] = Environment()

    @staticmethod
    def write_scene_to_file(scene: Scene, filename: str | Path):
        """Render a Scene to a PNG file using POV-Ray."""
        current_dir = Path.cwd()

        with TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            POVRayRenderer.write_povray_input_scene_and_settings(
                scene, image_filename="crystal_toolkit_scene.png"
            )
            POVRayRenderer.call_povray()

            shutil.copy("crystal_toolkit_scene.png", current_dir / filename)

        os.chdir(current_dir)

    @staticmethod
    def call_povray(
        povray_args: tuple[str] = ("render.ini",),
        povray_path: str = SETTINGS.POVRAY_PATH,
    ):
        """
        Run POV-Ray. Prefer `render_scene` method unless advanced user.
        """

        povray_args = [povray_path, *povray_args]
        result = subprocess.run(povray_args, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(
                f"{povray_path} exit code: {result.returncode}."
                f"Please check your POV-Ray installation."
                f"\nStdout:\n\n{result.stdout}\n\nStderr:\n\n{result.stderr}"
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
            f.write(POVRayRenderer._get_camera_for_scene(scene))
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

        return ""

    @staticmethod
    def _format_color_to_povray(color: str) -> str:
        """Convert a matplotlib-compatible color string to a POV-Ray color string."""
        vect = "{:.4f},{:.4f},{:.4f}"
        color = to_hex(color)
        color = color.replace("#", "")
        color = tuple(int(color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
        return f"rgb<{vect.format(*color)}>"

    @staticmethod
    def _get_camera_for_scene(scene: Scene) -> str:
        """Creates a camera in POV-Ray format for a given scene with respect to its bounding box."""

        bounding_box = scene.bounding_box  # format is [min_corner, max_corner]
        center = (np.array(bounding_box[0]) + bounding_box[1]) / 2
        size = np.array(bounding_box[1]) - bounding_box[0]
        camera_pos = center + np.array([0, 0, 1.2 * size[2]])

        return f"""
camera {{
   orthographic
   location <{camera_pos[0]:.4f}, {camera_pos[1]:.4f}, {camera_pos[2]:.4f}>
   look_at <{center[0]:.4f}, {center[1]:.4f}, {center[2]:.4f}>
   sky <0, 0, 1>
}}
"""
