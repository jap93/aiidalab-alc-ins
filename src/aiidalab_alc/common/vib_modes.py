"""Vibrational modes viewer widget."""

from collections.abc import Generator, Iterable, Sequence
from functools import cached_property
from itertools import groupby
from lzma import LZMAFile
from typing import TypedDict, cast

import ipywidgets as ipw
import numpy as np
import plotly.graph_objects as go
import yaml
from aiida.orm import BandsData, KpointsData, SinglefileData
from numpy.typing import NDArray
from typing_extensions import NotRequired, Self

_PathDict = TypedDict(
    "_PathDict",
    {
        "length": int,
        "from": str,
        "to": str,
        "values": list,
        "x": float,
        "two_band_types": bool,
    },
)


class _BandPlotData(TypedDict):
    x: list[float]
    y: NDArray[np.floating]
    band_type_idx: NDArray
    raw_labels: list[tuple[str, str]]
    labels: list[tuple[int, str]]
    path: list[tuple[str, str]]
    paths: list[_PathDict]


class _PhonopyBand(TypedDict, total=False):
    frequency: float
    eigenvector: list[
        tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    ]


_PhonopySegment = TypedDict(
    "_PhonopySegment",
    {
        "q-position": Sequence[tuple[float, float, float]],
        "band": Sequence[_PhonopyBand],
        "distance": float,
        "label": NotRequired[str],
    },
    total=False,
)


class _AtomData(TypedDict):
    symbol: str
    coordinates: tuple[float, float, float]
    mass: float


class _PhonopyDict(TypedDict, total=False):
    nqpoint: int
    npath: int
    natom: int
    segment_nqpoint: list[int]
    phonon: list[_PhonopySegment]
    labels: NotRequired[Sequence[str]]
    segment_nqpoint: NotRequired[Sequence[int]]
    reciprocal_lattice: NotRequired[
        tuple[
            tuple[float, float, float],
            tuple[float, float, float],
            tuple[float, float, float],
        ]
    ]
    lattice: NotRequired[
        tuple[
            tuple[float, float, float],
            tuple[float, float, float],
            tuple[float, float, float],
        ]
    ]
    supercell_matrix: NotRequired[
        tuple[
            tuple[float, float, float],
            tuple[float, float, float],
            tuple[float, float, float],
        ]
    ]
    points: list[_AtomData]


class VibrationalModesViewWidget(ipw.VBox):
    """Custom widget to display vibrational modes."""

    def __init__(self, node: BandsData, debug=False, **kwargs) -> None:
        """VibrationalModesViewWidget Constructor.

        Parameters
        ----------
        array : ArrayData
            The AiiDA ArrayData object to display.
        """
        self.debug = debug
        self.debug_output = ipw.Output()
        self.figure = go.FigureWidget()
        super().__init__([self.figure], **kwargs)

        if self.debug:
            self.children = [self.figure, self.debug_output]

        self.bands = node
        self.plot()

    @cached_property
    def bandplot_data(self) -> _BandPlotData:
        """Get the data from the BandsData."""
        return self.bands._get_bandplot_data(cartesian=True)

    def plot(self) -> None:
        """Plot the bands data."""
        bpd = self.bandplot_data

        with self.figure.batch_update():
            for line in bpd["y"].T:
                self.figure.add_scatter(
                    x=bpd["x"],
                    y=line,
                    mode="lines",
                    line={
                        "color": "black",
                    },
                )

        self.figure.add_hline(0)
        for pos, _ in bpd["labels"]:
            self.figure.add_vline(pos)

        labels = dict(self._compress_labels(bpd["labels"]))
        self.figure.update_layout(
            template="plotly_white",
            yaxis_title="Dispersion (meV)",
            showlegend=False,
            margin={"l": 20, "r": 20, "t": 20, "b": 10},
            xaxis={
                "tickmode": "array",
                "tickvals": list(labels.keys()),
                "ticktext": list(labels.values()),
            },
        )

    def _compress_labels(
        self,
        labels: Iterable[tuple[float, str]],
    ) -> Generator[tuple[float, str]]:
        for key, grp in groupby(labels, lambda x: round(x[0], 3)):
            label = dict.fromkeys((lab for _, lab in grp), None)

            if len(label) > 2:
                raise ValueError("0 width position in labels.")
            yield key, " | ".join(label)

    @classmethod
    def from_phonopy_yaml(cls, node: SinglefileData, **kwargs) -> Self:
        """Construct a VibrationalModesViewWidget from a phonopy file.

        Parameters
        ----------
        node : SinglefileData
            Phonopy file.

        Returns
        -------
        Self
            Constructed Bands view
        """
        with node.open(None, "rb") as file, LZMAFile(file, "r") as decompress:
            raw = cast("_PhonopyDict", yaml.safe_load(decompress))
        bands = cls._clean_phonopy_bs_yaml(raw)
        return cls(bands, **kwargs)

    @staticmethod
    def _clean_label(label: str) -> str:
        """Remove LaTeX math mode delimiters and backslashes.

        Returns
        -------
        str
            Sanitised string.
        """
        if not label:
            return label
        return (
            label.replace("\\", "")
            .replace("$", "")
            .replace("mathrm{", "")
            .replace("}", "")
            .replace("Gamma", "Γ")
        )

    @staticmethod
    def _clean_phonopy_bs_yaml(data: _PhonopyDict) -> BandsData:

        clean = VibrationalModesViewWidget._clean_label

        frequencies = []
        kpoints = []
        labels = []

        for i, segment in enumerate(data["phonon"]):
            kpoints.extend(segment["q-position"])
            band_freqs = [band["frequency"] for band in segment["band"]]
            frequencies.append(band_freqs)

            # Extract label if present for this specific q-point
            if "label" in segment:
                labels.append((i, clean(segment["label"])))

        kpoints = np.array(kpoints).reshape((-1, 3))
        frequencies = np.array(frequencies)

        kpoints_data = KpointsData()
        kpoints_data.set_kpoints(kpoints)
        if lattice := data.get("lattice"):
            kpoints_data.set_cell(lattice)

        # Handle top-level labels if no labels were
        # found in the individual points (Phonopy format)
        if not labels and "labels" in data and "segment_nqpoint" in data:
            curr_idx = 0
            for seg_labels, nq in zip(
                data["labels"], data["segment_nqpoint"], strict=True
            ):
                labels.append((curr_idx, clean(seg_labels[0])))
                curr_idx += nq
                labels.append((curr_idx - 1, clean(seg_labels[1])))
            # Deduplicate labels at segment boundaries and sort by index
            labels = sorted(set(labels))

        bands_data = BandsData()
        bands_data.set_kpointsdata(kpoints_data)
        bands_data.set_bands(frequencies)
        if labels:
            bands_data.labels = labels

        return bands_data
