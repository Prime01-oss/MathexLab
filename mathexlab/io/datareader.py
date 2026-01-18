import os
import pandas as pd
import numpy as np
import scipy.io
from mathexlab.math.arrays import MatlabArray
from mathexlab.math.structs import MatlabStruct

def readtable(filename, **kwargs):
    """
    T = readtable(filename)
    Returns a struct of arrays (since we don't have a Table class yet).
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")

    # Auto-detect format
    ext = os.path.splitext(filename)[1].lower()
    
    try:
        if ext in ('.xls', '.xlsx'):
            df = pd.read_excel(filename, **kwargs)
        else:
            # Default to CSV for everything else
            df = pd.read_csv(filename, **kwargs)
    except Exception as e:
        raise IOError(f"Could not read table: {str(e)}")

    # Convert DataFrame to Struct of MatlabArrays
    data = {}
    for col in df.columns:
        # Clean column name (MATLAB valid identifier)
        safe_col = "".join(c for c in col if c.isalnum() or c=='_')
        if not safe_col: safe_col = "Var"
        
        val = df[col].values
        # Convert strings/objects, keep numbers
        if val.dtype == object:
            # Convert to list of strings
            val = [str(x) for x in val]
        
        data[safe_col] = MatlabArray(val)

    return MatlabStruct(**data)

def readmatrix(filename, **kwargs):
    """
    M = readmatrix(filename)
    Returns a numeric matrix, skipping headers automatically.
    """
    # Force pandas to ignore headers and return numpy array
    try:
        if filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(filename, header=None, **kwargs)
        else:
            df = pd.read_csv(filename, header=None, **kwargs)
            
        # Attempt to find the numeric block
        df_numeric = df.apply(pd.to_numeric, errors='coerce')
        # Drop rows/cols that are all NaN (headers/index)
        df_numeric = df_numeric.dropna(how='all', axis=0).dropna(how='all', axis=1)
        
        return MatlabArray(df_numeric.values)
    except Exception as e:
        raise IOError(f"Could not read matrix: {str(e)}")

def csvread(filename):
    """Legacy MATLAB csvread."""
    return readmatrix(filename)

def loadmat(filename):
    """
    S = loadmat(filename)
    Reads MATLAB .mat files (versions 4, 5, 7.1).
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")
        
    try:
        # struct_as_record=False loads structs as objects, simpler for us to wrap
        mat_dict = scipy.io.loadmat(filename, struct_as_record=False, squeeze_me=True)
        
        clean_data = {}
        for k, v in mat_dict.items():
            # Skip internal metadata keys (__header__, etc.)
            if k.startswith('__'):
                continue
            
            # Wrap in MatlabArray
            clean_data[k] = MatlabArray(v)
            
        return MatlabStruct(**clean_data)
    except NotImplementedError:
        raise IOError("MathexLab cannot read -v7.3 .mat files (HDF5 based) yet. Please save as -v7.")
    except Exception as e:
        raise IOError(f"Failed to load .mat file: {str(e)}")

def load(filename):
    """
    load(filename)
    Universal loader. Detects .mat, .csv, or .txt.
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.mat':
        return loadmat(filename)
    return readtable(filename)
