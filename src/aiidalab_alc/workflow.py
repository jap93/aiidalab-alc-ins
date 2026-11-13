"""Module defining the view for the workflow configuration step."""

import aiidalab_widgets_base as awb
import ipywidgets as ipw

from aiidalab_alc.data import DataStepModel
from aiidalab_alc.models.workflow_model import WorkflowCalculationModel
from aiidalab_alc.wizards.ins_workflow import INSOptionsWidget
from aiidalab_alc.wizards.mlip_workflow import MethodWizardStep

__all__ = ["WorkflowCalculationModel", "WorkflowCalculationStep"]


class WorkflowCalculationStep(ipw.VBox, awb.WizardAppWidgetStep):
    """Wizard for viewing process progress and results."""

    def __init__(
        self, data_model: DataStepModel, work_model: WorkflowCalculationModel, **kwargs
    ):
        """
        DataWizardStep constructor.

        Parameters
        ----------
        model : DataStepModel
            The model controlling required data.
        **kwargs :
            Keyword arguments passed to the parent class's constructor.
        """
        super().__init__(**kwargs)
        self.data_model = data_model
        self.work_model = work_model
        self.rendered = False
        # self.model.observe(self._on_process_uuid_change, "process_uuid")

    def _on_process_uuid_change(self, _):
        """Update view when process UUID changes."""
        if self.rendered:
            self._update_view()

    def render(self) -> None:
        """Render the wizard's content."""
        if self.rendered:
            return
        self._update_view()
        self.rendered = True

    def _update_view(self):
        # if not self.model.process_uuid:
        #    self.children = [ipw.HTML("Waiting for calculation results...")]
        #    return

        vwr_panel = None
        if self.data_model.data_type == "ase_mlip":
            mlip_vwr = MethodWizardStep(model=self.work_model)
            mlip_vwr.render()
            vwr_panel = ipw.VBox(
                children=[
                    mlip_vwr,
                ]
            )

        elif (
            self.data_model.data_type == "phonopy"
            or self.data_model.data_type == "castep"
        ):
            ins_vwr = INSOptionsWidget(model=self.work_model)
            ins_vwr.render()
            vwr_panel = ipw.VBox(
                children=[
                    ins_vwr,
                ]
            )
        else:
            vwr_panel = ipw.VBox(
                children=[
                    ipw.HTML("<h4>Select structure or force constants</h4>"),
                ]
            )

        self.children = [
            vwr_panel,
        ]
