"""Defines the model and view components for the structure setup stage."""

import aiidalab_widgets_base as awb
import ipywidgets as ipw

from aiidalab_alc.models.data_model import DataStepModel
from aiidalab_alc.wizards.forceconstant_step_wizard import ForceConstantWizardStep
from aiidalab_alc.wizards.structure_step_wizard import StructureWizardStep

__all__ = ["DataStepModel", "DataWizardStep"]


class DataWizardStep(ipw.VBox, awb.WizardAppWidgetStep):
    """Wizard for viewing process progress and results."""

    def __init__(self, model: DataStepModel, **kwargs):
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
        self.model = model
        self.rendered = False
        self.model.observe(self._on_process_uuid_change, "process_uuid")

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

        #if not self.model.process_uuid:
        #    self.children = [ipw.HTML("Waiting for calculation results...")]
        #    return

        # 1. Structure Panel
        structure_vwr = StructureWizardStep(model=self.model)
        structure_vwr.render()

        # 2. Phonon Force constant Panel
        fc_vwr = ForceConstantWizardStep(model=self.model, structure_step=structure_vwr)
        structure_vwr.force_constants_step = fc_vwr
        fc_vwr.render()

        structure_panel = ipw.VBox(
            children=[
                structure_vwr,
            ]
        )
        force_constants_panel = ipw.VBox(
            children=[
                ipw.HTML("<h5>Force Constants</h5>"),
                fc_vwr,
            ]
        )

        accordion = ipw.Accordion(
            children=[structure_panel, force_constants_panel, ],
            selected_index=None,
        )
        accordion.set_title(0, "Structure")
        accordion.set_title(1, "Force Constants")

        self.children = [
            accordion,
        ]


