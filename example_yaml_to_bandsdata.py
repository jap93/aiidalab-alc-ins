"""
Quick example script showing how to use the YAML to BandsData converter.

This script demonstrates the most common use cases for converting
band structure data from YAML to AiiDA BandsData format.
"""

from pathlib import Path

from yaml_to_bandsdata import create_bandsdata_from_yaml, parse_yaml_bands


# Example 1: Parse YAML and get raw arrays
def example_parse_yaml():
    """Parse YAML file and extract k-points and frequencies."""
    yaml_file = Path("~/aiida_run/cb/ce/32d6-f70e-4459-bc04-443906df85e3/bands_data.yml").expanduser()

    if yaml_file.exists():
        kpoints, frequencies, labels = parse_yaml_bands(yaml_file)
        print(f"K-points shape: {kpoints.shape}")
        print(f"Frequencies shape: {frequencies.shape}")
        return kpoints, frequencies, labels


# Example 2: Create BandsData without storing
def example_create_bandsdata():
    """Create AiiDA BandsData from YAML file (without storing)."""
    yaml_file = Path("~/aiida_run/cb/ce/32d6-f70e-4459-bc04-443906df85e3/bands_data.yml").expanduser()

    if yaml_file.exists():
        bands_data = create_bandsdata_from_yaml(yaml_file, reciprocal=False)
        print(f"Created BandsData with {bands_data.get_number_of_kpoints()} k-points")
        print(f"                      {bands_data.get_number_of_bands()} bands")
        return bands_data


# Example 3: Create and store BandsData
def example_create_and_store():
    """Create AiiDA BandsData and store in database."""
    yaml_file = Path("~/aiida_run/cb/ce/32d6-f70e-4459-bc04-443906df85e3/bands_data.yml").expanduser()

    if yaml_file.exists():
        bands_data = create_bandsdata_from_yaml(yaml_file)
        bands_data.store()
        print(f"Stored BandsData with PK: {bands_data.pk}")
        return bands_data


# Example 4: With structure attachment (if you have a structure)
def example_with_structure():
    """Create BandsData and attach to a structure."""
    from aiida.orm import load_node

    yaml_file = Path("~/aiida_run/cb/ce/32d6-f70e-4459-bc04-443906df85e3/bands_data.yml").expanduser()
    # Replace 123 with your actual StructureData PK
    structure_pk = 123

    if yaml_file.exists():
        try:
            structure = load_node(structure_pk)
            bands_data = create_bandsdata_from_yaml(
                yaml_file,
                structure_node=structure,
                reciprocal=True,  # Often band structures are in reciprocal space
            )
            bands_data.store()
            print(f"Stored BandsData with structure, PK: {bands_data.pk}")
            return bands_data
        except Exception as e:
            print(f"Could not load structure with PK {structure_pk}: {e}")


# Example 5: Using the command-line interface
def example_cli():
    """
    Command-line usage examples:

    # Parse and print info
    python yaml_to_bandsdata.py ~/aiida_run/cb/ce/32d6-f70e-4459-bc04-443906df85e3/bands_data.yml

    # Parse with auto-format detection
    python yaml_to_bandsdata.py bands_data.yml --format auto

    # Parse as phonopy format
    python yaml_to_bandsdata.py bands_data.yml --format phonopy

    # Parse as simple format with reciprocal k-points
    python yaml_to_bandsdata.py bands_data.yml --format simple --reciprocal

    # Parse and store in AiiDA database
    python yaml_to_bandsdata.py bands_data.yml --store
    """
    pass


if __name__ == "__main__":
    import sys

    print("YAML to BandsData Converter - Example Scripts")
    print("=" * 50)

    # Try to parse and create BandsData
    try:
        print("\nAttempting to create BandsData...")
        bands_data = example_create_bandsdata()
        print("SUCCESS!")
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        print("The YAML file doesn't exist yet. Update the path and try again.")
    except Exception as e:
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check if the YAML file exists at the specified path")
        print("2. Ensure the file format is one of: phonopy, simple, or json")
        print("3. Check the file structure matches the expected format")
