from __future__ import annotations

import os
from typing import TYPE_CHECKING

from dash import dcc
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from tqdm import tqdm

if TYPE_CHECKING:
    import pandas as pd


def load_and_store_matbench_dataset(dataset_name: str) -> pd.DataFrame:
    """Load, process and save Matbench datasets to disk to avoid having to re-process on subsequent
    app runs.
    """
    data_path = os.path.join(os.path.dirname(__file__), f"{dataset_name}.json.gz")

    if os.path.isfile(data_path):
        import pandas as pd

        df = pd.read_json(data_path)
    else:
        try:
            from matminer.datasets import load_dataset

            df = load_dataset(dataset_name)

            if "structure" in df:
                df[["spg_symbol", "spg_num"]] = [
                    struct.get_space_group_info()
                    for struct in tqdm(df.structure, desc="Getting space groups")
                ]

                df["crystal_sys"] = [
                    SpacegroupAnalyzer(x).get_crystal_system() for x in df.structure
                ]

                df["volume"] = [x.volume for x in df.structure]
                df["formula"] = [x.formula for x in df.structure]

            df.to_json(data_path, default_handler=lambda x: x.as_dict())
        except ImportError:
            print(
                "matminer is not installed but needed to download a dataset. Run "
                "`pip install matminer`"
            )

    return df


matbench_dielectric_desc = dcc.Markdown(
    """
    ## About the [`matbench_dielectric` dataset][mp_mb_diel]

    Intended use: Machine learning task to predict refractive index from structure.
        All data from Materials Project. Removed entries having a formation energy (or energy
        above the convex hull) more than 150meV and those having refractive indices less than
        1 and those containing noble gases. Retrieved April 2, 2019.

    - Input: Pymatgen Structure of the material
    - Target variable: refractive index n (unitless)
    - Entries: 636

    See [MatBench website](https://matbench.materialsproject.org) for details.

    [mp_mb_diel]: https://ml.materialsproject.org/projects/matbench_dielectric
    """,
    style=dict(margin="3em auto", maxWidth="50em"),
)
