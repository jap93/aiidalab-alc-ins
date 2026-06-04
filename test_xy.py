import lzma
import yaml
import json
from pathlib import Path

def convert_bands_to_json(input_file="aiida-auto_bands.yml.xz", output_file="aiida-auto_bands.json"):
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: {input_file} not found.")
        return

    # Decompress and load YAML
    print(f"Decompressing and parsing {input_file}...")
    with lzma.open(input_path, mode="rt", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Write to JSON
    print(f"Writing data to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"Successfully created {output_file}")

if __name__ == "__main__":
    convert_bands_to_json()
