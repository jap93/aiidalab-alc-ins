from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Dict

import yaml
from euphonic import ForceConstants

from aiida.engine import run_get_node
from aiida.orm import SinglefileData, load_code, load_computer, Computer, InstalledCode
from aiida_pythonjob import PythonJob
from aiida_pythonjob_ins.data import ForceConstantsData
from aiida_pythonjob_ins.pythonjobs import prepare_dispersion_inputs, prepare_dos_inputs
from aiida_pythonjob_ins.workflows import DispersionWorkChain, DosWorkChain
from aiida import orm
from aiida.engine import run_get_node
from aiida_pythonjob import PythonJob

from aiidalab_alc.resources import ComputationalResourcesModel
from aiidalab_alc.results import ResultsModel
from aiidalab_alc.data import DataStepModel
from aiidalab_alc.workflow import WorkflowCalculationModel

import tempfile
import sys
from aiida.common.exceptions import NotExistent
from aiida.manage.configuration import get_config
from aiida.storage.sqlite_temp import SqliteTempBackend
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
        print(f"Validating force constants file: {self.data_model.force_constants_file}")
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

        code = get_python_code()
        structure = self.data_model.structure
        if structure is None:
            structure = self.data_model.structure_file

        force_constants = self.data_model.force_constants_data
        if force_constants is None:
            raise ValueError("Unable to build ForceConstantsData from the supplied input.")

        spacing = float(self.workflow_model.ins_spacing)
        energy_spacing = float(self.workflow_model.ins_energy_spacing)

        #dispersion_inputs = prepare_dispersion_inputs(
        #    force_constants,
        #    q_spacing=spacing,
        #    code=code,
        #)

        bands_results, bands_node = run_get_node(
            DispersionWorkChain,
            force_constants=force_constants,
            q_spacing=orm.Float(spacing),
            code=code,)

        if bands_node.exit_status != 0:
            print(f"Dispersion process failed with exit status: {bands_node.exit_status}")
            return

        print("results dictionary: ")
        for key, value in bands_results.items():
            print(f"  {key}: {value}")

        
        print("bands:", bands_results["band_structure"])

        print(f"Dispersion process finished with UUID: {bands_node.uuid}")
        bands_results["band_structure"].show_mpl()

        dos_results, dos_node = run_get_node(
            DosWorkChain,
            force_constants=force_constants,
            q_spacing=orm.Float(spacing),
            energy_spacing=orm.Float(energy_spacing),
            code=code,
        )

        if dos_node.exit_status != 0:
            print(f"DOS process failed with exit status: {dos_node.exit_status}")
            return

        import matplotlib.pyplot as plt

        dos = dos_results["dos"]
        _, energy, energy_unit = dos.get_x()
        ((_, density, dos_unit),) = dos.get_y()

        fig, ax = plt.subplots()
        ax.plot(energy, density)
        ax.set_xlabel(f"Energy ({energy_unit})")
        ax.set_ylabel(f"Density of states ({dos_unit})")
        ax.set_title("NaCl phonon DOS (from Phonopy)")
        fig.tight_layout()

        
        self.results_model.process_uuid = bands_node.uuid
        self.results_model.final_structure = structure
        self.results_model.phonon_band_structure = bands_results["band_structure"]
        self.results_model.phonon_dos = dos_results["dos"]
        self.results_model.phonon_pdos = ""
        

    def _dict_to_force_constants_data(self, data : Dict):
        """Build a ForceConstantsData node from supported input types."""
        if isinstance(data, ForceConstantsData):
            return data

        if isinstance(data, ForceConstants):
            return ForceConstantsData(data)

        if hasattr(data, "get_force_constants"):
            return ForceConstantsData(data.get_force_constants())

        if isinstance(data, (bytes, str)):
            content = data.decode("utf-8") if isinstance(data, bytes) else data
            content = content.strip()
            if not content:
                return None

            payload = yaml.safe_load(content)
            if isinstance(payload, dict) and "force_constants" in payload:
                payload = payload["force_constants"]
                tmp_filename = "phonopy.yaml"
            else:
                tmp_filename = "force_constants_input.yaml"

            with TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir) / tmp_filename
                tmp_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
                return ForceConstantsData.from_phonopy(
                    path=tmpdir,
                    summary_name=tmp_filename,
                )

            return None

        if not isinstance(data, SinglefileData):
            return None

        filename = data.filename or "force_constants_input"
        content = data.get_content()

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

