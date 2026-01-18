import scipy.io
import numpy as np
from pathlib import Path
from mathexlab.math.arrays import MatlabArray

def save_workspace(session, filename="mathexlab_workspace.mat"):
    """
    Saves the current variables to a .mat file.
    """
    if not filename.endswith(".mat"):
        filename += ".mat"
        
    data = {}
    # Extract variables from session
    for name, val in session.globals.items():
        if name.startswith("_") or callable(val) or isinstance(val, type(np)):
            continue
            
        # Unwrap MatlabArray to numpy for compatibility
        if isinstance(val, MatlabArray):
            data[name] = val._data
        elif isinstance(val, (int, float, str, list, tuple, np.ndarray)):
            data[name] = val
            
    try:
        scipy.io.savemat(filename, data)
        print(f"Workspace saved to {filename}")
    except Exception as e:
        print(f"Error saving workspace: {e}")

def load_workspace(session, filename="mathexlab_workspace.mat"):
    """
    Loads variables from a .mat file into the session.
    """
    if not filename.endswith(".mat"):
        filename += ".mat"
        
    if not Path(filename).exists():
        print(f"File not found: {filename}")
        return

    try:
        data = scipy.io.loadmat(filename)
        
        for name, val in data.items():
            if name.startswith("__"): continue # Skip metadata
            
            # Wrap numpy arrays back into MatlabArray
            if isinstance(val, np.ndarray):
                session.set_variable(name, MatlabArray(val))
            else:
                session.set_variable(name, val)
                
        print(f"Loaded variables from {filename}")
    except Exception as e:
        print(f"Error loading workspace: {e}")