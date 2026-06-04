# YAML to AiiDA BandsData Converter

A Python utility to convert band structure data from YAML/JSON files to AiiDA's BandsData format.

## Features

- **Multiple format support**: Automatically detects or accepts hints for:
  - Phonopy YAML format
  - Simple format (direct k-points and bands arrays)
  - JSON format (with paths and segments)
- **Flexible k-point handling**: Supports both Cartesian and reciprocal space k-points
- **AiiDA integration**: Creates proper AiiDA BandsData nodes ready for storage
- **Optional structure attachment**: Can attach a StructureData node to the BandsData
- **Command-line interface**: Use from terminal or import as a Python module

## Installation

The script requires:
- `aiida-core`
- `numpy`
- `pyyaml`

These are typically already installed in your AiiDA environment.

## Usage

### As a Python Module

#### Basic Usage

```python
from yaml_to_bandsdata import create_bandsdata_from_yaml

# Create BandsData from YAML file
bands_data = create_bandsdata_from_yaml("~/aiida_run/.../bands_data.yml")

# Store in AiiDA database
bands_data.store()
print(f"Stored with PK: {bands_data.pk}")
```

#### With Structure Node

```python
from aiida.orm import load_node
from yaml_to_bandsdata import create_bandsdata_from_yaml

structure = load_node(123)  # Load your structure by PK

bands_data = create_bandsdata_from_yaml(
    "bands_data.yml",
    structure_node=structure,
    reciprocal=True,  # If k-points are in reciprocal space
)
bands_data.store()
```

#### Parse Only (Without BandsData)

```python
from yaml_to_bandsdata import parse_yaml_bands

kpoints, frequencies, labels = parse_yaml_bands("bands_data.yml")
print(f"K-points shape: {kpoints.shape}")
print(f"Frequencies shape: {frequencies.shape}")
```

### From Command Line

#### Basic parsing (no storage)
```bash
python yaml_to_bandsdata.py ~/aiida_run/cb/ce/32d6-f70e-4459-bc04-443906df85e3/bands_data.yml
```

#### Auto-detect format
```bash
python yaml_to_bandsdata.py bands_data.yml --format auto
```

#### Specify format explicitly
```bash
python yaml_to_bandsdata.py bands_data.yml --format phonopy
```

#### With reciprocal space k-points
```bash
python yaml_to_bandsdata.py bands_data.yml --reciprocal
```

#### Parse and store in AiiDA database
```bash
python yaml_to_bandsdata.py bands_data.yml --store
```

## Supported YAML Formats

### 1. Phonopy Format

```yaml
phonon:
  - q-point:
      - coordinates: [0.0, 0.0, 0.0]
      - coordinates: [0.1, 0.0, 0.0]
    band:
      - frequency: 0.0
        q-position: [0.0, 0.0, 0.0]
      - frequency: 1.5
        q-position: [0.1, 0.0, 0.0]
```

### 2. Simple Format

```yaml
kpoints:
  - [0.0, 0.0, 0.0]
  - [0.1, 0.0, 0.0]
  - [0.2, 0.0, 0.0]
bands:
  - [0.0, 2.5, 5.0, ...]  # Band energies for k-point 1
  - [0.1, 2.4, 4.9, ...]  # Band energies for k-point 2
  - [0.2, 2.3, 4.8, ...]  # Band energies for k-point 3
labels:  # Optional
  - GAMMA
  - X
  - Y
```

### 3. JSON Format

```json
{
  "paths": [
    {
      "length": 10,
      "from": "GAMMA",
      "to": "X",
      "values": [[e1, e2, ...], [e1, e2, ...], ...]
    }
  ]
}
```

## API Reference

### `parse_yaml_bands(file_path, format_hint=None)`

Parse YAML/JSON file and extract k-points and band data.

**Parameters:**
- `file_path` (str or Path): Path to the YAML or JSON file
- `format_hint` (str, optional): 'phonopy', 'simple', 'json', or None for auto-detect

**Returns:**
- Tuple of (kpoints, frequencies, labels)
- `kpoints`: np.ndarray of shape (n_kpoints, 3)
- `frequencies`: np.ndarray of shape (n_kpoints, n_bands)
- `labels`: List of k-point labels or None

### `create_bandsdata_from_yaml(file_path, structure_node=None, format_hint=None, reciprocal=False)`

Create an AiiDA BandsData node from a YAML/JSON file.

**Parameters:**
- `file_path` (str or Path): Path to the YAML or JSON file
- `structure_node` (StructureData, optional): AiiDA StructureData to attach
- `format_hint` (str, optional): 'phonopy', 'simple', 'json', or None for auto-detect
- `reciprocal` (bool): Whether k-points are in reciprocal space (default: False)

**Returns:**
- `BandsData`: AiiDA BandsData node (not stored unless explicitly called)

## Examples

See `example_yaml_to_bandsdata.py` for more detailed examples.

## Troubleshooting

### File not found
- Ensure the file path is correct and file exists
- Use full or expanded paths (e.g., `~/path/to/file.yml`)

### Format not recognized
- The script tries to auto-detect format from structure
- If auto-detection fails, specify format with `--format` flag
- Check that your YAML file matches one of the supported formats

### K-points shape mismatch
- Ensure k-points array has shape (n_kpoints, 3)
- Frequencies array should have shape (n_kpoints, n_bands)
- The converter will transpose if needed

### AiiDA database errors
- Ensure you have a running AiiDA profile
- Check that the database is properly initialized
- Use `verdi database integrity detect-invalid-nodes` if issues persist

## Related Files

- `yaml_to_bandsdata.py`: Main converter module
- `example_yaml_to_bandsdata.py`: Example usage scripts
- `phon_2_band.py`: Similar conversion for phonopy output (reference)
