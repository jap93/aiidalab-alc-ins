import sys
from pathlib import Path
import numpy as np

def remove_header_and_load(file_path):
    """
    Reads an XY data file, skips the first line, and returns a NumPy array.
    
    Parameters:
        file_path (str): Path to the input data file.
        
    Returns:
        np.ndarray: Array of shape (N, 2) containing the data.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    # Using numpy's loadtxt is the most efficient way to skip rows
    # and handle numerical XY data.
    try:
        data = np.loadtxt(path, skiprows=1)
        return data
    except Exception as e:
        # Fallback to manual parsing if the file has inconsistent columns
        data = []
        with path.open('r') as f:
            next(f)  # Skip the first line
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        data.append([float(parts[0]), float(parts[1])])
                    except ValueError:
                        continue
        return np.array(data)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_xy_data.py <filename>")
        sys.exit(1)

    try:
        xy_data = remove_header_and_load(sys.argv[1])
        print(f"Successfully loaded {len(xy_data)} points.")
        print("First 5 points:\n", xy_data[:5])
    except Exception as e:
        print(f"Error: {e}")