"""Defines the model for the data input stage."""

import traitlets as tl
from aiida.orm import SinglefileData, StructureData
from aiida_alc_ins.data import ForceConstantsData


class DataStepModel(tl.HasTraits):
    """
    Model for structure selection and manipulation.

    A model to define and store required information from the structure
    step in the app's configuration wizard.
    """

    data_type = tl.Unicode("", allow_none=True)

    structure = tl.Instance(StructureData, allow_none=True)
    structure_file = tl.Instance(SinglefileData, allow_none=True)

    force_constants_file = tl.Instance(SinglefileData, allow_none=True)
    force_constants_path = tl.Unicode("", allow_none=False)
    force_constants_data = tl.Instance(ForceConstantsData, allow_none=True)
    submitted = tl.Bool(False).tag(sync=True)

    default_guide = ""

    @property
    def has_structure(self) -> bool:
        """True if a StructureData object has been attached to the model."""
        return self.structure is not None

    @property
    def has_file(self) -> bool:
        """True if a raw structure file object has been attached to the model."""
        return self.structure_file is not None

    @property
    def is_periodic(self) -> bool:
        """True if the attached StructureData object is a periodic structure."""
        if self.has_structure:
            return any(self.structure.pbc)
        return False

    @property
    def has_force_constants(self) -> bool:
        """True if force constants have been attached to the model."""
        return (
            self.force_constants_file is not None
            or self.force_constants_data is not None
        )

