"""Model for the results step."""

import traitlets as tl
from aiida.orm import BandsData, StructureData, XyData

from aiidalab_alc.models.process_model import ProcessModel


class ResultsModel(ProcessModel):
    """MVC results step model."""

    blocked = tl.Bool(False)
    final_structure = tl.Instance(StructureData, allow_none=True)
    phonon_band_structure = tl.Instance(BandsData, allow_none=True)
    phonon_dos = tl.Instance(XyData, allow_none=True)
    phonon_pdos = tl.Unicode("", allow_none=True)
    phonopy = tl.Dict({}, allow_none=True)
    tosca_spectrum = tl.Instance(XyData, allow_none=True)
