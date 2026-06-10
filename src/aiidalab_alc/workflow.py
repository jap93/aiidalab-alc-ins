"""Module defining the MVC for MLIP workflow configuration."""

import aiidalab_widgets_base as awb
import ipywidgets as ipw
import traitlets as tl
from aiida.orm import SinglefileData

from aiidalab_alc.common.file_handling import FileUploadWidget, FilenameSelector, create_filename_selector

class MLIPWorkflowModel(tl.HasTraits):
    """The model for setting up a MLIP workflow."""

    #parameters for MLIP
    calc_style = tl.Unicode("Geometry optimisation", allow_none=False)
    optimisation = tl.Unicode("cell lengths", allow_none=False)
    maximum_force = tl.Float(0.001, allow_none=False)
    pressure = tl.Float(0.0, allow_none=False)
    force_field = tl.Unicode("mace_mp_small.model", allow_none=True)
    architecture = tl.Unicode("mace", allow_none=False)
    submitted = tl.Bool(False).tag(sync=True)
    use_dftd3 = tl.Bool(False).tag(sync=True)

    #phonon parameters
    auto_bands = tl.Bool(True).tag(sync=True)
    supercell_size_x = tl.Int(2).tag(sync=True)
    supercell_size_y = tl.Int(2).tag(sync=True) 
    supercell_size_z = tl.Int(2).tag(sync=True)
    number_points = tl.Int(51).tag(sync=True)

    default_guide = ""

class MethodWizardStep(ipw.VBox, awb.WizardAppWidgetStep):
    """Wizard setup for the calculation workflow."""

    def __init__(self, model: MLIPWorkflowModel, **kwargs):
        """
        MethodWizardStep constructor.

        Parameters
        ----------
        model : MLIPWorkflowModel
            The model that defines the data related to this step in the setup wizard.
        **kwargs :
            Keyword arguments passed to the parent class's constructor.
        """
        super().__init__(children=[], **kwargs)
        self.model = model
        self.rendered = False

        

        return
    
    def render(self):
        """Render the wizard contents if not already rendered."""
        if self.rendered:
            return

        self.header = ipw.HTML(
            """
            <h3> MLIP Calculation </h3>
            """,
            layout={"margin": "auto"},
        )
        self.guide = ipw.HTML(
            self.model.default_guide,
        )

        self.tabs = ipw.Tab()
        self.mlip_input_widget = ipw.HBox()
        self.mlip_options_widget = MLIPOptionsWidget(self.model)
        self.mlip_input_widget.children = [self.mlip_options_widget]

        self.phonon_input_widget = ipw.HBox()
        self.phonon_options_widget = PhononOptionsWidget(self.model)
        self.phonon_input_widget.children = [self.phonon_options_widget]
        
        self.tabs.children = [self.mlip_input_widget, self.phonon_input_widget]
        self.tabs.set_title(0, "MLIP Parameters")
        self.tabs.set_title(1, "Phonon Parameters")

        self.submit_btn = ipw.Button(
            description="Submit Options",
            disabled=False,
            button_style="success",
            tooltip="Submit the workflow configuration",
            icon="check",
            layout={"margin": "auto", "width": "60%"},
        )
        self.submit_btn.on_click(self._submit)

        self.error_output = ipw.HTML(layout={"margin": "10px auto", "width": "60%"})

        self.children = [
            self.header,
            self.guide,
            self.tabs,
            self.error_output,
            self.submit_btn,
        ]
        self.rendered = True
        return

    def _submit(self, _):
        """Store the MLIP parameters in the MLIP workflow model."""
        self.error_output.value = ""
        if not self.model.force_field:
            self.error_output.value = """
                <div style="background-color: #f8d7da; color: #721c24; padding: 10px; border: 1px solid #f5c6cb; border-radius: 5px;">
                    <strong>Error:</strong> No MLIP force field file provided.
                </div>"""
            return
        self.submit_btn.description = "Submitted"
        self.submit_btn.disabled = True
        self.mlip_options_widget.disable(True)
        self.phonon_options_widget.disable(True)
        self.model.submitted = True
        return

class MLIPOptionsWidget(ipw.VBox):
    """Widget for selecting the MLIP input options."""

    def __init__(self, model: MLIPWorkflowModel, **kwargs):
        """
        MLIPOptionsWidget constructor.

        Parameters
        ----------
        model : MLIPWorkflowModel
            The model that defines the phonon data.
        **kwargs :
            Keyword arguments passed to the parent class's constructor.
        """
        super().__init__(**kwargs)
        self.model = model
        self.rendered = False

        self.calculation_dropdown = ipw.Dropdown(
            options=["Single point", "Geometry optimisation"],
            description="Calculation:",
            disabled=False,
            layout={"width": "50%"},
        )
        self.calculation_dropdown.observe(self._update_optimisation, names='value')
        
        self.optimisation_dropdown = ipw.Dropdown(
            options=["cell lengths", "fully relax", "atoms only"],
            description="Optimisation:",
            disabled=False,
            layout={"width": "50%"},
        )
        
        self.enable_dftd3_chk = ipw.Checkbox(
            value=False, description="Use DFTd3", indent=True
        )
                
        self.pressure_text = ipw.BoundedFloatText(
            value=0.0,
            description="Pressure:",
            disabled=False,
            layout={"width": "50%"},
        )
        self.max_force_text = ipw.BoundedFloatText(
            value=0.001,
            min=0,
            step=0.001,
            description="Max force:",
            disabled=False,
            layout={"width": "50%"},
        )

        self.arch_dropdown = ipw.Dropdown(
            options=["mace"],
            description="Architecture:",
            disabled=False,
            layout={"width": "50%"},
        )

        self.ff_file = create_filename_selector(label="Model filename:", placeholder="mace_mp_small.model", 
                                        default="mace_mp_small.model")
    
        self.ff_file.observe(self.on_filename_change, names="filename")
        
        self.children = [
            self.calculation_dropdown,
            self.optimisation_dropdown,
            self.enable_dftd3_chk,
            self.pressure_text,
            self.max_force_text,
            self.arch_dropdown,
            self.ff_file,
        ]

        tl.link((self.calculation_dropdown, "value"), (self.model, "calc_style"))
        tl.link((self.optimisation_dropdown, "value"), (self.model, "optimisation"))
        tl.link((self.arch_dropdown, "value"), (self.model, "architecture"))
        tl.link((self.enable_dftd3_chk, "value"), (self.model, "use_dftd3"))
        tl.link((self.pressure_text, "value"), (self.model, "pressure"))
        tl.link((self.max_force_text, "value"), (self.model, "maximum_force"))

        # Ensure UI state matches initial model values
        self._update_optimisation(None)
        return
    
    def on_filename_change(self, change):
        self.model.force_field = self.ff_file.value

    #def _enable_dftd3_options(self, _) -> None:
    #    self.pressure_text.disabled = not self.enable_dftd3_chk.value
    #    self.max_force_text.disabled = not self.enable_dftd3_chk.value
    #    self.ff_file.disable(not self.enable_dftd3_chk.value)
    #    return

    def _update_optimisation(self, _) -> None:
        if self.calculation_dropdown.value.lower() == "geometry optimisation":
            self.optimisation_dropdown.disabled = False
            self.pressure_text.disabled = False
            self.max_force_text.disabled = False
        else:
            self.optimisation_dropdown.disabled = True
            self.pressure_text.disabled = True
            self.max_force_text.disabled = True
        return

    def render(self):
        """Render the options widget contents if not already rendered."""
        if self.rendered:
            return

        self.rendered = True
        return

    def disable(self, val: bool) -> None:
        """Disable the input fields."""
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = val
        #self.ff_file.disable(val)
        return
    
class PhononOptionsWidget(ipw.VBox):
    """Widget for selecting the MLIP input options."""

    def __init__(self, model: MLIPWorkflowModel, **kwargs):
        """
        MLIPOptionsWidget constructor.

        Parameters
        ----------
        model : MLIPWorkflowModel
            The model that defines the data related to this step in the setup wizard.
        **kwargs :
            Keyword arguments passed to the parent class's constructor.
        """
        super().__init__(**kwargs)
        self.model = model
        self.rendered = False

        style = {'description_width': 'initial'}
        self.x_axis_input = ipw.BoundedIntText(
            value=self.model.supercell_size_x,
            min=1,
            max=10,
            step=1,
            description="supercell size in x:", 
            style=style,
            disabled=False,
            layout=ipw.Layout(width="80%"),
        )
        tl.link((self.x_axis_input, "value"), (self.model, "supercell_size_x"))

        self.y_axis_input = ipw.BoundedIntText(
            value=self.model.supercell_size_y,
            min=1,
            max=10,
            step=1,
            description="supercell size in y:",
            style=style,
            disabled=False,
            layout=ipw.Layout(width="80%"),
        )
        tl.link((self.y_axis_input, "value"), (self.model, "supercell_size_y"))

        self.z_axis_input = ipw.BoundedIntText(
            value=self.model.supercell_size_z,
            min=1,
            max=10,
            step=1,
            description="supercell size in z:",
            style=style,
            disabled=False,
            layout=ipw.Layout(width="80%"),
        )
        tl.link((self.z_axis_input, "value"), (self.model, "supercell_size_z"))

        self.points_input = ipw.BoundedIntText(
            value=self.model.number_points,
            min=1,
            max=100,
            step=1,
            description="   number of points:",
            style=style,
            disabled=False,
            layout=ipw.Layout(width="80%"),
        )
        tl.link((self.points_input, "value"), (self.model, "number_points"))
      
        self.enable_auto_bands_chk = ipw.Checkbox(
            value=True, description="Auto bands calculation", indent=True
        )
                
        self.children = [
            self.x_axis_input,
            self.y_axis_input,
            self.z_axis_input,
            self.points_input,
            self.enable_auto_bands_chk,
        ]

        tl.link((self.enable_auto_bands_chk, "value"), (self.model, "auto_bands"))

        return
    
    
    def render(self):
        """Render the options widget contents if not already rendered."""
        if self.rendered:
            return

        self.rendered = True
        return

    def disable(self, val: bool) -> None:
        """Disable the input fields."""
        for child in self.children:
            child.disabled = val
        return
