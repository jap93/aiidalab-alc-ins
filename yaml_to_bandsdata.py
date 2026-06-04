"""
Convert YAML band structure data to AiiDA BandsData format.

This script reads band structure data from a YAML file and converts it
to an AiiDA BandsData node, which can be stored in the AiiDA database.

Supports multiple YAML formats:
- Phonopy format
- Simple format with k-points and band energies
- JSON format (as backup)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
import yaml

from aiida.orm import BandsData, KpointsData


def load_yaml_or_json(file_path: str | Path) -> dict:
    """
    Load data from YAML or JSON file.

    Parameters
    ----------
    file_path : str | Path
        Path to the YAML or JSON file.

    Returns
    -------
    dict
        Parsed data from the file.

    Raises
    ------
    FileNotFoundError
        If file does not exist.
    ValueError
        If file format is not supported.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        if file_path.suffix.lower() in [".yml", ".yaml"]:
            with open(file_path, "r") as f:
                return yaml.safe_load(f)
        elif file_path.suffix.lower() == ".json":
            with open(file_path, "r") as f:
                return json.load(f)
        else:
            raise ValueError(
                f"Unsupported file format: {file_path.suffix}. "
                "Supported formats: .yml, .yaml, .json"
            )
    except Exception as e:
        raise ValueError(f"Error parsing file {file_path}: {str(e)}") from e


def extract_phonopy_format(data: dict) -> tuple[np.ndarray, np.ndarray, Optional[list]]:
    """
    Extract k-points and band frequencies from Phonopy YAML format.

    Parameters
    ----------
    data : dict
        Parsed YAML data in Phonopy format.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, Optional[list]]
        Tuple of (kpoints, frequencies, kpoint_labels).
    """
    frequencies_list = []
    kpoints_list = []
    labels = []

    if "phonon" in data:
        phonon_data = data["phonon"]
    elif "band_structure" in data:
        phonon_data = data["band_structure"]
    else:
        phonon_data = data.get("segments", [])

    for segment in phonon_data:
        # Extract q-points
        q_points = segment.get("q-point") or segment.get("q-points") or segment.get("qpt") or []
        if isinstance(q_points, dict):
            q_points = [q_points]
        
        for qpt_data in q_points:
            if isinstance(qpt_data, dict):
                if "coordinates" in qpt_data:
                    kpoints_list.append(qpt_data["coordinates"])
                elif "q-position" in qpt_data:
                    kpoints_list.append(qpt_data["q-position"])
            else:
                kpoints_list.append(qpt_data)

        # Extract band frequencies
        band_data = segment.get("band") or segment.get("bands")
        if band_data:
            band_freqs = []
            for band in band_data:
                if isinstance(band, dict):
                    if "frequency" in band:
                        band_freqs.append(band["frequency"])
                    elif "frequencies" in band:
                        band_freqs.append(band["frequencies"])
                else:
                    band_freqs.append(band)
            if band_freqs:
                frequencies_list.append(band_freqs)

    if not kpoints_list or not frequencies_list:
        raise ValueError("Could not extract k-points or band frequencies from YAML")

    # Reshape k-points to (N, 3) to accommodate various input structures
    kpoints = np.array(kpoints_list, dtype=float).reshape(-1, 3)
    frequencies = np.array(frequencies_list, dtype=float)

    # Ensure frequencies shape is (n_kpoints, n_bands)
    if (frequencies.ndim == 2 and frequencies.shape[0] != kpoints.shape[0] 
        and frequencies.shape[1] == kpoints.shape[0]):
        frequencies = frequencies.T

    return kpoints, frequencies, labels if labels else None


def extract_simple_format(data: dict) -> tuple[np.ndarray, np.ndarray, Optional[list]]:
    """
    Extract k-points and band frequencies from simple format.

    Expected format:
    {
        'kpoints': [[x, y, z], ...],
        'bands': [[e1, e2, ...], ...],
        'labels': ['GAMMA', 'X', ...]  # optional
    }

    Parameters
    ----------
    data : dict
        Parsed data in simple format.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, Optional[list]]
        Tuple of (kpoints, frequencies, kpoint_labels).
    """
    kpoints = np.array(data["kpoints"], dtype=float).reshape(-1, 3)
    frequencies = np.array(data["bands"], dtype=float)
    labels = data.get("labels")

    # Ensure frequencies shape is (n_kpoints, n_bands)
    if (frequencies.ndim == 2 and frequencies.shape[0] != kpoints.shape[0] 
        and frequencies.shape[1] == kpoints.shape[0]):
        frequencies = frequencies.T

    return kpoints, frequencies, labels


def extract_json_format(data: dict) -> tuple[np.ndarray, np.ndarray, Optional[list]]:
    """
    Extract k-points and band frequencies from JSON format.

    Expected format: band structure with 'paths' containing segments
    with k-point coordinates and energies.

    Parameters
    ----------
    data : dict
        Parsed JSON data.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, Optional[list]]
        Tuple of (kpoints, frequencies, kpoint_labels).
    """
    kpoints_list = []
    frequencies_list = []
    labels = []

    if "paths" in data:
        paths = data["paths"]
    else:
        paths = []

    for path in paths:
        if "values" in path:
            # Each value array is the band structure for one k-point
            frequencies_list.extend(path["values"])

    if "kpoints" in data:
        kpoints_list = data["kpoints"]
    else:
        # If no explicit kpoints, generate from path info
        n_kpoints = sum(path.get("length", len(path["values"])) for path in paths)
        kpoints_list = np.linspace(0, 1, n_kpoints)
        kpoints_list = np.column_stack([kpoints_list, np.zeros_like(kpoints_list), np.zeros_like(kpoints_list)])

    kpoints = np.array(kpoints_list, dtype=float).reshape(-1, 3)
    frequencies = np.array(frequencies_list, dtype=float)

    return kpoints, frequencies, labels if labels else None


def parse_yaml_bands(
    file_path: str | Path,
    format_hint: Optional[str] = None,
) -> tuple[np.ndarray, np.ndarray, Optional[list]]:
    """
    Parse YAML/JSON file and extract k-points and band data.

    Parameters
    ----------
    file_path : str | Path
        Path to the YAML or JSON file.
    format_hint : Optional[str]
        Hint about data format: 'phonopy', 'simple', 'json', or None for auto-detect.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, Optional[list]]
        Tuple of (kpoints, frequencies, kpoint_labels).

    Raises
    ------
    FileNotFoundError
        If file does not exist.
    ValueError
        If data format is not recognized.
    """
    data = load_yaml_or_json(file_path)

    # Auto-detect format if not provided
    if format_hint is None:
        if "phonon" in data or "band_structure" in data or "segments" in data:
            format_hint = "phonopy"
        elif "kpoints" in data and "bands" in data:
            format_hint = "simple"
        elif "paths" in data:
            format_hint = "json"
        else:
            format_hint = "phonopy"  # Default to phonopy format

    if format_hint == "phonopy":
        return extract_phonopy_format(data)
    elif format_hint == "simple":
        return extract_simple_format(data)
    elif format_hint == "json":
        return extract_json_format(data)
    else:
        raise ValueError(f"Unknown format: {format_hint}")


def create_bandsdata_from_yaml(
    file_path: str | Path,
    structure_node: Optional[object] = None,
    format_hint: Optional[str] = None,
    reciprocal: bool = False,
) -> BandsData:
    """
    Create an AiiDA BandsData node from a YAML/JSON file.

    Parameters
    ----------
    file_path : str | Path
        Path to the YAML or JSON file containing band structure data.
    structure_node : Optional[object]
        Optional AiiDA StructureData node to attach to the BandsData.
        If not provided, no structure will be attached.
    format_hint : Optional[str]
        Hint about data format: 'phonopy', 'simple', 'json', or None for auto-detect.
    reciprocal : bool
        Whether the k-points are in reciprocal space (default: False).

    Returns
    -------
    BandsData
        AiiDA BandsData node with the parsed band structure.

    Raises
    ------
    FileNotFoundError
        If file does not exist.
    ValueError
        If data format is not recognized or data extraction fails.
    """
    # Parse YAML file
    kpoints, frequencies, labels = parse_yaml_bands(file_path, format_hint)

    print(f"Loaded band structure data from {file_path}")
    print(f"  K-points shape: {kpoints.shape}")
    print(f"  Frequencies shape: {frequencies.shape}")

    # Create KpointsData
    kpoints_data = KpointsData()
    kpoints_data.set_kpoints(kpoints, cartesian=not reciprocal)

    # Add labels if available
    if labels:
        for i, label in enumerate(labels):
            kpoints_data.labels.append((i, label))

    # Create BandsData
    bands_data = BandsData()
    bands_data.set_kpointsdata(kpoints_data)
    bands_data.set_bands(frequencies)

    # Attach structure if provided
    if structure_node is not None:
        bands_data.set_structure(structure_node)

    return bands_data


def main():
    """
    Example usage: read YAML file and create BandsData.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert YAML band structure data to AiiDA BandsData"
    )
    parser.add_argument(
        "yaml_file",
        help="Path to the YAML or JSON file with band structure data",
    )
    parser.add_argument(
        "--format",
        choices=["phonopy", "simple", "json", "auto"],
        default="auto",
        help="Format of the input file (default: auto-detect)",
    )
    parser.add_argument(
        "--reciprocal",
        action="store_true",
        help="K-points are in reciprocal space",
    )
    parser.add_argument(
        "--store",
        action="store_true",
        help="Store the BandsData node in the AiiDA database",
    )

    args = parser.parse_args()

    yaml_file = Path(args.yaml_file).expanduser()
    format_hint = args.format if args.format != "auto" else None

    try:
        # Create BandsData from YAML
        bands_data = create_bandsdata_from_yaml(
            yaml_file,
            format_hint=format_hint,
            reciprocal=args.reciprocal,
        )

        print(f"\nSuccessfully created BandsData node")
        print(f"  Number of k-points: {bands_data.get_number_of_kpoints()}")
        print(f"  Number of bands: {bands_data.get_number_of_bands()}")

        if args.store:
            bands_data.store()
            print(f"  Stored in AiiDA database with PK: {bands_data.pk}")
        else:
            print("  (Not stored in database - use --store to save)")

        return bands_data

    except Exception as e:
        print(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
