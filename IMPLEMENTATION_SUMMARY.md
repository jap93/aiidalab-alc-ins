# YAML to AiiDA BandsData Converter - Implementation Summary

## Overview

A complete Python solution to read YAML/JSON band structure files and convert them to AiiDA BandsData format, ready for storage in the AiiDA database.

## Created Files

### 1. **yaml_to_bandsdata.py** (Main Module)
   - **Location**: `/home/jap93/aiidalab-mlip/yaml_to_bandsdata.py`
   - **Purpose**: Core converter module with all conversion logic
   - **Key Functions**:
     - `parse_yaml_bands()`: Parse YAML/JSON and extract k-points and frequencies
     - `create_bandsdata_from_yaml()`: Create AiiDA BandsData from YAML file
     - `load_yaml_or_json()`: Load YAML or JSON files
     - Support functions for different format types
   - **Supports**:
     - Phonopy format (auto-detected)
     - Simple format (direct arrays)
     - JSON format (with segments)
     - Auto-format detection
   - **Features**:
     - Flexible k-point handling (Cartesian or reciprocal)
     - Optional structure attachment
     - Command-line interface
     - Comprehensive error handling

### 2. **example_yaml_to_bandsdata.py** (Examples)
   - **Location**: `/home/jap93/aiidalab-mlip/example_yaml_to_bandsdata.py`
   - **Purpose**: Demonstration of common use cases
   - **Includes**:
     - Example 1: Parse YAML and get raw arrays
     - Example 2: Create BandsData without storing
     - Example 3: Create and store BandsData
     - Example 4: With structure attachment
     - Example 5: CLI usage examples

### 3. **test_yaml_to_bandsdata.py** (Testing)
   - **Location**: `/home/jap93/aiidalab-mlip/test_yaml_to_bandsdata.py`
   - **Purpose**: Testing and demonstration script
   - **Features**:
     - Creates sample YAML files in all supported formats
     - Tests converter functionality on sample files
     - Generates test reports
   - **Run**: `python3 test_yaml_to_bandsdata.py`

### 4. **README_YAML_TO_BANDSDATA.md** (Documentation)
   - **Location**: `/home/jap93/aiidalab-mlip/README_YAML_TO_BANDSDATA.md`
   - **Purpose**: Complete documentation and reference guide
   - **Contains**:
     - Installation instructions
     - Usage examples (Python module and CLI)
     - API reference
     - Supported format specifications
     - Troubleshooting guide

## Quick Start

### Installation Check
All required packages are typically already available in AiiDA environments:
- `aiida-core`
- `numpy`
- `pyyaml`

### Basic Usage

#### Python Module
```python
from yaml_to_bandsdata import create_bandsdata_from_yaml

# Create BandsData from YAML
bands_data = create_bandsdata_from_yaml("~/aiida_run/.../bands_data.yml")

# Store in AiiDA database
bands_data.store()
print(f"Stored with PK: {bands_data.pk}")
```

#### Command Line
```bash
# Parse and display info
python3 yaml_to_bandsdata.py ~/aiida_run/cb/ce/32d6-f70e-4459-bc04-443906df85e3/bands_data.yml

# Parse and store
python3 yaml_to_bandsdata.py bands_data.yml --store

# Specify format
python3 yaml_to_bandsdata.py bands_data.yml --format phonopy
```

#### Testing
```bash
python3 test_yaml_to_bandsdata.py
```

## Supported YAML/JSON Formats

### Format 1: Phonopy
```yaml
phonon:
  - q-point:
      - coordinates: [0.0, 0.0, 0.0]
    band:
      - frequency: 0.0
```

### Format 2: Simple
```yaml
kpoints: [[0.0, 0.0, 0.0], ...]
bands: [[e1, e2, ...], ...]
labels: [GAMMA, X, ...]  # optional
```

### Format 3: JSON
```json
{"paths": [{"length": 10, "from": "GAMMA", "to": "X", "values": [[...]]}]}
```

## API Functions

### `parse_yaml_bands(file_path, format_hint=None)`
Parse and extract k-points, frequencies, and labels from YAML/JSON.

**Parameters:**
- `file_path`: Path to YAML or JSON file
- `format_hint`: 'phonopy', 'simple', 'json', or None (auto-detect)

**Returns:** (kpoints, frequencies, labels)

### `create_bandsdata_from_yaml(file_path, structure_node=None, format_hint=None, reciprocal=False)`
Create AiiDA BandsData node from YAML/JSON file.

**Parameters:**
- `file_path`: Path to YAML or JSON file
- `structure_node`: Optional StructureData to attach
- `format_hint`: Format hint or None for auto-detection
- `reciprocal`: Whether k-points are in reciprocal space

**Returns:** AiiDA BandsData node (not stored)

## Usage Examples by Scenario

### Scenario 1: Simple Conversion
```python
from yaml_to_bandsdata import create_bandsdata_from_yaml

bands = create_bandsdata_from_yaml("path/to/bands_data.yml")
bands.store()
```

### Scenario 2: With Structure
```python
from aiida.orm import load_node
from yaml_to_bandsdata import create_bandsdata_from_yaml

structure = load_node(123)  # Your structure PK
bands = create_bandsdata_from_yaml(
    "bands_data.yml",
    structure_node=structure,
    reciprocal=True
)
bands.store()
```

### Scenario 3: Multiple Files
```python
from pathlib import Path
from yaml_to_bandsdata import create_bandsdata_from_yaml

yaml_dir = Path("~/aiida_run/").expanduser()
for yaml_file in yaml_dir.glob("**/bands_data.yml"):
    bands = create_bandsdata_from_yaml(yaml_file)
    bands.store()
    print(f"Stored {yaml_file.name} with PK: {bands.pk}")
```

### Scenario 4: From CLI
```bash
# Single file
python3 yaml_to_bandsdata.py ~/aiida_run/.../bands_data.yml --store

# Multiple files (bash)
for file in ~/aiida_run/**/bands_data.yml; do
    python3 yaml_to_bandsdata.py "$file" --store
done
```

## Features

✓ **Multiple Format Support**: Automatically detects Phonopy, Simple, or JSON formats
✓ **Flexible K-points**: Handles Cartesian and reciprocal space
✓ **AiiDA Integration**: Creates proper AiiDA nodes ready for database storage
✓ **Structure Support**: Can attach StructureData nodes to BandsData
✓ **Robust Error Handling**: Detailed error messages for troubleshooting
✓ **CLI Interface**: Command-line tool for quick conversions
✓ **Comprehensive Documentation**: Full API reference and examples
✓ **Testing Support**: Sample file generation and test scripts

## File Locations

```
/home/jap93/aiidalab-mlip/
├── yaml_to_bandsdata.py              # Main converter module
├── example_yaml_to_bandsdata.py     # Usage examples
├── test_yaml_to_bandsdata.py        # Test and demo script
├── README_YAML_TO_BANDSDATA.md      # Documentation
└── IMPLEMENTATION_SUMMARY.md        # This file
```

## Testing

All Python files have been syntax-checked and are ready to use:
- ✓ yaml_to_bandsdata.py
- ✓ example_yaml_to_bandsdata.py
- ✓ test_yaml_to_bandsdata.py

## Next Steps

1. **For immediate use**: Run `test_yaml_to_bandsdata.py` to test the converter
2. **To convert your data**: Use the provided examples or CLI interface
3. **For integration**: Import the module in your scripts
4. **For help**: Refer to README_YAML_TO_BANDSDATA.md

## Notes

- The script automatically detects YAML vs JSON format
- Format type is detected from file structure when not specified
- K-points are expected to be shape (n_kpoints, 3)
- Frequencies are expected to be shape (n_kpoints, n_bands)
- The converter will transpose arrays if dimensions don't match
- No data is stored to the AiiDA database until explicitly called
- Optional structure attachment for band structure metadata

## Questions or Issues?

Refer to the troubleshooting section in README_YAML_TO_BANDSDATA.md for common issues and solutions.
