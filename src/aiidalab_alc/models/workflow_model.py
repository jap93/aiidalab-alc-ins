"""Model for the workflow configuration step."""

import traitlets as tl


class WorkflowCalculationModel(tl.HasTraits):
    """The model for setting up a MLIP workflow."""

    # parameters for MLIP
    calc_style = tl.Unicode("Geometry optimisation", allow_none=False)
    optimisation = tl.Unicode("cell lengths", allow_none=False)
    maximum_force = tl.Float(0.001, allow_none=False)
    pressure = tl.Float(0.0, allow_none=False)
    force_field = tl.Unicode("mace_mp_small.model", allow_none=True)
    architecture = tl.Unicode("mace", allow_none=False)
    submitted = tl.Bool(False).tag(sync=True)
    use_dftd3 = tl.Bool(False).tag(sync=True)

    # phonon parameters
    auto_bands = tl.Bool(True).tag(sync=True)
    supercell_size_x = tl.Int(2).tag(sync=True)
    supercell_size_y = tl.Int(2).tag(sync=True)
    supercell_size_z = tl.Int(2).tag(sync=True)
    number_points = tl.Int(51).tag(sync=True)

    # INS parameters
    use_ins_spacing = tl.Unicode("Use spacing").tag(sync=True)

    ins_supercell_size_x = tl.Int(2).tag(sync=True)
    ins_supercell_size_y = tl.Int(2).tag(sync=True)
    ins_supercell_size_z = tl.Int(2).tag(sync=True)
    ins_spacing = tl.Float(0.05).tag(sync=True)
    ins_temperature = tl.Float(300.0).tag(sync=True)
    ins_dos_qspacing = tl.Float(0.1).tag(sync=True)
    ins_dos_energy_spacing = tl.Float(0.1).tag(sync=True)
    ins_resins_qspacing = tl.Float(0.5).tag(sync=True)
    ins_resins_energy_spacing = tl.Float(0.5).tag(sync=True)

    calculate_band_structure = tl.Bool(True).tag(sync=True)
    calculate_ins = tl.Bool(False).tag(sync=True)
    calculate_resins = tl.Bool(False).tag(sync=True)

    default_guide = ""
