"""Defines the model and view for the resource setup stage."""

import aiidalab_widgets_base as awb
import ipywidgets as ipw
import traitlets as tl
from aiida.orm import Code, QueryBuilder

from aiidalab_alc.utils import test_resource_import


class ComputationalResourcesModel(tl.HasTraits):
    """Model for the resource setup stage."""

    code_name = tl.Unicode("").tag(sync=True)
    #code_label = tl.Unicode("").tag(sync=True)
    device_name = tl.Unicode("").tag(sync=True)
    ncpus = tl.Int(1).tag(sync=True)
    process_label = tl.Unicode("").tag(sync=True)
    process_description = tl.Unicode("").tag(sync=True)
    submitted = tl.Bool(False).tag(sync=True)

    default_guide = """
        <p>
            Configure the computational resources required to run the MLIP
            calculation. Additionally, you can provide a label and description for
            the AiiDA process that will be created.
        </p>
    """

    def validate(self) -> bool:
        """
        Validate the model's inputs.

        Returns
        -------
        bool
            True if all inputs are valid, False otherwise.
        """
        if not self.code_name:
            return False
        if not self.process_label:
            return False
        return True


class ComputationalResourcesWizardStep(ipw.VBox, awb.WizardAppWidgetStep):
    """Main view for the resource setup stage."""

    def __init__(self, model: ComputationalResourcesModel, **kwargs):
        """
        ComputationalResourcesWizardStep constructor.

        Parameters
        ----------
        **kwargs :
            Keyword arguments passed to the parent class's constructor.
        """
        super().__init__(children=[], **kwargs)
        self.model = model
        self.rendered = False

        self.header = ipw.HTML(
            """
            <h3> Computational Resources Setup </h3>
            """,
            layout={"margin": "auto"},
        )
        self.mlips_installed = test_resource_import()
        self.mlips_warning = ipw.HTML("", layout={"margin": "auto"})

        self.guide = ipw.HTML(
            self.model.default_guide,
        )

        self.submit_btn = ipw.Button(
            description="Submit",
            button_style="success",
            tooltip="Submit the calculation",
            icon="check",
            layout={"width": "80%", "margin": "auto"},
        )
        self.submit_btn.on_click(self._submit)

        self.error_output = ipw.HTML(layout={"margin": "10px auto", "width": "80%"})

        self.children = [
            # self.header,
            self.guide,
            self.mlips_warning if not self.mlips_installed else ipw.HTML(""),
            ResourceSetupBox(model=self.model),
            self.error_output,
            self.submit_btn,
        ]
        return

    def render(self):
        """Render the wizard's contents if not already rendered."""
        if self.rendered:
            return
        self._refresh_widget()
        self.rendered = True
        return

    def _submit(self, _=None) -> None:
        """Handle the submission of the AiiDA process."""
        self.error_output.value = ""

        if self.model.validate():
            self.model.submitted = True
            self.submit_btn.disabled = True
            self.submit_btn.description = "Submitted"
        else:
            # Capture specific validation errors for the UI
            errors = []
            if not self.model.code_name:
                errors.append("No code selected.")
            if not self.model.process_label:
                errors.append("Process label cannot be empty.")

            error_text = " ".join(errors) or "Input validation failed."
            self.error_output.value = f"""
                <div style="background-color: #f8d7da; color: #721c24; padding: 10px; border: 1px solid #f5c6cb; border-radius: 5px;">
                    <strong>Validation Error:</strong> {error_text}
                </div>"""
        return

    def _refresh_widget(self) -> None:
        """Refresh the widget's contents."""
        self.mlips_installed = test_resource_import()
        if not self.mlips_installed:
            self.submit_btn.disabled = True
            self.mlips_warning.value = (
                "<p style='color:red;'>"
                "The aiida-mlip plugin is not installed. Please install it "
                "to proceed."
                "</p>"
            )
        else:
            self.mlips_warning.value = ""
            self.submit_btn.disabled = False


class ResourceSetupBox(ipw.VBox):
    """A box widget for defining computational resources."""

    def __init__(self, model: ComputationalResourcesModel, **kwargs):
        """
        ResourceSetupBox constructor.

        Parameters
        ----------
        **kwargs :
            Keyword arguments passed to the parent class's constructor.
        """
        super().__init__(layout={"margin": "auto", "width": "80%"}, **kwargs)
        self.model = model

        self.code = ipw.Combobox(
            description="Code:",
            value = "",
            layout={"width": "60%"},
        )
        tl.link((self.code, "value"), (self.model, "code_name"))
        self.refresh_codes_button = ipw.Button(
            description="Refresh",
            button_style="info",
            tooltip="Refresh the list of available codes",
            icon="refresh",
            layout={"width": "20%"},
        )
        self.refresh_codes_button.on_click(self.update_codes)
        self.code_box = ipw.HBox(
            layout={"width": "100%"}, children=[self.code, self.refresh_codes_button]
        )
        self.update_codes()

        tl.link((self.code, "value"), (self.model, "code_name"))

        #style = {'description_width': 'initial'}
        self.device_dropdown = ipw.Dropdown(
            options=["cpu", "cuda"],
            value = "cpu",
            description="Device:",
            #style=style,
            disabled=False,
            layout=ipw.Layout(width="80%"),
        )
        self.device_dropdown.observe(self._update_device, names='value')
        tl.link((self.device_dropdown, "value"), (self.model, "device_name"))

        self.ncpus_input = ipw.BoundedIntText(
            value=self.model.ncpus,
            min=1,
            max=128,
            step=1,
            #style=style,
            description="No. CPUs:",
            disabled=False,
            layout=ipw.Layout(width="80%"),
        )
        tl.link((self.ncpus_input, "value"), (self.model, "ncpus"))

        self.label = ipw.Text(
            value=self.model.process_label,
            placeholder="Enter process label",
            description="Process Label:",
            disabled=False,
            #style=style,
            layout=ipw.Layout(width="80%"),
        )
        tl.link((self.label, "value"), (self.model, "process_label"))

        self.description = ipw.Textarea(
            value=self.model.process_description,
            placeholder="Enter process description",
            description="Description:",
            disabled=False,
            #style=style,
            layout=ipw.Layout(width="80%"),
        )
        tl.link((self.description, "value"), (self.model, "process_description"))

        self.children = [
            self.code_box,
            self.device_dropdown,
            self.ncpus_input,
            self.label,
            self.description,
        ]

    def update_codes(self, _=None) -> None:
        """Update the list of available codes."""
        qb = QueryBuilder()
        qb.append(Code, project=["label", "id"])
        codes = qb.all()
        code_names = [f"{name}" for name, id in codes]
        self.code.options = code_names
        if code_names:
            self.code.value = code_names[0]
        else:
            self.code.value = "No codes are available. Please add a code to AiiDA."
        return
    
    def _update_device(self, _) -> None:
        """Update the device options."""
        
        if self.device_dropdown.value.lower() == "cpu":
            self.ncpus_input.disabled = False
        else:
            self.ncpus_input.disabled = True
            
