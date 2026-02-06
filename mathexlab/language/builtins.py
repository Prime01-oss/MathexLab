import numpy as np
import os
import time
from mathexlab.math.arrays import MatlabArray
from mathexlab.math.structs import MatlabStruct
from mathexlab.plotting.state import plot_manager

# ==========================================================
# MATLAB Built-ins
# ==========================================================

# [FIX] Added num2str function (Safely wraps string in MatlabArray)
def num2str(x, format_spec=None):
    """
    s = num2str(x)
    Converts number to string representation.
    """
    # Unwrap MatlabArray
    if isinstance(x, MatlabArray):
        val = x._data
    else:
        val = x
        
    # Handle Scalar
    if np.isscalar(val) or (isinstance(val, np.ndarray) and val.size == 1):
        if isinstance(val, np.ndarray): val = val.item()
        
        # Complex handling (Python uses j, MATLAB uses i)
        if isinstance(val, (complex, np.complex128, np.complex64)):
            s = str(val).replace('j', 'i')
        elif format_spec:
            s = "{:.4f}".format(val)
        else:
            s = str(val)
        
        # [FIX] Return as MatlabArray so it can be concatenated with other arrays
        return MatlabArray(np.array(s))
        
    # Handle Array (simplified default string representation)
    return MatlabArray(np.array(str(val)))


# [FIX] Added deal function for Phase 3 anonymous functions
def deal(*args):
    """
    [a, b] = deal(x, y)
    [a, b] = deal(x) % copies x to a and b
    """
    if len(args) == 0:
        return None
    if len(args) == 1:
        return args[0]
    return args


def disp(x=None):
    if x is None:
        print()
    else:
        print(x)

disp.__mathexlab_command__ = True


def clc():
    # Print Form Feed (\f) which ConsoleWidget intercepts
    print("\f", end="")

clc.__mathexlab_command__ = True


# --- ANIMATION COMMANDS (NEW) ---

def drawnow():
    """
    drawnow;
    Update figures and process callbacks.
    """
    # immediate=True: tells backend to flush events
    # wait=True: blocks Kernel thread until UI thread confirms draw is done
    plot_manager.request_draw(immediate=True, wait=True)

drawnow.__mathexlab_command__ = True


def pause(n=None):
    """
    pause(n) - Pause for n seconds.
    pause - Wait for user response (not fully impl, treats as 0.1s sleep)
    """
    # Always force a draw before pausing
    drawnow()
    
    if n is None:
        time.sleep(0.01)
        return
    
    # n might be MatlabArray, cast to float
    sec = float(n)
    if sec > 0:
        time.sleep(sec)

pause.__mathexlab_command__ = True


# --- END ANIMATION COMMANDS ---


def size(x, dim=None):
    """
    MATLAB-compatible size():
      size(x)      -> [m n] (returns MatlabArray)
      size(x, dim) -> scalar (returns MatlabArray)
    """
    # Handle standard Python types gracefully
    if not hasattr(x, "shape"):
        # Scalars have size [1 1]
        return MatlabArray([1, 1])

    shape = x.shape

    if dim is not None:
        # MATLAB uses 1-based indexing for dimensions
        # If dim is larger than ndim, returns 1
        d = int(dim)
        if d < 1 or d > len(shape):
            return MatlabArray(1)
        return MatlabArray(shape[d - 1])

    # Return shape as a MatlabArray row vector
    return MatlabArray(list(shape))


def length(x):
    """
    MATLAB length(): max(size(x))
    """
    if not hasattr(x, "shape"):
        return MatlabArray(1)
    return MatlabArray(max(x.shape) if x.shape else 1)


def numel(x):
    """
    MATLAB numel(): total number of elements
    """
    if not hasattr(x, "shape"):
        return MatlabArray(1)
    return MatlabArray(int(np.prod(x.shape)))


def who(namespace):
    print("Your variables are:")
    names = sorted(
        k for k, v in namespace.items()
        if not k.startswith("__") and not callable(v)
    )
    if names:
        print("  " + "  ".join(names))
    else:
        print("  (none)")
    print()

who.__mathexlab_command__ = True


def whos(namespace):
    print(f"{'Name':<12} {'Size':<16} {'Class'}")
    print("-" * 40)

    for name, val in sorted(namespace.items()):
        if name.startswith("__") or callable(val):
            continue

        if hasattr(val, "shape"):
            dims = "x".join(str(d) for d in val.shape)
            size_str = dims
        else:
            size_str = "1x1"

        if isinstance(val, MatlabArray):
            cls = "double" 
            if val.is_sparse:
                cls = "sparse double"
            elif val._data.dtype == object:
                cls = "struct array"
        elif isinstance(val, (int, float, complex)):
            cls = "double"
        elif isinstance(val, str):
            cls = "char"
        elif isinstance(val, MatlabStruct):
            cls = "struct"
        else:
            cls = type(val).__name__

        print(f"{name:<12} {size_str:<16} {cls}")

    print()
    
whos.__mathexlab_command__ = True


def exist(name, kind=None, namespace=None):
    """
    exist name [kind]
    """
    if not isinstance(name, str):
        return 0

    if (kind == 'var' or kind is None) and namespace is not None:
        if name in namespace:
            return 1
            
    if kind == 'file' or kind == 'dir' or kind is None:
        if os.path.exists(name):
            if os.path.isdir(name):
                return 7
            return 2
        if os.path.exists(name + ".m"):
            return 2
            
    return 0


def struct(*args):
    """
    s = struct('field1', val1, 'field2', val2, ...)
    """
    if len(args) % 2 != 0:
        raise ValueError("struct requires field-value pairs.")
    
    keys = []
    values = []
    max_len = 1
    has_cells = False

    for i in range(0, len(args), 2):
        key = args[i]
        if isinstance(key, MatlabArray): key = str(key._data)
        if not isinstance(key, str): raise ValueError("Field names must be strings.")
        
        val = args[i+1]
        
        if isinstance(val, MatlabArray) and val._data.dtype == object:
             val = val._data.flatten().tolist()
        
        if isinstance(val, (list, tuple)):
            has_cells = True
            max_len = max(max_len, len(val))
        
        keys.append(key)
        values.append(val)

    if not has_cells or max_len == 0:
        data = {k: v for k, v in zip(keys, values)}
        return MatlabStruct(**data)

    struct_list = []
    for idx in range(max_len):
        data = {}
        for k, v in zip(keys, values):
            if isinstance(v, (list, tuple)):
                if idx < len(v):
                    data[k] = v[idx]
                else:
                    data[k] = None
            else:
                data[k] = v
        struct_list.append(MatlabStruct(**data))

    return MatlabArray(np.array(struct_list, dtype=object).reshape(1, max_len))