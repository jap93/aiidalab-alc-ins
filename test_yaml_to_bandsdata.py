#!/usr/bin/env python3
"""
Test script for YAML to BandsData converter.

This script demonstrates the converter functionality and can create
sample YAML files for testing purposes.
"""

import json
from pathlib import Path

import numpy as np
import yaml


def create_sample_yaml_phonopy(output_file: str | Path = "sample_bands_phonopy.yml"):
    """
    Create a sample Phonopy-format YAML file for testing.

    Parameters
    ----------
    output_file : str | Path
        Output file path.
    """
    # Create sample data
    n_kpoints = 10
    n_bands = 3
    kpoints = np.linspace([0, 0, 0], [0.5, 0.5, 0.5], n_kpoints)
    frequencies = np.random.rand(n_kpoints, n_bands) * 10

    # Create phonopy format
    data = {
        "phonon": [
            {
                "q-point": [
                    {"coordinates": list(kpt), "q-position": list(kpt)}
                    for kpt in kpoints
                ],
                "band": [
                    {"frequency": float(freq), "q-position": list(kpts)}
                    for kpts, freq_row in zip(kpoints, frequencies)
                    for freq in freq_row
                ],
            }
        ]
    }

    with open(output_file, "w") as f:
        yaml.dump(data, f)

    print(f"Created sample Phonopy YAML: {output_file}")
    return output_file


def create_sample_yaml_simple(output_file: str | Path = "sample_bands_simple.yml"):
    """
    Create a sample simple-format YAML file for testing.

    Parameters
    ----------
    output_file : str | Path
        Output file path.
    """
    n_kpoints = 10
    n_bands = 3
    kpoints = np.linspace([0, 0, 0], [0.5, 0.5, 0.5], n_kpoints).tolist()
    bands = np.random.rand(n_kpoints, n_bands).tolist()
    labels = ["GAMMA", "X", "Y", "Z", "A", "B", "C", "D", "E", "F"]

    data = {
        "kpoints": kpoints,
        "bands": bands,
        "labels": labels[:n_kpoints],
    }

    with open(output_file, "w") as f:
        yaml.dump(data, f)

    print(f"Created sample simple YAML: {output_file}")
    return output_file


def create_sample_json(output_file: str | Path = "sample_bands.json"):
    """
    Create a sample JSON band structure file for testing.

    Parameters
    ----------
    output_file : str | Path
        Output file path.
    """
    n_kpoints_per_segment = 5
    n_bands = 3

    # Create sample data with multiple segments
    paths = []
    for i, (start, end) in enumerate([("GAMMA", "X"), ("X", "L"), ("L", "GAMMA")]):
        energies = np.random.rand(n_kpoints_per_segment, n_bands).tolist()
        paths.append(
            {
                "from": start,
                "to": end,
                "length": n_kpoints_per_segment,
                "values": energies,
            }
        )

    data = {
        "label": "Silicon band structure",
        "path": [["GAMMA", "X"], ["X", "L"], ["L", "GAMMA"]],
        "paths": paths,
    }

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Created sample JSON: {output_file}")
    return output_file


def test_converter(yaml_file: str | Path):
    """
    Test the converter on a YAML file.

    Parameters
    ----------
    yaml_file : str | Path
        Path to the YAML file to test.
    """
    try:
        from yaml_to_bandsdata import create_bandsdata_from_yaml, parse_yaml_bands

        print(f"\nTesting converter on: {yaml_file}")
        print("-" * 50)

        # Test parsing
        try:
            kpoints, frequencies, labels = parse_yaml_bands(yaml_file)
            print(f"✓ Successfully parsed YAML file")
            print(f"  K-points shape: {kpoints.shape}")
            print(f"  Frequencies shape: {frequencies.shape}")
            if labels:
                print(f"  Labels: {labels}")
        except Exception as e:
            print(f"✗ Failed to parse: {e}")
            return False

        # Test BandsData creation
        try:
            bands_data = create_bandsdata_from_yaml(yaml_file)
            print(f"✓ Successfully created BandsData")
            print(f"  Number of k-points: {bands_data.get_number_of_kpoints()}")
            print(f"  Number of bands: {bands_data.get_number_of_bands()}")
        except Exception as e:
            print(f"✗ Failed to create BandsData: {e}")
            return False

        print("✓ All tests passed!")
        return True

    except ImportError as e:
        print(f"✗ Could not import converter: {e}")
        print("Make sure yaml_to_bandsdata.py is in the same directory")
        return False


def main():
    """Run tests and demonstrations."""
    import sys

    print("=" * 60)
    print("YAML to BandsData Converter - Test Suite")
    print("=" * 60)

    # Create sample files
    print("\nCreating sample test files...")
    print("-" * 60)
    
    sample_phonopy = create_sample_yaml_phonopy()
    sample_simple = create_sample_yaml_simple()
    sample_json = create_sample_json()

    # Test each format
    print("\nTesting converter...")
    print("=" * 60)

    results = {
        "Phonopy format": test_converter(sample_phonopy),
        "Simple format": test_converter(sample_simple),
        "JSON format": test_converter(sample_json),
    }

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for format_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {format_name}")

    all_passed = all(results.values())
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    import sys

    exit_code = main()
    sys.exit(exit_code)
