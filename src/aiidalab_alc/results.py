"""Module for defining widgets/models for viewing process progress and results."""
import io
import json
from pathlib import Path
from typing import cast
import numpy as np

import aiidalab_widgets_base as awb
from aiida import plugins
import ipywidgets as ipw
import traitlets as tl
from aiida.common.exceptions import NotExistent
from aiida.orm import (
    BandsData,
    NodeLinksManager,
    ProcessNode,
    StructureData,
    XyData,
    load_node,
)
from aiidalab_widgets_base.viewers import BandsDataViewer

#bool8 was depracated in numpy 1.24, but BandsDataViewer still uses it, so alias it to bool_ for compatibility
if np.__version__ >= "1.24":
    np.bool8 = np.bool

class ProcessModel(tl.HasTraits):
    """Model describing an AiiDA process."""

    process_uuid = tl.Unicode(None, allow_none=True)

    @property
    def process(self) -> ProcessNode | None:
        """Return the process node for the stored uuid."""
        if not self.process_uuid:
            return None
        try:
            return cast(ProcessNode, load_node(self.process_uuid))
        except NotExistent:
            return None

    @property
    def has_process(self) -> bool:
        """Return true if a valid process node is associated with the uuid."""
        return self.process is not None

    @property
    def inputs(self) -> NodeLinksManager | list:
        """Return the inputs for the process."""
        return self.process.inputs if self.has_process else []

    @property
    def outputs(self) -> NodeLinksManager | list:
        """Return the outputs for the process."""
        return self.process.outputs if self.has_process else []


class ResultsModel(ProcessModel):
    """MVC results step model."""

    blocked = tl.Bool(False)
    final_structure = tl.Instance(StructureData, allow_none=True)
    phonon_band_structure = tl.Instance(BandsData, allow_none=True)
    phonon_dos = tl.Unicode("", allow_none=True)
    phonon_pdos = tl.Unicode("", allow_none=True)

class ResultsWizardStep(ipw.VBox, awb.WizardAppWidgetStep):
    """Wizard for viewing process progress and results."""

    def __init__(self, model: ResultsModel, **kwargs):
        """
        ResultsWizardStep constructor.

        Parameters
        ----------
        model : ResultsModel
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

    def load_json(self, filename: str):
        """Helper to load JSON data from a file relative to this script."""
        # Try to find the file relative to the package directory first
        base_path = Path(__file__).parent
        filepath = base_path / filename
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def render(self) -> None:
        """Render the wizard's content."""
        if self.rendered:
            return
        self._update_view()
        self.rendered = True

    def _get_data_from_node(self):
        """Try to extract bands and dos data from the AiiDA process node."""
        bands_data = None
        dos_data = None

        if self.model.has_process:
            outputs = self.model.process.outputs
            # Look for BandsData in outputs
            for label in outputs:
                node = outputs[label]
                if isinstance(node, BandsData):
                    # In a real scenario, you'd convert BandsData to the widget's JSON format
                    # For now, we return None to fall back to the demo JSONs
                    pass
        return bands_data, dos_data

    def _update_view(self):

        if not self.model.process_uuid:
            self.children = [ipw.HTML("Waiting for calculation results...")]
            return

        # 1. Structure Panel
        structure_node = self.model.final_structure
        if structure_node:
            structure_vwr = awb.viewers.StructureDataViewer(structure=structure_node)
        else:
            structure_vwr = ipw.HTML("<p>No output structure found for this process.</p>")

        # 2. Phonon Dispersion Panel
        bands_node = self.model.phonon_band_structure
        dos_node = self.model.phonon_dos
        pdos_node = self.model.phonon_pdos
        dos = self._create_density_of_states_data(dos_node, pdos_node)

        if bands_node:
            phonon_vwr = BandsDataViewer(bands_node, units = "eV", downloadable=True)
        else:
            phonon_vwr = ipw.HTML("<p>No output phonon data found for this process.</p>")

        # Result tabs
        tabs = ipw.Tab(children=[structure_vwr, phonon_vwr])
        tabs.set_title(0, "Resulting Structure")
        tabs.set_title(1, "Phonon Dispersion")

        self.children = [
            ipw.HTML(f"<h4>Results for Process: {self.model.process_uuid}</h4>"),
            tabs,
        ]

    def _create_bands_data_json(self, bands_node: BandsData):
        """Convert AiiDA BandsData to a dictionary format for the plotting widget."""
        if not bands_node:
            return None
        
        # Get bands array. Shape: (kpoints, bands) or (spin, kpoints, bands)
        bands_array = bands_node.get_bands()

        # Handle 3D array for spin-polarized data (spin, kpoints, bands)
        if len(bands_array.shape) == 3:
            bands_array = bands_array[0]

        # Calculate x-axis values (cumulative distance between k-points)
        kpoints = bands_node.get_kpoints()
        if kpoints.ndim == 2 and kpoints.shape[1] == 3:
            diff = np.diff(kpoints, axis=0)
            dist = np.sqrt(np.sum(diff**2, axis=1))
            x_axis = np.concatenate(([0], np.cumsum(dist)))
        else:
            x_axis = kpoints[:, 0] if kpoints.ndim == 2 else np.arange(len(bands_array))

        # Extract labels in [position, label] format
        labels = []
        try:
            for idx, label in bands_node.labels:
                if idx < len(x_axis):
                    labels.append([float(x_axis[idx]), label])
        except (AttributeError, TypeError):
            pass

        return {
            "bands": bands_array.T.tolist(),
            "kpoints": x_axis.tolist(),
            "labels": labels,
        }
    def load_file(self, filename):
        with open(filename, 'r') as fhandle:
            return json.load(fhandle)    
        
    def _create_density_of_states_data(self, dos, pdos):
        
        #remove title at the top of dos and pdos
        dos = dos.replace("dos # Tetrahedron method", "")
        pdos = pdos.replace("pdos # Tetrahedron method", "")
        # Load the data from the string; genfromtxt ignores lines starting with '#'
        dos_data = np.genfromtxt(io.StringIO(dos))
        x_dos = dos_data[:, 0] 
        y_dos = dos_data[:, 1] 
        pdos_data = np.genfromtxt(io.StringIO(pdos))
        x_pdos = pdos_data[:, 0] 
        y_pdos = pdos_data[:, 1]
        #create json 
        json_data = {
            "dos": {"label": "Total DOS", "x": x_dos.tolist(), "y": y_dos.tolist()},
            "pdos": {"x": x_pdos.tolist(), "y": y_pdos.tolist()}
        }
        return json_data
    