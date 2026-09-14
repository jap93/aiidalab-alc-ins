"""Module defining the MVC for MLIP workflow configuration."""

import aiidalab_widgets_base as awb
import ipywidgets as ipw
import traitlets as tl
from aiida.orm import SinglefileData

from aiidalab_alc.common.file_handling import FileUploadWidget, FilenameSelector, create_filename_selector
from aiidalab_alc.data import DataStepModel

class WorkflowCalculationModel(tl.HasTraits):
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

    #INS parameters
    use_ins_spacing = tl.Unicode("").tag(sync=True)

    ins_supercell_size_x = tl.Int(2).tag(sync=True)
    ins_supercell_size_y = tl.Int(2).tag(sync=True)
    ins_supercell_size_z = tl.Int(2).tag(sync=True)
    ins_spacing = tl.Float(0.1).tag(sync=True)
    ins_temperature = tl.Float(300.0).tag(sync=True)
    ins_energy_spacing = tl.Float(1.0).tag(sync=True)

    calculate_band_structure = tl.Bool(True).tag(sync=True)
    calculate_ins = tl.Bool(False).tag(sync=True)
    calculate_resins = tl.Bool(False).tag(sync=True)

    default_guide = ""

class WorkflowCalculationStep(ipw.VBox, awb.WizardAppWidgetStep):
    """Wizard for viewing process progress and results."""

    def __init__(self, data_model: DataStepModel, work_model: WorkflowCalculationModel, **kwargs):
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
        #self.model.observe(self._on_process_uuid_change, "process_uuid")

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

        
        vwr_panel = None
        if self.data_model.data_type == "ase_mlip":
            mlip_vwr = MethodWizardStep(model=self.work_model)
            mlip_vwr.render()
            vwr_panel = ipw.VBox(
                children=[
                    mlip_vwr,
                ]
            )

        elif self.data_model.data_type == "phonopy" or self.data_model.data_type == "castep":
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


class MethodWizardStep(ipw.VBox, awb.WizardAppWidgetStep):
    """Wizard setup for the calculation workflow."""

    def __init__(self, model: WorkflowCalculationModel, **kwargs):
        """
        MethodWizardStep constructor.

        Parameters
        ----------
        model : WorkflowCalculationModel
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
            tooltip="Submit the MLIP workflow configuration",
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

    def __init__(self, model: WorkflowCalculationModel, **kwargs):
        """
        MLIPOptionsWidget constructor.

        Parameters
        ----------
        model : WorkflowCalculationModel
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
    """Widget for selecting the Phonon input options."""

    def __init__(self, model: WorkflowCalculationModel, **kwargs):
        """
        PhononOptionsWidget constructor.

        Parameters
        ----------
        model : WorkflowCalculationModel
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
    
class INSOptionsWidget(ipw.VBox):
    """Widget for selecting the INS input options."""

    def __init__(self, model: WorkflowCalculationModel, **kwargs):
        """
        INSOptionsWidget constructor.

        Parameters
        ----------
        model : WorkflowCalculationModel
            The model that defines the data related to this step in the setup wizard.
        **kwargs :
            Keyword arguments passed to the parent class's constructor.
        """
        super().__init__(**kwargs)
        self.model = model
        self.rendered = False

        self.header = ipw.HTML(
            """
            <h3> INS Calculation </h3>
            """,
            layout={"margin": "auto"},
        )
        #radio buttons for INS options
        self.ins_options = INSInputWidget(model=self.model)
        self.ins_options.render()

        style = {'description_width': 'initial'}
        self.x_axis_input = ipw.BoundedIntText(
            value=self.model.supercell_size_x,
            min=1,
            max=10,
            step=1,
            description="MP grid in x:",
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
            description="MP grid in y:",
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
            description="MP grid in z:",
            style=style,
            disabled=False,
            layout=ipw.Layout(width="80%"),
        )
        tl.link((self.z_axis_input, "value"), (self.model, "supercell_size_z"))

        self.points_input = ipw.BoundedFloatText(
            value=self.model.ins_spacing,
            min=0.0001,
            max=1,
            step=0.001,
            description=" Spacing:",
            style=style,
            disabled=False,
            layout=ipw.Layout(width="80%"),
        )
        tl.link((self.points_input, "value"), (self.model, "ins_spacing"))

        self.temperature_input = ipw.BoundedFloatText(
            value=self.model.ins_temperature,
            min=0.0001,
            max=1000,
            step=1,
            description="Temperature, K:",
            style=style,
            disabled=False,
            layout=ipw.Layout(width="80%"),
        )
        tl.link((self.temperature_input, "value"), (self.model, "ins_temperature"))

        self.energy_spacing_input = ipw.BoundedFloatText(
            value=self.model.ins_energy_spacing,
            min=0.0001,
            max=1000,
            step=1,
            description="Energy Spacing for DOS, eV:",
            style=style,
            disabled=False,
            layout=ipw.Layout(width="80%"),
        )
        tl.link((self.energy_spacing_input, "value"), (self.model, "ins_energy_spacing"))
        self.calculate_band_structure_chk = ipw.Checkbox(
            value=True, description="band structure calculation", indent=True
        )
        self.calculate_ins_chk = ipw.Checkbox(
            value=False, description="Calculate INS", indent=True
        )
        self.calculate_resins_chk = ipw.Checkbox(
            value=False, description="Calculate RESINS", indent=True
        )

        self.submit_btn = ipw.Button(
            description="Submit Options",
                disabled=False,
                button_style="success",
                tooltip="Submit the INS workflow configuration",
                icon="check",
                layout={"margin": "auto", "width": "60%"},
            )
        self.submit_btn.on_click(self._submit)

        self.model.observe(self._update_inputs, names="use_ins_spacing")
        self._update_inputs()

        tl.link((self.calculate_band_structure_chk, "value"), (self.model, "calculate_band_structure"))
        tl.link((self.calculate_ins_chk, "value"), (self.model, "calculate_ins"))
        tl.link((self.calculate_resins_chk, "value"), (self.model, "calculate_resins"))

        return

    def _submit(self, _):
            """Store the MLIP parameters in the MLIP/INS workflow model."""
            #self.error_output.value = ""
            #if not self.model.force_field:
            #    self.error_output.value = """
            #        <div style="background-color: #f8d7da; color: #721c24; padding: 10px; border: 1px solid #f5c6cb; border-radius: 5px;">
            #            <strong>Error:</strong> No MLIP force field file provided.
            #        </div>"""
            #    return
            self.submit_btn.description = "Submitted INS Options"
            self.submit_btn.disabled = True
            self.calculate_band_structure_chk.disabled = True
            self.energy_spacing_input.disabled = True
            self.temperature_input.disabled = True
            self.points_input.disabled = True
            self.x_axis_input.disabled = True
            self.y_axis_input.disabled = True       
            self.z_axis_input.disabled = True
            self.calculate_ins_chk.disabled = True
            self.calculate_resins_chk.disabled = True
            self.model.submitted = True
            return

    def _update_inputs(self, _=None) -> None:
        """Show either spacing or supercell controls for the selected mode."""
        
        if self.model.use_ins_spacing == "Use spacing":
            self.children = [
                self.header,
                self.ins_options, 
                self.points_input, 
                self.temperature_input,
                self.energy_spacing_input,
                self.calculate_band_structure_chk,
                self.calculate_ins_chk,
                self.calculate_resins_chk,
                self.submit_btn,
            ]
        else:
            self.children = [
                self.header,
                self.ins_options,
                self.x_axis_input,
                self.y_axis_input,
                self.z_axis_input,
                self.temperature_input,
                self.energy_spacing_input,
                self.calculate_band_structure_chk,
                self.calculate_ins_chk,
                self.calculate_resins_chk,
                self.submit_btn,
            ]
    
    
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

class INSInputWidget(ipw.VBox):
    """Widget for the data input step."""

    value = tl.Unicode("Use supercell size", allow_none=True)

    def __init__(self, model: WorkflowCalculationModel, **kwargs):
        """
        DataInputWidget constructor.

        Parameters
        ----------
        model : WorkflowCalculationModel
            The model controlling required workflow.
        **kwargs :
            Keyword arguments passed to the parent class's constructor.
        """
        super().__init__(**kwargs)
        self.model = model
        self.rendered = False
        self.input_method = None
        self.model.use_ins_spacing = self.value

    def _on_input_method_change(self, change):
        """Keep the widget value synchronized with the selected radio button."""
        self.value = change["new"]
        self.model.use_ins_spacing = self.value
        print(f"Data input method changed to: {self.value}")

    def render(self) -> None:
        """Render the view's content."""
        if self.rendered:
            return

        self.input_method = ipw.RadioButtons(
            options=["Use supercell size", "Use spacing"],
            value="Use supercell size",
            description="INS options:",
            disabled=False,
        )
        self.input_method.observe(self._on_input_method_change, "value")

        self.children = [
            self.input_method,
        ]
        self.rendered = True
