"""Module for handling AiiDA processes."""
import io
import uuid
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import traitlets as tl
from aiida.engine import submit
from aiida.orm import Dict, load_code
from ipywidgets import dlink
from IPython.display import Javascript, display, clear_output
from aiida_mlip.data.model import ModelData
from aiida.orm import StructureData
from aiida.orm import load_code, load_node
from aiida.orm import Str, Float, Bool, Int, BandsData, KpointsData
from aiida.plugins import CalculationFactory
from aiida_workgraph import WorkGraph

from aiidalab_alc.resources import ComputationalResourcesModel
from aiidalab_alc.results import ResultsModel
from aiidalab_alc.data import DataStepModel
from aiidalab_alc.workflow import WorkflowCalculationModel

from aiidalab_alc.ins_process import INSProcess
from aiidalab_alc.mlip_process import MLIPProcess

from ase import Atoms
import numpy as np
import sys

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
        if self.data_model.data_type in {"phonopy", "castep"}:
            self.process = INSProcess(self.data_model, self.workflow_model, self.resource_model, self.results_model)
            #at this point the submit button should be changed to calculating and disabled
            self._calculating()
            exit_status = self.process.submit_process()
            self.block_results = False
            self._finished(exit_status)

            if self.process.node is not None:
                 self.results_model.process_uuid = self.process.node.uuid
        
        elif self.data_model.data_type == "ase_mlip":
            self.process = MLIPProcess(self.data_model, self.workflow_model, self.resource_model, self.results_model)
            self._calculating()
            exit_status = self.process.submit_process()
            self.block_results = False
            self._finished(exit_status)

            if self.process.node is not None:
                self.results_model.process_uuid = self.process.node.uuid

        else:
            print("ERROR: Unsupported computational method for submission.")
            return

        print("I have finished submitting the process. You can now view the results in the Results tab.")
        """
        def _run_with_log(submit_fn):
            Capture stdout/stderr for the job in a temporary log file.
            log_path = Path.cwd() / f"submit-process-{uuid.uuid4().hex}.log"
            self.results_model.process_log = str(log_path)
            with log_path.open("w", encoding="utf-8") as log_handle:
                with redirect_stdout(log_handle), redirect_stderr(log_handle):
                    exit_status = submit_fn()

            if exit_status != 0 and log_path.exists():
                try:
                    from aiidalab_alc.utils import open_link_in_new_tab

                    open_link_in_new_tab(log_path)
                except Exception:
                    pass
            return exit_status

        sys.stdout = self.original
        if self.data_model.data_type in {"phonopy", "castep"}:
            self.process = INSProcess(self.data_model, self.workflow_model, self.resource_model, self.results_model)
            #at this point the submit button should be changed to calculating and disabled
            self._calculating()
            exit_status = _run_with_log(self.process.submit_process)
            self.block_results = False
            self._finished(exit_status)

            if self.process.node is not None:
                 self.results_model.process_uuid = self.process.node.uuid
        
        elif self.data_model.data_type == "ase_mlip":
            self.process = MLIPProcess(self.data_model, self.workflow_model, self.resource_model, self.results_model)
            self._calculating()
            exit_status = _run_with_log(self.process.submit_process)
            self.block_results = False
            self._finished(exit_status)

            if self.process.node is not None:
                self.results_model.process_uuid = self.process.node.uuid

        else:
            print("ERROR: Unsupported computational method for submission.")
            return
        """
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

