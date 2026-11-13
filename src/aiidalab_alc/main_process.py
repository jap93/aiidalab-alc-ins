"""Module for handling AiiDA processes."""

import sys
import uuid
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import traitlets as tl
from ipywidgets import dlink

from aiidalab_alc.data import DataStepModel
from aiidalab_alc.ins_process import INSProcess
from aiidalab_alc.mlip_process import MLIPProcess
from aiidalab_alc.resources import ComputationalResourcesModel
from aiidalab_alc.results import ResultsModel
from aiidalab_alc.workflow import WorkflowCalculationModel


class MainAppModel(tl.HasTraits):
    """The main AiiDAlab application MVC model."""

    block_results = tl.Bool(True, allow_none=False)

    def __init__(self):
        """MainAppModel constructor."""
        super().__init__()
        self.data_model = DataStepModel()
        self.workflow_model = WorkflowCalculationModel()
        self.resource_model = ComputationalResourcesModel()
        self.results_model = ResultsModel()

        self.resource_model.observe(self._submit_model, "submitted")
        dlink((self, "block_results"), (self.results_model, "blocked"))

        self.process = None
        self.original = sys.stdout

        return

    def _submit_model(self, _) -> None:
        """Handle the submission of the AiiDA process."""
        log_path = Path.cwd() / f"submit-process-{uuid.uuid4().hex}.log"
        self.results_model.process_log = str(log_path)
        with log_path.open("w", encoding="utf-8") as log_handle:
            with redirect_stdout(log_handle), redirect_stderr(log_handle):
                if self.data_model.data_type in {"phonopy", "castep"}:
                    self.process = INSProcess(
                        self.data_model,
                        self.workflow_model,
                        self.resource_model,
                        self.results_model,
                    )
                    # at this point the submit button should be changed to
                    # calculating and disabled
                    self._calculating()
                    exit_status = self.process.submit_process()
                    self.block_results = False
                    self._finished(exit_status)

                    if self.process.node is not None:
                        self.results_model.process_uuid = self.process.node.uuid

                elif self.data_model.data_type == "ase_mlip":
                    self.process = MLIPProcess(
                        self.data_model,
                        self.workflow_model,
                        self.resource_model,
                        self.results_model,
                    )
                    self._calculating()
                    exit_status = self.process.submit_process()
                    self.block_results = False
                    self._finished(exit_status)

                    if self.process.node is not None:
                        self.results_model.process_uuid = self.process.node.uuid

                else:
                    print("ERROR: Unsupported computational method for submission.")
                    return

        sys.stdout = self.original
        print(
            "I have finished submitting the process. "
            "You can now view the results in the Results tab."
        )

    def _calculating(self) -> None:
        """Update the UI to indicate that the calculation is in progress."""
        self.resource_model.submit_btn.description = "Calculating..."
        self.resource_model.submit_btn.disabled = True
        self.resource_model.submit_btn.button_style = "warning"
        return

    def _finished(self, exit_status) -> None:
        """Update the UI to indicate that the calculation is in progress."""
        if exit_status != 0:
            self.resource_model.submit_btn.description = "Failed"
            self.resource_model.submit_btn.disabled = True
            self.resource_model.submit_btn.button_style = "danger"
        else:
            self.resource_model.submit_btn.description = "Finished"
            self.resource_model.submit_btn.disabled = True
            self.resource_model.submit_btn.button_style = "success"
        return

    def reset(self) -> None:
        """Reset the state of the model."""
        self.submitted = False
