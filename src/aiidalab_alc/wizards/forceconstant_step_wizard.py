"""Defines the view components for the force constant setup stage."""

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import aiidalab_widgets_base as awb
import ase
import ipywidgets as ipw
import traitlets as tl
import yaml
from aiida.orm import SinglefileData, StructureData
from aiida_alc_ins.data import ForceConstantsData
from euphonic import ForceConstants

from aiidalab_alc.common.file_handling import FileUploadWidget
from aiidalab_alc.common.file_selector import FilenameSelector
from aiidalab_alc.models.data_model import DataStepModel


class ForceConstantWizardStep(ipw.VBox, awb.WizardAppWidgetStep):
    """
    Wizard for force constant selection and manipulation.

    A step in a wizard based process widget which allows a user to
    configure force constants to be used in their workflow.
    """

    def __init__(self, model: DataStepModel, structure_step=None, **kwargs):
        """
        ForceConstantWizardStep constructor.

        Parameters
        ----------
        model : DataStepModel
            A model controlling the data required for the force constant step.
        structure_step : StructureWizardStep, optional
            The structure step, whose inputs are disabled once force constants
            are submitted.
        **kwargs :
            Keyword arguments passed to the parent class's constructor.
        """
        super().__init__(children=[], **kwargs)
        self.structure_step = structure_step
        self.rendered = False
        self.model = model

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
        self.castep_selector.observe(self._on_castep_path_change, names="filename")

        self.tabs.children = [
            self.file_input_widget,
        ]
        self.tabs.set_title(0, "Upload File")
        # self.tabs.set_title(1, "AiiDA Database")

        self.model.observe(self._on_file_upload, "force_constants_file")

    def _on_data_type_change(self, change):
        """Show the appropriate file input for the selected data format."""
        if change["new"] == "castep":
            self.model.force_constants_file = None
            self.model.force_constants_data = None
            self.model.force_constants_path = ""
            self.file_input_widget.children = [
                self.input_radio_btn,
                self.castep_selector,
            ]
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
        self,
        castep_data: bytes | str | Path,
        filename: str = "force_constants.castep_bin",
    ) -> ForceConstantsData:
        """Convert a CASTEP force-constants binary file into ForceConstantsData."""
        if castep_data is None:
            raise ValueError("CASTEP force-constants data is empty.")

        if isinstance(castep_data, Path):
            filename = castep_data.name
            content = castep_data.read_bytes()
        elif isinstance(castep_data, str):
            content = castep_data.encode("utf-8")
        else:
            content = bytes(castep_data)

        if not content:
            raise ValueError("CASTEP force-constants file is empty.")

        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / filename
            tmp_path.write_bytes(content)

            result = self._castep_via_force_constants_data(tmpdir, tmp_path)
            if result is None:
                result = self._castep_via_euphonic(tmp_path)
            if result is not None:
                return result

        raise ValueError(
            "Unable to build ForceConstantsData from the supplied CASTEP "
            "force-constants file. Install euphonic or provide a "
            "CASTEP-compatible importer on ForceConstantsData."
        )

    @staticmethod
    def _castep_via_force_constants_data(tmpdir: str, tmp_path: Path):
        """Try ``ForceConstantsData.from_castep``; return None if unavailable."""
        factory = getattr(ForceConstantsData, "from_castep", None)
        if not callable(factory):
            return None
        try:
            return factory(path=tmpdir, summary_name=tmp_path.name)
        except TypeError:
            pass
        try:
            return factory(str(tmp_path))
        except TypeError:
            return None

    @staticmethod
    def _castep_via_euphonic(tmp_path: Path):
        """Try euphonic's ``ForceConstants`` readers; return None on failure."""
        try:
            if hasattr(ForceConstants, "from_castep"):
                return ForceConstantsData(ForceConstants.from_castep(str(tmp_path)))
            if hasattr(ForceConstants, "from_file"):
                return ForceConstantsData(ForceConstants.from_file(str(tmp_path)))
        except Exception:
            return None
        return None

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
            raise ValueError(
                "Phonopy YAML does not contain a unit_cell or primitive_cell."
            )

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
        # print(f'Force constants data: {fc}')

        content = yaml.safe_dump(
            # {"force_constants": fc},
            {"force_constants": phonopy_data},
            sort_keys=False,
        ).encode("utf-8")
        return SinglefileData(
            file=BytesIO(content),
            filename="force_constants.yaml",
        )

    def _force_constants_data_to_structure_data(
        self, force_constants_data: ForceConstantsData
    ) -> StructureData:
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
