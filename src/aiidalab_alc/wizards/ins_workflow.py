"""Widgets for configuring the INS workflow."""

import ipywidgets as ipw
import traitlets as tl

from aiidalab_alc.models.workflow_model import WorkflowCalculationModel


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
        # radio buttons for INS options
        self.ins_options = INSInputWidget(model=self.model)
        self.ins_options.render()

        style = {"description_width": "initial"}
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
            description=" q-spacing:",
            style=style,
            disabled=False,
            layout=ipw.Layout(width="80%"),
        )
        tl.link((self.points_input, "value"), (self.model, "ins_spacing"))

        self.resins_qspacing_input = ipw.BoundedFloatText(
            value=self.model.ins_resins_qspacing,
            min=0.0001,
            max=1,
            step=0.01,
            description="q-spacing RESINS/TOSCA:",
            style=style,
            disabled=False,
            layout=ipw.Layout(width="80%"),
        )
        tl.link(
            (self.resins_qspacing_input, "value"), (self.model, "ins_resins_qspacing")
        )

        self.resins_energy_spacing_input = ipw.BoundedFloatText(
            value=self.model.ins_resins_energy_spacing,
            min=0.0001,
            max=10,
            step=1,
            description="Energy Spacing RESINS/TOSCA:",
            style=style,
            disabled=False,
            layout=ipw.Layout(width="80%"),
        )
        tl.link(
            (self.resins_energy_spacing_input, "value"),
            (self.model, "ins_resins_energy_spacing"),
        )

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

        self.dos_qspacing_input = ipw.BoundedFloatText(
            value=self.model.ins_dos_qspacing,
            min=0.0001,
            max=1,
            step=0.01,
            description="q-spacing for DOS:",
            style=style,
            disabled=False,
            layout=ipw.Layout(width="80%"),
        )
        tl.link((self.dos_qspacing_input, "value"), (self.model, "ins_dos_qspacing"))

        self.energy_spacing_input = ipw.BoundedFloatText(
            value=self.model.ins_dos_energy_spacing,
            min=0.0001,
            max=1000,
            step=1,
            description="Energy Spacing for DOS, meV:",
            style=style,
            disabled=False,
            layout=ipw.Layout(width="80%"),
        )
        tl.link(
            (self.energy_spacing_input, "value"), (self.model, "ins_dos_energy_spacing")
        )
        self.calculate_band_structure_chk = ipw.Checkbox(
            value=True,
            description="band structure calculation",
            indent=True,
            disabled=True,
        )
        # self.calculate_ins_chk = ipw.Checkbox(
        #    value=False, description="Calculate INS", indent=True
        # )
        self.calculate_resins_chk = ipw.Checkbox(
            value=False, description="Calculate RESINS/TOSCA ", indent=True
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

        # tl.link(
        #     (self.calculate_band_structure_chk, "value"),
        #     (self.model, "calculate_band_structure"),
        # )
        # tl.link((self.calculate_ins_chk, "value"), (self.model, "calculate_ins"))
        tl.link((self.calculate_resins_chk, "value"), (self.model, "calculate_resins"))

        return

    def _submit(self, _):
        """Store the MLIP parameters in the MLIP/INS workflow model."""
        # self.error_output.value = ""
        # if not self.model.force_field:
        #    self.error_output.value = """
        #        <div style="background-color: #f8d7da; color: #721c24;
        #            padding: 10px; border: 1px solid #f5c6cb;
        #            border-radius: 5px;">
        #            <strong>Error:</strong> No MLIP force field file provided.
        #        </div>"""
        #    return
        self.ins_options._disable()
        self.submit_btn.description = "Submitted INS Options"
        self.submit_btn.disabled = True
        self.calculate_band_structure_chk.disabled = True
        self.energy_spacing_input.disabled = True
        self.temperature_input.disabled = True
        self.points_input.disabled = True
        self.dos_qspacing_input.disabled = True
        self.resins_qspacing_input.disabled = True
        self.resins_energy_spacing_input.disabled = True
        self.x_axis_input.disabled = True
        self.y_axis_input.disabled = True
        self.z_axis_input.disabled = True
        # self.calculate_ins_chk.disabled = True
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
                self.dos_qspacing_input,
                self.energy_spacing_input,
                self.resins_qspacing_input,
                self.resins_energy_spacing_input,
                self.calculate_band_structure_chk,
                # self.calculate_ins_chk,
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
                # self.calculate_ins_chk,
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

    value = tl.Unicode("Use spacing", allow_none=True)

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
            value="Use spacing",
            description="INS options:",
            disabled=False,
        )
        self.input_method.observe(self._on_input_method_change, "value")

        self.children = [
            self.input_method,
        ]
        self.rendered = True

    def _disable(self):
        """Disable the input method radio buttons."""
        if self.input_method:
            self.input_method.disabled = True
