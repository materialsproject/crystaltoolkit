from __future__ import annotations

from crystal_toolkit.components.bandstructure import (
    BandstructureAndDosComponent,
    BandstructureAndDosPanelComponent,
)
from crystal_toolkit.components.diffraction import XRayDiffractionComponent
from crystal_toolkit.components.diffraction_tem import TEMDiffractionComponent
from crystal_toolkit.components.fermi_surface import FermiSurfaceComponent
from crystal_toolkit.components.localenv import LocalEnvironmentPanel
from crystal_toolkit.components.phase_diagram import (
    PhaseDiagramComponent,
    PhaseDiagramPanelComponent,
)
from crystal_toolkit.components.phonon import (
    PhononBandstructureAndDosComponent,
    PhononBandstructureAndDosPanelComponent,
)
from crystal_toolkit.components.pourbaix import PourbaixDiagramComponent
from crystal_toolkit.components.search import SearchComponent
from crystal_toolkit.components.structure import StructureMoleculeComponent

# from crystal_toolkit.components.submit_snl import SubmitSNLPanel
from crystal_toolkit.components.symmetry import SymmetryPanel
from crystal_toolkit.components.transformations.autooxistatedecoration import (
    AutoOxiStateDecorationTransformationComponent,
)
from crystal_toolkit.components.transformations.core import AllTransformationsComponent

# from crystal_toolkit.components.transformations.cubic import (
#     CubicSupercellTransformationComponent,
# )
from crystal_toolkit.components.transformations.grainboundary import (
    GrainBoundaryTransformationComponent,
)

# from crystal_toolkit.components.transformations.rattle import (
#     MonteCarloRattleTransformationComponent,
# )
from crystal_toolkit.components.transformations.slab import SlabTransformationComponent
from crystal_toolkit.components.transformations.substitution import (
    SubstitutionTransformationComponent,
)
from crystal_toolkit.components.transformations.supercell import (
    SupercellTransformationComponent,
)
from crystal_toolkit.components.upload import StructureMoleculeUploadComponent

# from crystal_toolkit.components.xas import XASComponent
# from crystal_toolkit.components.xas import XASPanelComponent
from crystal_toolkit.core.mpcomponent import MPComponent

register_app = MPComponent.register_app
register_cache = MPComponent.register_cache
register_crystal_toolkit = MPComponent.register_crystal_toolkit
crystal_toolkit_layout = MPComponent.crystal_toolkit_layout
