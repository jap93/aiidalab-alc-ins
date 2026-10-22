"""Defines the model and view components for the structure setup stage."""

from pathlib import Path
from io import BytesIO
from tempfile import NamedTemporaryFile, TemporaryDirectory

import yaml

import aiidalab_widgets_base as awb
import ase
import ipywidgets as ipw
import traitlets as tl
from aiida.orm import SinglefileData, StructureData, JsonableData
from aiida_pythonjob_ins.data import ForceConstantsData
from euphonic import ForceConstants

from aiidalab_alc.common.database import AiiDADatabaseWidget
from aiidalab_alc.common.file_handling import FileUploadWidget
from aiidalab_alc.common.file_selector import FilenameSelector

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
    force_constants_path = tl.Unicode("", allow_none=False)
    force_constants_data = tl.Instance(ForceConstantsData, allow_none=True)
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
        return (
            self.force_constants_file is not None
            or self.force_constants_data is not None
        )

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
        self.force_constants_step = None

        self.tabs = ipw.Tab()

        # upload file
        self.file_input_widget = ipw.VBox()
        self.file_uploader = FileUploadWidget(description="Structure file: ")
        self.file_input_widget.children = [
            self.file_uploader,
        ]
        ipw.dlink((self.file_uploader, "file"), (self.model, "structure_file"))

        # AiiDA database
        self.database_widget = AiiDADatabaseWidget(
            title="AiiDA Database",
            query=[
                SinglefileData,
            ],
        )
        ipw.dlink((self.database_widget, "data_object"), (self.model, "structure_file"))

        self.tabs.children = [self.file_input_widget, self.database_widget]

        self.tabs.set_title(0, "Upload File")
        self.tabs.set_title(1, "AiiDA Database")

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

    def disable_inputs(self) -> None:
        """Disable structure inputs after the structure has been submitted."""
        self.file_uploader.disable(True)
        self.database_widget.disable(True)
        self.submit_btn.disabled = True

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
            self.disable_inputs()
            if self.force_constants_step is not None:
                self.force_constants_step.disable_inputs()
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

    def __init__(
        self,
        model: DataStepModel,
        structure_step: StructureWizardStep | None = None,
        **kwargs,
    ):
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
        self.structure_step = structure_step

        self.tabs = ipw.Tab()

        # upload file
        self.file_input_widget = ipw.VBox()
        self.input_radio_btn = DataInputWidget(model=self.model)
        self.input_radio_btn.render()
        self.file_uploader = FileUploadWidget(description="force constants: ")
        self.castep_selector = FilenameSelector(
            extensions=[".castep_bin"],
            default="",
        )
        self.file_input_widget.children = [self.input_radio_btn, self.file_uploader]
        ipw.dlink((self.file_uploader, "file"), (self.model, "force_constants_file"))
        self.input_radio_btn.observe(self._on_data_type_change, names="value")
        self.castep_selector.observe(
            self._on_castep_path_change, names="filename"
        )

        # AiiDA database
        #self.database_widget = AiiDADatabaseWidget(
        #    title="AiiDA Database",
        #    query=[
        #        SinglefileData,
        #    ],
        #)
        #ipw.dlink((self.database_widget, "data_object"), (self.model, "force_constants_file"))

        self.tabs.children = [self.file_input_widget, ]
        self.tabs.set_title(0, "Upload File")
        #self.tabs.set_title(1, "AiiDA Database")

        self.model.observe(self._on_file_upload, "force_constants_file")

    def _on_data_type_change(self, change):
        """Show the appropriate file input for the selected data format."""
        if change["new"] == "castep":
            self.model.force_constants_file = None
            self.model.force_constants_data = None
            self.model.force_constants_path = ""
            self.file_input_widget.children = [self.input_radio_btn, self.castep_selector]
        else:
            self.model.force_constants_path = ""
            self.model.force_constants_data = None
            self.file_input_widget.children = [self.input_radio_btn, self.file_uploader]

    def _on_castep_path_change(self, change):
        """Load force constants and structure from the selected CASTEP file."""
        filename = change["new"]
        self.model.force_constants_path = filename
        self.model.force_constants_data = None
        if not filename:
            return

        self.model.force_constants_data = ForceConstantsData.from_castep(filename)
        self.model.structure = self._force_constants_data_to_structure_data(
            self.model.force_constants_data
        )

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
        """Clear previously parsed data when the uploaded file changes."""
        self.model.force_constants_data = None

    def disable_inputs(self) -> None:
        """Disable force-constant inputs after a structure is submitted."""
        self.file_uploader.disable(True)
        self.castep_selector.disabled = True
        self.submit_btn.disabled = True
        self.input_radio_btn._disable()

    def submit_force_constants(self, _):
        """Submit the force constants step."""
        if self.model.has_force_constants:
            if self.structure_step is not None:
                self.structure_step.disable_inputs()
            self.disable_inputs()

            if self.model.data_type == "phonopy" and self.model.force_constants_file:
                self.model.structure = self._phonpopy_to_structure_data(
                    self.model.force_constants_file.get_content()
                )
               
                filename = self.model.force_constants_file.filename
                phonopy_data = self.model.force_constants_file.get_content()
                
                self.model.force_constants_data = self._phonopy_to_force_constants_data(
                    phonopy_data
                )

                self.submit_btn.description = "Submitted Force Constants from Phonopy"
                self.model.submitted = True
        
            elif (
                self.model.data_type == "castep"
                and self.model.force_constants_path
                and self.model.force_constants_data
            ):
                self.submit_btn.description = "Submitted Force Constants from CASTEP"
                self.model.submitted = True
        else:
            self.model.submitted = False
        return

    def _castep_bin_to_force_constants_data(
        self, castep_data: bytes | str | Path, filename: str = "force_constants.castep_bin"
    ) -> ForceConstantsData:
        """Convert a CASTEP force-constants binary file into a ForceConstantsData node."""
        if castep_data is None:
            raise ValueError("CASTEP force-constants data is empty.")

        if isinstance(castep_data, Path):
            source_path = Path(castep_data)
            filename = source_path.name
            content = source_path.read_bytes()
        elif isinstance(castep_data, str):
            content = castep_data.encode("utf-8")
        else:
            content = bytes(castep_data)

        if not content:
            raise ValueError("CASTEP force-constants file is empty.")

        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / filename
            tmp_path.write_bytes(content)

            factory = getattr(ForceConstantsData, "from_castep", None)
            if callable(factory):
                try:
                    return factory(path=tmpdir, summary_name=tmp_path.name)
                except TypeError:
                    try:
                        return factory(str(tmp_path))
                    except TypeError:
                        pass

            try:
                
                if hasattr(ForceConstants, "from_castep"):
                    force_constants = ForceConstants.from_castep(str(tmp_path))
                    return ForceConstantsData(force_constants)
                if hasattr(ForceConstants, "from_file"):
                    force_constants = ForceConstants.from_file(str(tmp_path))
                    return ForceConstantsData(force_constants)
            except Exception:
                pass

        raise ValueError(
            "Unable to build ForceConstantsData from the supplied CASTEP force-constants file. "
            "Install euphonic or provide a CASTEP-compatible importer on ForceConstantsData."
        )

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

    def _phonopy_to_force_constants_data(
        self, phonopy_data: bytes | str | dict
    ) -> ForceConstantsData:
        """Convert a Phonopy YAML document to a ForceConstantsData object."""
        if isinstance(phonopy_data, bytes):
            phonopy_data = phonopy_data.decode("utf-8")
        if isinstance(phonopy_data, str):
            phonopy_data = yaml.safe_load(phonopy_data)
        if not isinstance(phonopy_data, dict):
            raise ValueError("Phonopy data must be YAML text or a mapping.")

        if "force_constants" not in phonopy_data:
            raise ValueError("Phonopy YAML does not contain force_constants.")

        with TemporaryDirectory() as tmpdir:
            summary_name = "phonopy_data.yaml"
            tmp_path = Path(tmpdir) / summary_name
            tmp_path.write_text(
                yaml.safe_dump(phonopy_data, sort_keys=False),
                encoding="utf-8",
            )
            return ForceConstantsData.from_phonopy(
                path=tmpdir,
                summary_name=summary_name,
            )

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

    def _force_constants_data_to_structure_data(self, force_constants_data: ForceConstantsData) -> StructureData:
        """Convert a ForceConstantsData object to an AiiDA StructureData object."""
        if not isinstance(force_constants_data, ForceConstantsData):
            raise ValueError("Input must be a ForceConstantsData object.")

        phon = force_constants_data.get_force_constants().to_dict()
        crystal = phon["crystal"]
        atoms = ase.Atoms(
            symbols=crystal["atom_type"],
            cell=crystal["cell_vectors"],
            scaled_positions=crystal["atom_r"],
            pbc=True,
        )
        return StructureData(ase=atoms)
    

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

    def _disable(self):
        """Disable the input method radio buttons."""
        if self.input_method:
            self.input_method.disabled = True   

    
# %%
