from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import yaml
from build.lib.aiidalab_alc.data import DataStepModel
from euphonic import ForceConstants

from aiida.engine import run_get_node
from aiida.orm import SinglefileData, load_code
from aiida_pythonjob import PythonJob
from aiida_pythonjob_ins.data import ForceConstantsData
from aiida_pythonjob_ins.pythonjobs import prepare_dispersion_inputs, prepare_dos_inputs

from aiidalab_alc.resources import ComputationalResourcesModel
from aiidalab_alc.results import ResultsModel
from aiidalab_alc.data import DataStepModel
from aiidalab_alc.workflow import WorkflowCalculationModel

class INSProcess:
    """Handle an INS-style phonon workflow driven by PythonJob calculations."""

    def __init__(self, data_model: DataStepModel, workflow_model: WorkflowCalculationModel, resource_model: ComputationalResourcesModel, results_model: ResultsModel):
        """Initialise the INS process wrapper."""
        self.data_model = data_model
        self.workflow_model = workflow_model
        self.resource_model = resource_model
        self.results_model = results_model
        self.node = None

    def validate_model(self) -> bool:
        """Validate the required data for the INS workflow."""
        print(
            f"Validating model for INS workflow with data type: "
            f"{self.data_model.has_structure}, {self.data_model.has_file}"
        )
        if not self.data_model.has_structure and not self.data_model.has_file:
            print("No structure provided for INS calculation.")
            return False

        if not self.data_model.force_constants_file:
            print("No force constants provided for INS calculation.")
            return False

        return True

    def submit_process(self):
        """Submit PythonJobs to compute the dispersion and DOS."""
        if not self.validate_model():
            return

        code = load_code(self.resource_model.code_name)
        structure = self.data_model.structure
        if structure is None:
            structure = self.data_model.structure_file

        force_constants = self._build_force_constants_data(
            self.data_model.force_constants_file
        )
        if force_constants is None:
            raise ValueError("Unable to build ForceConstantsData from the supplied input.")

        spacing = float(self.workflow_model.ins_spacing)
        energy_spacing = float(self.workflow_model.ins_energy_spacing)

        dispersion_inputs = prepare_dispersion_inputs(
            force_constants,
            q_spacing=spacing,
            code=code,
        )
        _, dispersion_process = run_get_node(PythonJob, **dispersion_inputs)

        modes = dispersion_process.outputs.result
        bands = modes.to_bands()

        dos_inputs = prepare_dos_inputs(
            force_constants,
            q_spacing=spacing,
            energy_spacing=energy_spacing,
            code=code,
        )
        _, dos_process = run_get_node(PythonJob, **dos_inputs)

        self.node = dispersion_process
        self.results_model.process_uuid = dispersion_process.uuid
        self.results_model.final_structure = structure
        self.results_model.phonon_band_structure = bands
        self.results_model.phonon_dos = dos_process.outputs.result.get_content()
        self.results_model.phonon_pdos = ""
        self.results_model.phonopy = {
            "dispersion_process_uuid": dispersion_process.uuid,
            "dos_process_uuid": dos_process.uuid,
        }

    def _build_force_constants_data(self, source):
        """Build a ForceConstantsData node from supported input types."""
        if isinstance(source, ForceConstantsData):
            return source

        if isinstance(source, ForceConstants):
            return ForceConstantsData(source)

        if hasattr(source, "get_force_constants"):
            return ForceConstantsData(source.get_force_constants())

        if not isinstance(source, SinglefileData):
            return None

        filename = source.filename or "force_constants_input"
        content = source.get_content()

        if filename.endswith((".castep_bin", ".check")):
            with TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir) / filename
                tmp_path.write_bytes(content)
                return ForceConstantsData.from_castep(tmp_path)

        if isinstance(content, bytes):
            content = content.decode("utf-8")

        content = content.strip()
        if not content:
            return None

        payload = yaml.safe_load(content)
        if isinstance(payload, dict) and "force_constants" in payload:
            payload = payload["force_constants"]
            tmp_filename = "phonopy.yaml"
        else:
            tmp_filename = filename

        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / tmp_filename
            tmp_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

            return ForceConstantsData.from_phonopy(
                path=tmpdir,
                summary_name=tmp_filename,
            )

        return None

