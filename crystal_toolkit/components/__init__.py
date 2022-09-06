# use redundant as-import following PEP 484, see
# https://github.com/microsoft/pylance-release/issues/856#issuecomment-763793949
# and https://peps.python.org/pep-0484/#stub-files

from crystal_toolkit.components.bandstructure import (
    BandstructureAndDosComponent as BandstructureAndDosComponent,
)
from crystal_toolkit.components.bandstructure import (
    BandstructureAndDosPanelComponent as BandstructureAndDosPanelComponent,
)
from crystal_toolkit.components.diffraction import (
    TEMDiffractionComponent as TEMDiffractionComponent,
)
from crystal_toolkit.components.diffraction import (
    XRayDiffractionComponent as XRayDiffractionComponent,
)
from crystal_toolkit.components.phase_diagram import (
    PhaseDiagramComponent as PhaseDiagramComponent,
)
from crystal_toolkit.components.phase_diagram import (
    PhaseDiagramPanelComponent as PhaseDiagramPanelComponent,
)
from crystal_toolkit.components.pourbaix import (
    PourbaixDiagramComponent as PourbaixDiagramComponent,
)
from crystal_toolkit.components.robocrys import RobocrysComponent as RobocrysComponent
from crystal_toolkit.components.search import SearchComponent as SearchComponent
from crystal_toolkit.components.structure import (
    StructureMoleculeComponent as StructureMoleculeComponent,
)

# from crystal_toolkit.components.submit_snl import SubmitSNLPanel as SubmitSNLPanel
from crystal_toolkit.components.symmetry import SymmetryPanel as SymmetryPanel
from crystal_toolkit.components.transformations.autooxistatedecoration import (
    AutoOxiStateDecorationTransformationComponent as AutoOxiStateDecorationTransformationComponent,
)
from crystal_toolkit.components.transformations.core import (
    AllTransformationsComponent as AllTransformationsComponent,
)

# from crystal_toolkit.components.transformations.cubic import (
#     CubicSupercellTransformationComponent as CubicSupercellTransformationComponent,
# )
from crystal_toolkit.components.transformations.grainboundary import (
    GrainBoundaryTransformationComponent as GrainBoundaryTransformationComponent,
)

# from crystal_toolkit.components.transformations.rattle import (
#     MonteCarloRattleTransformationComponent as MonteCarloRattleTransformationComponent,
# )
from crystal_toolkit.components.transformations.slab import (
    SlabTransformationComponent as SlabTransformationComponent,
)
from crystal_toolkit.components.transformations.substitution import (
    SubstitutionTransformationComponent as SubstitutionTransformationComponent,
)
from crystal_toolkit.components.transformations.supercell import (
    SupercellTransformationComponent as SupercellTransformationComponent,
)
from crystal_toolkit.components.upload import (
    StructureMoleculeUploadComponent as StructureMoleculeUploadComponent,
)

# from crystal_toolkit.components.xas import XASComponent as XASComponent
# from crystal_toolkit.components.xas import XASPanelComponent as XASPanelComponent
from crystal_toolkit.core.mpcomponent import MPComponent as MPComponent

register_app = MPComponent.register_app
register_cache = MPComponent.register_cache
register_crystal_toolkit = MPComponent.register_crystal_toolkit
crystal_toolkit_layout = MPComponent.crystal_toolkit_layout
