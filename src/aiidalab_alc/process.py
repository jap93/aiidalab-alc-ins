"""Module for handling AiiDA processes."""
import io
import lzma
import yaml
import shutil

import traitlets as tl
from aiida.engine import submit
from aiida.orm import Dict, load_code
from ipywidgets import dlink
from IPython.display import Javascript, display, clear_output
from pathlib import Path
from aiida_mlip.data.model import ModelData
from aiida.orm import StructureData
from aiida.orm import load_code, load_node
from aiida.orm import Str, Float, Bool, Int, BandsData, KpointsData
from aiida.plugins import CalculationFactory
from aiida_workgraph import WorkGraph

from aiidalab_alc.resources import ComputationalResourcesModel
from aiidalab_alc.results import ResultsModel
from aiidalab_alc.structure import StructureStepModel
from aiidalab_alc.workflow import MLIPWorkflowModel

from ase import Atoms
import numpy as np

class MainAppModel(tl.HasTraits):
    """The main AiiDAlab application MVC model."""

    block_results = tl.Bool(True, allow_none=False)

    def __init__(self):
        """MainAppModel constructor."""
        super().__init__()
        self.structure_model = StructureStepModel()
        self.workflow_model = MLIPWorkflowModel()
        self.resource_model = ComputationalResourcesModel()
        self.results_model = ResultsModel()

        self.resource_model.observe(self._submit_model, "submitted")
        dlink((self, "block_results"), (self.results_model, "blocked"))
        
        self.process = None

        return

    def _submit_model(self, _) -> None:
        """Handle the submission of the AiiDA process."""
        if MLIPProcess.validate_model(self):
            self.process = MLIPProcess(self)
            self.process.submit_process()
            self.block_results = False

            self.results_model.process_uuid = self.process.node.uuid
            
        else:
            print("ERROR: Input Validation Failed")
        return

    def reset(self) -> None:
        """Reset the state of the model."""
        self.submitted = False

class MLIPProcess:
    """Class to handle a MLIP AiiDA process."""

    def __init__(self, model: MainAppModel):
        """
        MLIPProcess constructor.

        Parameters
        ----------
        model : MainAppModel
            The main application model containing all necessary data.
        """
        self.model = model
        self.node = None
        return

    @classmethod
    def validate_model(cls, model: MainAppModel) -> bool:
        """
        Validate the main application model.

        Parameters
        ----------
        model : MainAppModel
            The main application model to validate.

        Returns
        -------
        bool
            True if the model is valid, False otherwise.
        """
        



        if not model.structure_model.has_structure:
            if not model.structure_model.has_file:
                print("No structure provided.")
                return False
            
        if not model.workflow_model.force_field:
            print("No force field provided.")
            return False
        
        # Add more validation checks as needed
        return True


    def submit_process(self):
        """Submit the AiiDA process."""

        structure = self.model.structure_model.structure
        code = load_code(self.model.resource_model.code_name)

        device = self.model.resource_model.device_name   

        model_file = self.model.workflow_model.force_field
        if not Path(model_file).exists():
            print("model file does not exist", model_file)

        architecture = self.model.workflow_model.architecture
        mlip_model = ModelData.from_local(model_file, architecture=architecture)

        calculation_style = self.model.workflow_model.calc_style.lower()
        optimisation = self.model.workflow_model.optimisation.lower()

        dftd3 = self.model.workflow_model.use_dftd3

        if calculation_style == "geometry optimisation":
            inputs_geom = {
                "code": code,
                "model": mlip_model,
                "struct": structure,
                "device": Str(device),
                "fmax": Float(self.model.workflow_model.maximum_force),
                "metadata": {"options": {"resources": {"num_machines": 1}}},
            }

            if optimisation == "cell lengths":
                inputs_geom["opt_cell_lengths"] = Bool(True)
            else:
                inputs_geom["opt_cell_fully"] = Bool(True)

            if dftd3:
                inputs_geom["calc_kwargs"] = Dict({"dispersion": True})

            geomoptCalc = CalculationFactory("mlip.opt")

        else: # must be single point
            inputs_geom = {
                "code": code,
                "model": mlip_model,
                "struct": structure,
                "device": Str(device),
                "metadata": {"options": {"resources": {"num_machines": 1}}},
            }
        
            if dftd3:
                inputs_geom["calc_kwargs"] = Dict({"dispersion": True})

            geomoptCalc = CalculationFactory("mlip.sp")

        supercell = str(self.model.workflow_model.supercell_size_x) + " " + str(self.model.workflow_model.supercell_size_y) + " " + str(self.model.workflow_model.supercell_size_z)

        inputs_phon = {
        "metadata": {"options": {"resources": {"num_machines": 1}}},
        "code": code,
        "model": mlip_model,
        "device": Str(device),
        "supercell": Str(supercell),
        "displacement": Float(0.01),
        "nqpoints": Int(51),
        "dos": Bool(True),
        "pdos": Bool(True),
        "bands": Bool(True),
        "no_hdf5": Bool(False),
        "symmetrize": Bool(False),
        }

        geomoptCalc = CalculationFactory("mlip.opt")
        phononCalc = CalculationFactory("mlip.ph")


        
        wg = WorkGraph("GeomOptGraph")

        gm_calc = wg.add_task(
        geomoptCalc,
        name="geomopt_calc",
        **inputs_geom
       )

        opt_struct = gm_calc.outputs.final_structure

        phononCalc = CalculationFactory("mlip.ph")

        ph_calc = wg.add_task(
        phononCalc,
        name="ph_calc",
        struct = opt_struct,
        **inputs_phon,
       )

        wg.outputs.results = wg.tasks.geomopt_calc.outputs.results_dict
        wg.outputs.results_file = wg.tasks.geomopt_calc.outputs.xyz_output

        wg.run()

        if wg.process.is_failed:
            print("WorkGraph failed")

        if wg.process.exit_status != 0:
            print(f"Failed with exit status {wg.process.exit_status}")

        self.node = wg.nodes[0]
        
        #force constants are always needed for scattering calculations, so we will always save them
        with wg.nodes[4].outputs['force_constants'].value.open(mode='rb') as source:
            with open('force_constants.hdf5', mode='wb') as target:
                shutil.copyfileobj(source, target)

        with wg.nodes[4].outputs['band_structure'].value.open(mode='rb') as source:
            with open('bands.yml.xz', mode='wb') as target:
                shutil.copyfileobj(source, target)
        
        with lzma.open('bands.yml.xz', mode="rt", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.model.results_model.final_structure = StructureData(ase=self.dict_to_ase_atoms(wg.outputs.results.value.get_dict()))
        self.model.results_model.phonon_band_structure = self._clean_band_structure_data(data)
        self.model.results_model.phonon_dos = wg.tasks.ph_calc.outputs.dos.value.get_content()
        self.model.results_model.phonon_pdos = wg.tasks.ph_calc.outputs.pdos.value.get_content()
        self.model.results_model.phonopy = wg.tasks.ph_calc.outputs.results_dict.value.get_dict()
        return
    
    def _phonopy_to_bandsplot(self, phonopy_data):
        """Convert phonopy band structure data to a format suitable for the BandsPlotWidget."""
        phonon_segments = phonopy_data.get(
            "phonon",
            phonopy_data.get("band_structure", phonopy_data.get("segments", [])),
        )

        kpoints = []
        band_branches = []
        segment_lengths = []
        segment_labels = []

        for segment in phonon_segments:
            q_points = segment.get(
                "q-position",
                segment.get("q-point", segment.get("q-points", segment.get("qpoints", []))),
            )
            if isinstance(q_points, dict):
                q_points = [q_points]

            q_coords = []
            for qpt in q_points:
                if isinstance(qpt, dict):
                    q_coords.append(
                        qpt.get("coordinates")
                        or qpt.get("q-position")
                        or [v for v in qpt.values() if isinstance(v, (int, float))]
                    )
                else:
                    q_coords.append(qpt)

            q_coords = [list(map(float, coords)) for coords in q_coords]
            kpoints.extend(q_coords)
            segment_lengths.append(len(q_coords))

            band_data = segment.get("band", segment.get("bands", []))
            if isinstance(band_data, dict):
                band_data = [band_data]

            if band_data and isinstance(band_data[0], dict) and "frequency" in band_data[0]:
                # Phonopy often stores one branch per segment as a list of dicts
                branch = [float(entry["frequency"]) for entry in band_data]
                band_branches.append(branch)
            elif band_data and isinstance(band_data[0], (list, tuple, np.ndarray)):
                band_branches.extend([list(map(float, branch)) for branch in band_data])
            elif band_data:
                band_branches.append([float(value) for value in band_data])

            if "label" in segment:
                segment_labels.append((len(kpoints) - len(q_coords), segment["label"]))

        if not kpoints or not band_branches:
            raise ValueError("No phonopy band structure data found in input")

        kpoints = np.asarray(kpoints, dtype=float).reshape(-1, 3)
        frequencies = np.asarray(band_branches, dtype=float)
        if frequencies.ndim == 2 and frequencies.shape[0] == len(kpoints):
            frequencies = frequencies.T

        distances = np.concatenate(
            ([0.0], np.linalg.norm(np.diff(kpoints, axis=0), axis=1).cumsum())
        )

        labels = []
        if segment_labels:
            for idx, label in segment_labels:
                if idx < len(distances):
                    labels.append([float(distances[idx]), label])
        elif "labels" in phonopy_data and "segment_nqpoint" in phonopy_data:
            offset = 0
            for pair, nq in zip(phonopy_data["labels"], phonopy_data["segment_nqpoint"]):
                labels.append([float(distances[offset]), pair[0]])
                labels.append([float(distances[offset + nq - 1]), pair[1]])
                offset += nq

        return {
            "bands": frequencies.T.tolist(),
            "kpoints": distances.tolist(),
            "labels": labels,
        }
    
    def _clean_band_structure_data(self, data) -> BandsData:
        

        frequencies = []
        kpoints = []
        labels = []

        def clean_label(label: str) -> str:
            """Remove LaTeX math mode delimiters and backslashes."""
            if not label:
                return label
            return label.replace("$", "").replace("\\", "").replace("mathrm{", "").replace("}", "")

        for i, segment in enumerate(data['phonon']):
            for qpt in segment['q-position']:
                kpoints.append(qpt)
            band_freqs = [band['frequency'] for band in segment['band']]
            frequencies.append(band_freqs)

            # Extract label if present for this specific q-point
            if "label" in segment:
                labels.append((i, clean_label(segment["label"])))

        kpoints = np.array(kpoints)
        kpoints = np.reshape(kpoints, (-1, 3))  # Ensure shape is (n_kpoints, 3)
        frequencies = np.array(frequencies)

        kpoints_data = KpointsData()
        kpoints_data.set_kpoints(kpoints)

        # Handle top-level labels if no labels were found in the individual points (Phonopy format)
        if not labels and "labels" in data and "segment_nqpoint" in data:
            curr_idx = 0
            for seg_labels, nq in zip(data["labels"], data["segment_nqpoint"]):
                labels.append((curr_idx, clean_label(seg_labels[0])))
                curr_idx += nq
                labels.append((curr_idx - 1, clean_label(seg_labels[1])))
            # Deduplicate labels at segment boundaries and sort by index
            labels = sorted(list(set(labels)))

        bands_data = BandsData()
        bands_data.set_kpointsdata(kpoints_data)
        bands_data.set_bands(frequencies)
        if labels:
            bands_data.labels = labels

        return bands_data
    
    def dict_to_ase_atoms(self, data: dict) -> Atoms:
        atoms = Atoms(
            numbers=np.asarray(data["numbers"], dtype=int),
            positions=np.asarray(data["positions"], dtype=float),
            cell=np.asarray(data["cell"], dtype=float),
            pbc=tuple(data["pbc"]),
        )

        if "masses" in data:
            atoms.set_masses(np.asarray(data["masses"], dtype=float))

        if "info" in data:
            atoms.info.update(data["info"])

        if "mace_forces" in data:
            atoms.arrays["mace_forces"] = np.asarray(data["mace_forces"], dtype=float)

        return atoms
