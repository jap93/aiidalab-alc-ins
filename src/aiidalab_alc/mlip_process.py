from __future__ import annotations

import io
from typing import TYPE_CHECKING

from ase import Atoms
import numpy as np
from pathlib import Path
import h5py
import yaml
import shutil
import logging


from aiida.orm import Dict, load_code


from aiida_mlip.data.model import ModelData
from aiida.orm import StructureData
from aiida.orm import load_code, load_node
from aiida.orm import Str, Float, Bool, Int, BandsData, KpointsData, XyData
from aiida.plugins import CalculationFactory
from aiida_workgraph import WorkGraph

from aiidalab_alc.resources import ComputationalResourcesModel
from aiidalab_alc.results import ResultsModel
from aiidalab_alc.data import DataStepModel
from aiidalab_alc.workflow import WorkflowCalculationModel

class MLIPProcess:
    """Class to handle a MLIP AiiDA process."""

    def __init__(self, data_model: DataStepModel, workflow_model: WorkflowCalculationModel, resource_model: ComputationalResourcesModel, results_model: ResultsModel):
            """Initialise the MLIP process wrapper."""
            self.data_model = data_model
            self.workflow_model = workflow_model
            self.resource_model = resource_model
            self.results_model = results_model
            self.node = None

    def validate_model(self) -> bool:
        """
        Validate the mlip application model.

        Parameters
        ----------
        model : MainAppModel
            The mlip application model to validate.

        Returns
        -------
        bool
            True if the model is valid, False otherwise.
        """

        if not self.data_model.has_structure:
            if not self.data_model.has_file:
                print("No structure provided.")
                return False

        if not self.workflow_model.force_field:
            print("No force field provided.")
            return False
        
        # Add more validation checks as needed
        return True


    def submit_process(self):
        """Submit the AiiDA process."""
        log_path = self.results_model.process_log 
        logging.basicConfig(filename=log_path, level=logging.INFO, force=True)
        logger = logging.getLogger(__name__)
        logger.info('Started MLIP:Process submission')
        if not self.validate_model():
            logger.info("Model validation failed.")
            return
        structure = self.data_model.structure
        code = load_code(self.resource_model.code_name)

        device = self.resource_model.device_name   

        model_file = self.workflow_model.force_field
        if not Path(model_file).exists():
            logger.info("model file does not exist: %s", model_file)
            print("model file does not exist", model_file)

        architecture = self.workflow_model.architecture
        mlip_model = ModelData.from_local(model_file, architecture=architecture)

        calculation_style = self.workflow_model.calc_style.lower()
        optimisation = self.workflow_model.optimisation.lower()

        dftd3 = self.workflow_model.use_dftd3

        logger.info("Starting to build inputs")
        if calculation_style == "geometry optimisation":
            inputs_geom = {
                "code": code,
                "model": mlip_model,
                "struct": structure,
                "device": Str(device),
                "fmax": Float(self.workflow_model.maximum_force),
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

        supercell = str(self.workflow_model.supercell_size_x) + " " + str(self.workflow_model.supercell_size_y) + " " + str(self.workflow_model.supercell_size_z)

        inputs_phon = {
        "metadata": {"options": {"resources": {"num_machines": 1}}},
        "code": code,
        "model": mlip_model,
        "device": Str(device),
        "supercell": Str(supercell),
        "displacement": Float(0.01),
        "n_qpoints": Int(51),
        "dos": Bool(True),
        "pdos": Bool(True),
        "bands": Bool(True),
        "no_hdf5": Bool(False),
        "symmetrize": Bool(False),
        }

        logger.info("Inputs built, starting WorkGraph")

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
        #print("phonon inputs", inputs_phon)

        ph_calc = wg.add_task(
        phononCalc,
        name="ph_calc",
        struct = opt_struct,
        **inputs_phon,
       )

        logger.info("WorkGraph built, running now")

        wg.outputs.results = wg.tasks.geomopt_calc.outputs.results_dict
        wg.outputs.results_file = wg.tasks.geomopt_calc.outputs.xyz_output

        wg.run()
        self.node = wg.process

        logger.info("WorkGraph run completed: %s", wg.process.exit_status)

        if wg.process.is_failed:
            logger.info("WorkGraph failed")

        if wg.process.exit_status != 0:
            logger.info("WorkGraph failed with exit status %s", wg.process.exit_status)
            print(f"Failed with exit status {wg.process.exit_status}")
            return wg.process.exit_status

        #force constants are always needed for scattering calculations, so we will always save them
        logger.info("Saving force constants and band structure to local files")
        with wg.tasks.ph_calc.outputs.force_constants.value.open(mode='rb') as source:
            with open('force_constants.hdf5', mode='wb') as target:
                shutil.copyfileobj(source, target)

        with wg.tasks.ph_calc.outputs.band_structure.value.open(mode='rb') as source:
            with open('aiida-auto_bands.hdf5', mode='wb') as target:
                shutil.copyfileobj(source, target)

        def read_hdf5_group(group):
            return {
                name: read_hdf5_group(item) if isinstance(item, h5py.Group) else item[()]
                for name, item in group.items()
            }

        with h5py.File("aiida-auto_bands.hdf5", "r") as bands_file:
            logger.info("Bands top-level keys from file: %s", list(bands_file.keys()))
            data = read_hdf5_group(bands_file)

        logger.info("data read from aiida-auto_bands.hdf5: ")

        logger.info("Saving results to ResultsModel")
        self.results_model.final_structure = StructureData(ase=self.dict_to_ase_atoms(wg.outputs.results.value.get_dict()))
        self.results_model.phonon_band_structure = self._clean_band_structure_data(data)
        self.results_model.phonon_dos = self._dos_to_xydata(
            wg.tasks.ph_calc.outputs.dos.value.get_content()
        )
        self.results_model.phonon_pdos = wg.tasks.ph_calc.outputs.pdos.value.get_content()
        self.results_model.phonopy = wg.tasks.ph_calc.outputs.results_dict.value.get_dict()

        logger.info("MLIP:Process submission completed successfully")
        
        return wg.process.exit_status
    
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
        """Convert phonopy HDF5 band data into an AiiDA BandsData node."""
        try:
            path = np.asarray(data["path"], dtype=float)
            frequencies = np.asarray(data["frequency"], dtype=float)
        except KeyError as exc:
            raise ValueError(
                f"Band structure HDF5 data is missing required dataset: {exc.args[0]}"
            ) from exc

        if path.ndim != 3 or path.shape[-1] != 3:
            raise ValueError(
                "Band structure path must have shape (nsegments, npoints, 3)"
            )
        if frequencies.ndim != 3 or frequencies.shape[:2] != path.shape[:2]:
            raise ValueError(
                "Band frequencies must have shape (nsegments, npoints, nbands)"
            )

        segment_nqpoint = np.asarray(
            data.get("segment_nqpoint", [path.shape[1]] * path.shape[0]),
            dtype=int,
        ).reshape(-1)
        if len(segment_nqpoint) != path.shape[0] or np.any(
            (segment_nqpoint <= 0) | (segment_nqpoint > path.shape[1])
        ):
            raise ValueError(
                "Segment point counts must fit the band structure path shape"
            )

        kpoints = np.concatenate(
            [segment[:count] for segment, count in zip(path, segment_nqpoint, strict=True)]
        )
        frequencies = np.concatenate(
            [
                segment[:count]
                for segment, count in zip(frequencies, segment_nqpoint, strict=True)
            ]
        )

        def clean_label(label) -> str:
            if isinstance(label, bytes):
                label = label.decode("utf-8").rstrip("\x00")
            return str(label).replace("$", "").replace("\\", "").replace(
                "mathrm{", ""
            ).replace("}", "").strip()

        labels = []
        if "label" in data:
            raw_labels = np.asarray(data["label"])
            if raw_labels.shape == (path.shape[0], 2):
                point_index = 0
                for segment_index, label_pair in enumerate(raw_labels):
                    start_label, end_label = map(clean_label, label_pair)
                    if start_label:
                        labels.append((point_index, start_label))
                    end_index = point_index + segment_nqpoint[segment_index] - 1
                    if end_label:
                        labels.append((end_index, end_label))
                    point_index += segment_nqpoint[segment_index]

        kpoints_data = KpointsData()
        kpoints_data.set_kpoints(kpoints)
        if "lattice" in data:
            kpoints_data.set_cell(np.asarray(data["lattice"], dtype=float))

        bands_data = BandsData()
        bands_data.set_kpointsdata(kpoints_data)
        bands_data.set_bands(frequencies)
        if labels:
            bands_data.labels = labels

        return bands_data

    def _dos_to_xydata(self, dos):
        """Convert MLIP phonon DOS text output to an AiiDA XyData node."""
        if isinstance(dos, bytes):
            dos = dos.decode()

        rows = []
        for line in io.StringIO(dos):
            values = line.split()
            if len(values) < 2:
                continue
            try:
                rows.append((float(values[0]), float(values[1])))
            except ValueError:
                continue

        if not rows:
            raise ValueError("DOS output does not contain numeric x/y data")

        data = np.asarray(rows, dtype=float)
        xydata = XyData()
        xydata.set_x(data[:, 0], "Energy", "eV")
        xydata.set_y(data[:, 1], "DOS", "1/eV")
        return xydata

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
