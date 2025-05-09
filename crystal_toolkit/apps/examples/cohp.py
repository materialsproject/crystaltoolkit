import os
import warnings

import dash
import numpy as np
from pymatgen.core import Structure
from pymatgen.electronic_structure.cohp import CompleteCohp
from pymatgen.io.lobster.inputs import Lobsterin
from pymatgen.io.lobster.outputs import (
    Bandoverlaps,
    Charge,
    Doscar,
    Icohplist,
    Lobsterout,
    MadelungEnergies,
)
from pymatgen.io.vasp.outputs import Vasprun

import crystal_toolkit.components as ctc
from crystal_toolkit.helpers.layouts import H3, Container
from crystal_toolkit.settings import SETTINGS


class CustomVasprun(Vasprun):
    """Override final_energy property without unitized decorator"""

    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)

    @property
    def final_energy(self) -> float:
        """Final energy from the VASP run."""

        try:
            final_istep = self.ionic_steps[-1]
            total_energy = final_istep["e_0_energy"]

            # Fix a bug in vasprun.xml.
            # See https://www.vasp.at/forum/viewtopic.php?f=3&t=16942
            final_estep = final_istep["electronic_steps"][-1]
            electronic_energy_diff = (
                final_estep["e_0_energy"] - final_estep["e_fr_energy"]
            )
            total_energy_bugfix = np.round(
                electronic_energy_diff + final_istep["e_fr_energy"], 8
            )
            if np.abs(total_energy - total_energy_bugfix) > 1e-7:
                return total_energy_bugfix

            return total_energy

        except (IndexError, KeyError):
            warnings.warn(
                "Calculation does not have a total energy. Possibly a GW or similar kind of run. Infinity is returned.",
                stacklevel=2,
            )
            return float("inf")


calc_dir = "path/to/your/lobster/output"  # Replace with your actual path

icohplist_obj = Icohplist(
    filename=f"{calc_dir}/ICOHPLIST.lobster.gz", are_cobis=False, are_coops=False
)

completecohp_obj = CompleteCohp.from_file(
    filename=f"{calc_dir}/COHPCAR.lobster.gz",
    structure_file=f"{calc_dir}/CONTCAR.gz",
    fmt="LOBSTER",
    are_cobis=False,
    are_coops=False,
)

charge_obj = Charge(filename=f"{calc_dir}/CHARGE.lobster.gz")
madelung_obj = MadelungEnergies(filename=f"{calc_dir}/MadelungEnergies.lobster.gz")
lob_dos = Doscar(
    doscar=f"{calc_dir}/DOSCAR.LSO.lobster.gz", structure_file=f"{calc_dir}/CONTCAR.gz"
)

vasprun_obj = CustomVasprun(filename=f"{calc_dir}/vasprun.xml.gz")
structure_obj = Structure.from_file(f"{calc_dir}/CONTCAR.gz")
lobsterin_obj = Lobsterin.from_file(f"{calc_dir}/lobsterin.gz")
lobsterout_obj = Lobsterout(filename=f"{calc_dir}/lobsterout.gz")
# Include band overlaps file if it exists available
bandoverlaps_obj = (
    Bandoverlaps(filename=f"{calc_dir}/bandOverlaps.lobster.gz")
    if os.path.exists(f"{calc_dir}/bandOverlaps.lobster.gz")
    else None
)

cohp_component = ctc.CohpAndDosComponent(
    density_of_states=lob_dos.completedos,
    charge_obj=charge_obj,
    icohplist_obj=icohplist_obj,
    completecohp_obj=completecohp_obj,
    madelung_obj=madelung_obj,
    vasprun_obj=vasprun_obj,
    structure_obj=structure_obj,
    lobsterin_obj=lobsterin_obj,
    lobsterout_obj=lobsterout_obj,
    bandoverlaps_obj=bandoverlaps_obj,
    mpid="mp-xxx",
    disable_callbacks=False,
)

# example layout to demonstrate capabilities of component
layout = Container([H3("COHP and Density of States Example"), cohp_component.layout()])

app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH, prevent_initial_callbacks=True)  #

ctc.register_crystal_toolkit(app, layout=layout)

if __name__ == "__main__":
    app.run(debug=True, port=8051)
