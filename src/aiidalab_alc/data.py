"""Defines the model and view components for the structure setup stage."""

from pathlib import Path
from io import BytesIO
from tempfile import NamedTemporaryFile

import yaml

import aiidalab_widgets_base as awb
import ase
import ipywidgets as ipw
import traitlets as tl
from aiida.orm import SinglefileData, StructureData, JsonableData

from aiidalab_alc.common.database import AiiDADatabaseWidget
from aiidalab_alc.common.file_handling import FileUploadWidget

import sys
from pathlib import Path as PathlibPath

class DataStepModel(tl.HasTraits):
    """
    Model for structure selection and manipulation.

    A model to define and store required information from the structure
    step in the app's configuration wizard.
    """

    data_type = tl.Unicode("", allow_none=True)

    structure = tl.Instance(StructureData, allow_none=True)
    structure_file = tl.Instance(SinglefileData, allow_none=True)

    force_constants_file = tl.Instance(SinglefileData, allow_none=True)
    submitted = tl.Bool(False).tag(sync=True)

    default_guide = ""

    @property
    def has_structure(self) -> bool:
        """True if a StructureData object has been attached to the model."""
        return self.structure is not None

    @property
    def has_file(self) -> bool:
        """True if a raw structure file object has been attached to the model."""
        return self.structure_file is not None

    @property
    def is_periodic(self) -> bool:
        """True if the attached StructureData object is a periodic structure."""
        if self.has_structure:
            return any(self.structure.pbc)
        return False

    @property
    def has_force_constants(self) -> bool:
        """True if force constants have been attached to the model."""
        return self.force_constants_file is not None

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
        fc_vwr = ForceConstantWizardStep(model=self.model)
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
            children=[structure_panel, force_constants_panel],
            selected_index=None,
        )
        accordion.set_title(0, "Structure")
        accordion.set_title(1, "Force Constants")

        self.children = [
            accordion,
        ]

class StructureWizardStep(ipw.VBox, awb.WizardAppWidgetStep):
    """
    Wizard for structure selection and manipulation.

    A step in a wizard based process widget which allows a user to
    configure a chemical structure to be used in their workflow.
    """

    def __init__(self, model: DataStepModel, **kwargs):
        """
        StructureWizardStep constructor.

        Parameters
        ----------
        model : DataStepModel
            A model controlling the data required for the structure step.
        **kwargs :
            Keyword arguments passed to the parent class's constructor.
        """
        super().__init__(children=[], **kwargs)
        self.rendered = False
        self.model = model

        self.tabs = ipw.Tab()

        # upload file
        self.tabs.set_title(0, "Upload File")
        self.file_input_widget = ipw.VBox()
        self.file_uploader = FileUploadWidget(description="Structure file: ")
        self.file_input_widget.children = [
            self.file_uploader,
        ]
        ipw.dlink((self.file_uploader, "file"), (self.model, "structure_file"))

        # AiiDA database
        self.tabs.set_title(1, "AiiDA Database")
        self.database_widget = AiiDADatabaseWidget(
            title="AiiDA Database",
            query=[
                SinglefileData,
            ],
        )
        ipw.dlink((self.database_widget, "data_object"), (self.model, "structure_file"))

        self.tabs.children = [self.file_input_widget, self.database_widget]

        self.model.observe(self._on_file_upload, "structure_file")

    def render(self):
        """Render the wizard's contents if not already rendered."""
        if self.rendered:
            return

        self.submit_btn = ipw.Button(
            description="Submit Structure",
            disabled=False,
            button_style="success",
            tooltip="Submit the structure to the workflow",
            icon="check",
            layout={"margin": "auto", "width": "60%"},
        )
        self.submit_btn.on_click(self.submit_structure)
        self.viewer = ipw.HTML("<p>No structure found...</p>")

        self._update_children()
        self.rendered = True
        return

    def _update_children(self) -> None:
        self.children = [
            self.tabs,
            ipw.HTML("<h2>Viewer:</h2>"),
            self.viewer,
            self.submit_btn,
        ]
        return

    def _on_file_upload(self, change=None):
        """When file upload button is pressed."""
        if self.model.has_file:
            atoms = self._get_ase_object_from_file(
                self.model.structure_file.filename, self.model.structure_file.content
            )
            self.model.structure = self._ase_to_structure_data(atoms) if atoms else None
            if self.model.structure:
                self.viewer = awb.viewers.StructureDataViewer(structure=atoms)
            else:
                self.viewer = ipw.HTML(
                    "<p>Could not visualise structure from file...</p>"
                )
            self._update_children()
        return

    def _get_ase_object_from_file(self, fname: str, content: bytes) -> ase.Atoms | None:
        suffix = "".join(Path(fname).suffixes)
        with NamedTemporaryFile(suffix=suffix) as tmpf:
            tmpf.write(content)
            tmpf.flush()
            try:
                structure = ase.io.read(tmpf.name, index=":")[0]
            except (KeyError, ase.io.formats.UnknownFileTypeError):
                structure = None
        return structure

    def _ase_to_structure_data(self, atoms: ase.Atoms) -> StructureData:
        """Convert ASE Atoms object to AiiDA StructureData."""
        return StructureData(ase=atoms)

    def submit_structure(self, _):
        """Submit the structure step."""
        if self.model.has_file or self.model.has_structure:
            self.file_uploader.disable(True)
            self.database_widget.disable(True)
            self.submit_btn.disabled = True
            self.model.data_type = "ase_mlip"
            self.submit_btn.description = "Submitted"
            self.model.submitted = True
        else:
            self.model.submitted = False
        return

#start to process the force constants file(s)
class ForceConstantWizardStep(ipw.VBox, awb.WizardAppWidgetStep):
    """
    Wizard for force constant selection and manipulation.

    A step in a wizard based process widget which allows a user to
    configure force constants to be used in their workflow.
    """

    def __init__(self, model: DataStepModel, **kwargs):
        """
        ForceConstantWizardStep constructor.

        Parameters
        ----------
        model : DataStepModel
            A model controlling the data required for the force constant step.
        **kwargs :
            Keyword arguments passed to the parent class's constructor.
        """
        super().__init__(children=[], **kwargs)
        self.rendered = False
        self.model = model

        self.tabs = ipw.Tab()

        # upload file
        self.tabs.set_title(0, "Upload File")
        self.file_input_widget = ipw.VBox()
        self.input_radio_btn = DataInputWidget(model=self.model)
        self.input_radio_btn.render()
        self.file_uploader = FileUploadWidget(description="force constants: ")
        self.file_input_widget.children = [
            self.input_radio_btn,
            self.file_uploader,
        ]
        ipw.dlink((self.file_uploader, "file"), (self.model, "force_constants_file"))

        # AiiDA database
        self.tabs.set_title(1, "AiiDA Database")
        self.database_widget = AiiDADatabaseWidget(
            title="AiiDA Database",
            query=[
                SinglefileData,
            ],
        )
        ipw.dlink((self.database_widget, "data_object"), (self.model, "force_constants_file"))

        self.tabs.children = [self.file_input_widget, self.database_widget]

        self.model.observe(self._on_file_upload, "force_constants_file")

    def render(self):
        """Render the wizard's contents if not already rendered."""
        if self.rendered:
            return

        self.submit_btn = ipw.Button(
            description="Submit Force Constants",
            disabled=False,
            button_style="success",
            tooltip="Submit the force constants to the workflow",
            icon="check",
            layout={"margin": "auto", "width": "60%"},
        )
        self.submit_btn.on_click(self.submit_force_constants)

        self._update_children()
        self.rendered = True
        return

    def _update_children(self) -> None:
        self.children = [
            self.tabs,
            self.submit_btn,
        ]
        return

    def _on_file_upload(self, change=None):
        """When file upload button is pressed."""
        if self.model.data_type == "phonopy" and not self.model.has_force_constants:
            phonopy_data = self.model.force_constants_file.get_content()
            self.model.force_constants_file = self._phonopy_to_single_file_data(
                phonopy_data
            )
            self.model.structure = self._phonpopy_to_structure_data(
                phonopy_data
            )
            
            
            self._update_children()
        if self.model.data_type == "castep" and self.model.has_force_constants:
            print(f"Force constants file uploaded from castep: {self.model.force_constants_file.filename}")
            #print(f"self.model.force_constants_file.content {self.model.force_constants_file.content}")
            #self.model.force_constants_file = read_force_constants_from_castep(self.model.force_constants_file.filename)
            self.model.force_constants_file = ForceConstants.from_castep(self.model.force_constants_file.filename)
            self._update_children()
        return

    def submit_force_constants(self, _):
        """Submit the force constants step."""
        if self.model.has_force_constants:
            self.file_uploader.disable(True)
            self.database_widget.disable(True)
            self.submit_btn.disabled = True
            self.submit_btn.description = "Submitted Force Constants"
            self.model.submitted = True
        else:
            self.model.submitted = False
        return

    def _phonpopy_to_structure_data(
        self, phonopy_data: bytes | str | dict
    ) -> StructureData:
        """Convert a Phonopy YAML document to an AiiDA structure."""
        if isinstance(phonopy_data, bytes):
            phonopy_data = phonopy_data.decode("utf-8")
        if isinstance(phonopy_data, str):
            phonopy_data = yaml.safe_load(phonopy_data)
        if not isinstance(phonopy_data, dict):
            raise ValueError("Phonopy data must be YAML text or a mapping.")

        cell_data = phonopy_data.get("unit_cell") or phonopy_data.get("primitive_cell")
        if not isinstance(cell_data, dict):
            raise ValueError("Phonopy YAML does not contain a unit_cell or primitive_cell.")

        lattice = cell_data.get("lattice")
        points = cell_data.get("points")
        if not lattice or not points:
            raise ValueError("Phonopy cell must contain lattice and points.")

        atoms = ase.Atoms(
            symbols=[point["symbol"] for point in points],
            cell=lattice,
            scaled_positions=[point["coordinates"] for point in points],
            pbc=True,
        )
        return StructureData(ase=atoms)

    def _phonopy_to_single_file_data(
        self, phonopy_data: bytes | str | dict
    ) -> SinglefileData:
        """Convert a Phonopy YAML document to a SinglefileData object."""
        if isinstance(phonopy_data, bytes):
            phonopy_data = phonopy_data.decode("utf-8")
        if isinstance(phonopy_data, str):
            phonopy_data = yaml.safe_load(phonopy_data)
        if not isinstance(phonopy_data, dict):
            raise ValueError("Phonopy data must be YAML text or a mapping.")

        fc = phonopy_data.get("force_constants")
        if not isinstance(fc, dict):
            raise ValueError("Phonopy YAML does not contain force_constants.")
        #print(f'Force constants data: {fc}')

        content = yaml.safe_dump(
            #{"force_constants": fc},
            {"force_constants":phonopy_data},
            sort_keys=False,
        ).encode("utf-8")
        return SinglefileData(
            file=BytesIO(content),
            filename="force_constants.yaml",
        )
    

class DataInputWidget(ipw.VBox):
    """Widget for the data input step."""

    value = tl.Unicode("phonopy", allow_none=True)

    def __init__(self, model: DataStepModel, **kwargs):
        """
        DataInputWidget constructor.

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
        self.input_method = None
        self.model.data_type = self.value

    def _on_input_method_change(self, change):
        """Keep the widget value synchronized with the selected radio button."""
        self.value = change["new"]
        self.model.data_type = self.value
        print(f"Data input method changed to: {self.value}")

    def render(self) -> None:
        """Render the view's content."""
        if self.rendered:
            return

        self.input_method = ipw.RadioButtons(
            options=["phonopy", "castep"],
            value=self.value,
            description="Input Method:",
            disabled=False,
        )
        self.input_method.observe(self._on_input_method_change, "value")

        self.children = [
            self.input_method,
        ]
        self.rendered = True

    
# %%
