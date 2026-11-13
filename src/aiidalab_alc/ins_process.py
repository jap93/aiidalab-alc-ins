"""AiiDA process driver for INS calculations from force constants."""

from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from aiida import orm
from aiida.common.exceptions import NotExistent
from aiida.engine import run_get_node
from aiida.orm import (
    Computer,
    Float,
    InstalledCode,
    List,
    SinglefileData,
    load_code,
    load_computer,
)
from aiida.plugins import WorkflowFactory
from aiida_alc_ins.data import ForceConstantsData
from euphonic import ForceConstants

from aiidalab_alc.data import DataStepModel
from aiidalab_alc.resources import ComputationalResourcesModel
from aiidalab_alc.results import ResultsModel
from aiidalab_alc.workflow import WorkflowCalculationModel


def get_python_code():
    """Load an in-memory AiiDA profile and return a localhost Python ``Code``.

    Uses an in-memory SQLite profile (no PostgreSQL, no persistent config) and a
    ``core.direct`` localhost computer running this interpreter -- enough to
    execute PythonJobs during the docs build.
    """
    # `runner.poll.interval` defaults to 60 s, and a WorkChain awaiting a child
    # process (`self.submit` + `ToContext`) pays it once per child -- turning a
    # seconds-long example into a minutes-long one. AiiDA waives it for *test*
    # profiles (`Manager.create_runner`: `poll_interval = 0.0 if
    # profile.is_test_profile else ...`), which is why the pytest suite never sees
    # this, but a profile built here is not flagged as one. Setting the option on
    # the profile is the supported route: profile options take priority over the
    # config and the built-in default (`Manager.get_option`).

    try:
        computer = load_computer("localhost")
    except NotExistent:
        computer = Computer(
            label="localhost",
            hostname="localhost",
            transport_type="core.local",
            scheduler_type="core.direct",
            workdir=tempfile.mkdtemp(),
        ).store()
        computer.configure(safe_interval=0.0)

    try:
        return load_code("python3@localhost")
    except NotExistent:
        return InstalledCode(
            computer=computer,
            label="python3",
            filepath_executable=sys.executable,
            default_calc_job_plugin="pythonjob.pythonjob",
        ).store()


class INSProcess:
    """Handle an INS-style phonon workflow driven by PythonJob calculations."""

    def __init__(
        self,
        data_model: DataStepModel,
        workflow_model: WorkflowCalculationModel,
        resource_model: ComputationalResourcesModel,
        results_model: ResultsModel,
    ):
        """Initialise the INS process wrapper."""
        self.data_model = data_model
        self.workflow_model = workflow_model
        self.resource_model = resource_model
        self.results_model = results_model
        self.node = None

    def validate_model(self) -> bool:
        """Validate the required data for the INS workflow."""
        if not self.data_model.has_structure and not self.data_model.has_file:
            print("No structure provided for INS calculation.")
            return False

        if not self.data_model.has_force_constants:
            print("No force constants provided for INS calculation.")
            return False

        return True

    def submit_process(self):
        """Submit PythonJobs to compute the dispersion and DOS."""
        exit_status = 0
        log_path = self.results_model.process_log
        logging.basicConfig(filename=log_path, level=logging.INFO, force=True)
        logger = logging.getLogger(__name__)
        logger.info("Started MLIP:Process submission")

        if not self.validate_model():
            logger.error("INSProcess validation failed. Aborting submission.")
            return 400

        code = get_python_code()

        structure = self.data_model.structure
        if structure is None:
            structure = self.data_model.structure_file

        force_constants_data = self.data_model.force_constants_data
        if force_constants_data is None:
            raise ValueError(
                "Unable to build ForceConstantsData from the supplied input."
            )
        # force_constants = self._force_constants_data_to_dict(force_constants_data)

        spacing = float(self.workflow_model.ins_spacing)

        # create the "workflows" using the WorkflowFactory to avoid import issues
        logger.info("Creating work chains using WorkflowFactory")
        dispersion_workchain = WorkflowFactory("alc_ins.dispersion")
        dos_workchain = WorkflowFactory("alc_ins.dos")
        tosca_workchain = WorkflowFactory("alc_ins.tosca_from_force_constants")
        logger.info("Submitting DispersionWorkChain")

        bands_results, bands_node = run_get_node(
            dispersion_workchain,
            force_constants={"node": force_constants_data},
            q_spacing=orm.Float(spacing),
            code=code,
        )
        self.node = bands_node

        if bands_node.exit_status != 0:
            print(
                f"Dispersion process failed with exit status: {bands_node.exit_status}"
            )
            logger.error(
                f"Dispersion process failed with exit status: {bands_node.exit_status}"
            )
            return bands_node.exit_status

        logger.info(
            "DispersionWorkChain completed successfully. Submitting DosWorkChain"
        )
        spacing = float(self.workflow_model.ins_dos_qspacing)
        energy_spacing = float(self.workflow_model.ins_dos_energy_spacing)
        dos_results, dos_node = run_get_node(
            dos_workchain,
            force_constants={"node": force_constants_data},
            q_spacing=orm.Float(spacing),
            energy_spacing=orm.Float(energy_spacing),
            code=code,
        )

        if dos_node.exit_status != 0:
            print(f"DOS process failed with exit status: {dos_node.exit_status}")
            return dos_node.exit_status

        # INS calculation starts if requested using tosca work chain
        if self.workflow_model.calculate_resins:
            spacing = float(self.workflow_model.ins_resins_qspacing)
            energy_spacing = float(self.workflow_model.ins_resins_energy_spacing)
            ins_results, ins_node = run_get_node(
                tosca_workchain,
                force_constants={"node": force_constants_data},
                q_spacing=Float(spacing),
                spectrum={
                    "temperature": Float(self.workflow_model.ins_temperature),
                    "energy_spacing": Float(energy_spacing),
                    "detector_angles": List(list=[135.0]),
                },
                code=code,
            )

            if ins_node.exit_status != 0:
                print(f"INS process failed with exit status: {ins_node.exit_status}")
                return ins_node.exit_status

            logger.info(
                "INS process completed successfully. Creating results model entries."
            )
        # keep the necessary data in the results model for later use
        self.results_model.process_uuid = bands_node.uuid
        self.results_model.final_structure = structure
        self.results_model.phonon_band_structure = bands_results["band_structure"]
        self.results_model.phonon_dos = dos_results["dos"]
        self.results_model.phonon_pdos = ""
        if self.workflow_model.calculate_resins:
            self.results_model.tosca_spectrum = ins_results["spectrum"]
        else:
            self.results_model.tosca_spectrum = None

        logger.info("INSProcess submission completed successfully.")
        return exit_status

    def _dict_to_force_constants_data(self, data: dict):
        """Build a ForceConstantsData node from supported input types."""
        if isinstance(data, ForceConstantsData):
            return data

        if isinstance(data, ForceConstants):
            return ForceConstantsData(data)

        if hasattr(data, "get_force_constants"):
            return ForceConstantsData(data.get_force_constants())

        if isinstance(data, bytes | str):
            return self._force_constants_from_text(data, "force_constants_input.yaml")

        if isinstance(data, SinglefileData):
            return self._force_constants_from_text(
                data.get_content(), data.filename or "force_constants_input"
            )

        return None

    @staticmethod
    def _force_constants_from_text(content: bytes | str, default_filename: str):
        """Build a ForceConstantsData node from phonopy YAML text."""
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
            tmp_filename = default_filename

        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / tmp_filename
            tmp_path.write_text(
                yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
            )
            return ForceConstantsData.from_phonopy(
                path=tmpdir,
                summary_name=tmp_filename,
            )

    def _force_constants_data_to_dict(
        self, force_constants_data: ForceConstantsData
    ) -> dict:
        """Convert a ForceConstantsData node to a dictionary."""
        if not isinstance(force_constants_data, ForceConstantsData):
            raise ValueError("Input must be a ForceConstantsData node.")

        return force_constants_data.get_force_constants().to_dict()
