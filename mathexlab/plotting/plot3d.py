"""
MATLAB-style 3D plotting API for MathexLab.

FINAL, ENGINE-COMPLIANT VERSION.

Rules:
- NO widget access
- NO canvas access
- NO drawing / flushing
- ONLY request draws via PlotStateManager
"""

import numpy as np
import matplotlib.cm as cm

from mathexlab.math.arrays import MatlabArray
from .state import plot_manager
from mathexlab.plotting.handles import (
    GraphicsHandle, SurfaceHandle, LineHandle, ScatterHandle, TextHandle
)


# ============================================================
# HELPERS
# ============================================================

def _unwrap(arg):
    if isinstance(arg, MatlabArray):
        return arg._data
    if isinstance(arg, (list, tuple)):
        return np.asarray(arg)
    return arg

def _unwrap_1d(arg):
    """
    Force unwrapped data into a 1D numpy array.
    Crucial for plot3/scatter3 to avoid Matplotlib Line3D initialization errors.
    """
    data = _unwrap(arg)
    # Flatten allows (1, N) or (N, 1) or (N,) to become (N,)
    return np.asarray(data).flatten()


def _map_matlab_kwargs(kwargs):
    mapping = {
        "LineWidth": "linewidth",
        "LineStyle": "linestyle",
        "MarkerSize": "markersize",
        "Color": "color",
        "Marker": "marker",
        "FaceColor": "facecolor",
        "EdgeColor": "edgecolor",
        "AlphaData": "alpha",
        "FaceAlpha": "alpha",
        "FontSize": "fontsize",
        "FontWeight": "fontweight",
        "HorizontalAlignment": "horizontalalignment",
        "VerticalAlignment": "verticalalignment",
        "String": "text"
    }
    out = {}
    for k, v in kwargs.items():
        key = k.strip("'") if isinstance(k, str) else k
        out[mapping.get(key, key)] = _unwrap(v)
    return out

def _is_format_string(s):
    """Check if a string is a valid Matplotlib format string (e.g., 'r--', 'bo')."""
    if not isinstance(s, str):
        return False
    # Basic set of valid characters for colors, markers, and line styles
    valid = set("rgbcmykw" + "o+*.xsd^v><ph" + "-:")
    return 1 <= len(s) <= 4 and set(s).issubset(valid)

def _parse_plot3_args(args):
    """
    Parses *args for plot3 to separate data/fmt from Name-Value pairs.
    Handles: plot3(x,y,z, 'r', 'LineWidth', 2)
    """
    data_args = []
    kw = {}
    
    i = 0
    n = len(args)
    while i < n:
        arg = _unwrap(args[i])
        
        # Check if this is a Name-Value pair (String that isn't a fmt string)
        if isinstance(arg, str) and not _is_format_string(arg):
            # Ensure there is a value following the name
            if i + 1 < n:
                key = arg
                val = args[i+1]
                kw[key] = val
                i += 2
                continue
            else:
                data_args.append(arg)
                i += 1
        else:
            # It's data (x, y, z) or a format string ('r', '--')
            data_args.append(arg)
            i += 1
            
    return data_args, _map_matlab_kwargs(kw)

def _parse_surf_args(args):
    """
    Parses *args for surf/mesh.
    Distinguishes between Data (Z or X,Y,Z) and Name-Value pairs.
    Does NOT support format strings (surf doesn't use 'r--').
    """
    data_args = []
    kw = {}
    
    i = 0
    n = len(args)
    while i < n:
        arg = _unwrap(args[i])
        
        # If we hit a string that looks like a property name, assume start of kwargs
        if isinstance(arg, str):
            if i + 1 < n:
                key = arg
                val = args[i+1]
                kw[key] = val
                i += 2
                continue
            else:
                i += 1
        else:
            data_args.append(arg)
            i += 1

    return data_args, _map_matlab_kwargs(kw)


# ============================================================
# CORE 3D PLOTS
# ============================================================

def plot3(x, y, z, *args, **kwargs):
    ax = plot_manager.prepare_plot(is_3d=True)
    if ax is None:
        return

    # [FIX] Parse args to handle 'LineWidth', 2 etc.
    extra_data, extra_kw = _parse_plot3_args(args)
    
    # Merge explicit kwargs with parsed Name-Value pairs
    final_kw = _map_matlab_kwargs(kwargs)
    final_kw.update(extra_kw)

    # [FIX] Force inputs to 1D arrays to prevent Line3D shape errors
    lines = ax.plot(
        _unwrap_1d(x),
        _unwrap_1d(y),
        _unwrap_1d(z),
        *extra_data,
        **final_kw,
    )
    plot_manager.request_draw()
    
    handles = [LineHandle(l, parent=ax) for l in lines]
    return handles[0] if len(handles) == 1 else handles


def scatter3(x, y, z, *args, **kwargs):
    ax = plot_manager.prepare_plot(is_3d=True)
    if ax is None:
        return

    # [FIX] Parse args to handle Name-Value pairs for scatter
    extra_data = []
    kw = {}
    
    # Pre-process args to remove 'filled' and handle N-V pairs
    raw_args = [_unwrap(a) for a in args]
    i = 0
    while i < len(raw_args):
        arg = raw_args[i]
        if isinstance(arg, str):
            if arg.lower() == "filled":
                i += 1
                continue
            elif not _is_format_string(arg) and i + 1 < len(raw_args):
                kw[arg] = raw_args[i+1]
                i += 2
                continue
        extra_data.append(arg)
        i += 1

    final_kw = _map_matlab_kwargs(kwargs)
    final_kw.update(_map_matlab_kwargs(kw))

    # [FIX] Force inputs to 1D arrays
    sc = ax.scatter(
        _unwrap_1d(x),
        _unwrap_1d(y),
        _unwrap_1d(z),
        *extra_data,
        **final_kw,
    )
    plot_manager.request_draw()
    return ScatterHandle(sc, parent=ax)


def quiver3(x, y, z, u, v, w, **kwargs):
    ax = plot_manager.prepare_plot(is_3d=True)
    if ax is None:
        return

    q = ax.quiver(
        _unwrap_1d(x), _unwrap_1d(y), _unwrap_1d(z),
        _unwrap_1d(u), _unwrap_1d(v), _unwrap_1d(w),
        **_map_matlab_kwargs(kwargs)
    )
    plot_manager.request_draw()
    return GraphicsHandle(q, parent=ax)


# ============================================================
# TEXT & ANNOTATION
# ============================================================

def text(x, y, z, s, **kwargs):
    ax = plot_manager.prepare_plot(is_3d=True)
    if ax is None: return

    x_val = _unwrap(x)
    y_val = _unwrap(y)
    z_val = _unwrap(z)
    
    if hasattr(x_val, 'item') and x_val.size == 1: x_val = x_val.item()
    if hasattr(y_val, 'item') and y_val.size == 1: y_val = y_val.item()
    if hasattr(z_val, 'item') and z_val.size == 1: z_val = z_val.item()

    s = str(_unwrap(s))
    kw = _map_matlab_kwargs(kwargs)
    
    if 'fontsize' not in kw: kw['fontsize'] = 10
    if 'color' not in kw: kw['color'] = '#eeeeee' 
    
    t = ax.text(float(x_val), float(y_val), float(z_val), s, **kw)
    plot_manager.request_draw()
    return TextHandle(t, parent=ax)


# ============================================================
# SURFACE / MESH
# ============================================================

def surf(*args, **kwargs):
    """
    surf(Z)
    surf(X, Y, Z)
    surf(..., Name, Value)
    """
    ax = plot_manager.prepare_plot(is_3d=True)
    if ax is None:
        return

    # [FIX] Separate Data from Name-Value pairs
    data_args, extra_kw = _parse_surf_args(args)
    
    # Merge kwargs
    mpl_kwargs = _map_matlab_kwargs(kwargs)
    mpl_kwargs.update(extra_kw)

    # Determine X, Y, Z
    if len(data_args) == 1:
        # surf(Z) -> generate X, Y indices
        Z = np.asarray(data_args[0])
        rows, cols = Z.shape
        X, Y = np.meshgrid(np.arange(cols), np.arange(rows))
    elif len(data_args) >= 3:
        # surf(X, Y, Z, [C])
        X, Y, Z = np.asarray(data_args[0]), np.asarray(data_args[1]), np.asarray(data_args[2])
    else:
        # Invalid arguments
        return

    # Defaults
    if 'cmap' not in mpl_kwargs and 'color' not in mpl_kwargs:
        mpl_kwargs['cmap'] = 'turbo'
    
    if 'linewidth' not in mpl_kwargs:
        mpl_kwargs['linewidth'] = 0
        
    if 'antialiased' not in mpl_kwargs:
        mpl_kwargs['antialiased'] = False

    # [FIX] Remove 'color' if 'cmap' is present (mutually exclusive in plot_surface sometimes)
    if 'cmap' in mpl_kwargs and 'color' in mpl_kwargs:
        mpl_kwargs.pop('color')

    poly = ax.plot_surface(X, Y, Z, **mpl_kwargs)
    plot_manager.request_draw()
    return SurfaceHandle(poly, parent=ax)


def mesh(*args, **kwargs):
    """
    mesh(Z)
    mesh(X, Y, Z)
    mesh(..., Name, Value)
    """
    ax = plot_manager.prepare_plot(is_3d=True)
    if ax is None:
        return

    # [FIX] Separate Data from Name-Value pairs
    data_args, extra_kw = _parse_surf_args(args)
    
    # Merge kwargs
    mpl_kwargs = _map_matlab_kwargs(kwargs)
    mpl_kwargs.update(extra_kw)

    if len(data_args) == 1:
        Z = np.asarray(data_args[0])
        rows, cols = Z.shape
        X, Y = np.meshgrid(np.arange(cols), np.arange(rows))
    elif len(data_args) >= 3:
        X, Y, Z = np.asarray(data_args[0]), np.asarray(data_args[1]), np.asarray(data_args[2])
    else:
        return
    
    if 'cmap' not in mpl_kwargs:
        mpl_kwargs['cmap'] = 'turbo'

    w = ax.plot_wireframe(X, Y, Z, **mpl_kwargs)
    plot_manager.request_draw()
    return SurfaceHandle(w, parent=ax)


# ============================================================
# CONTOURS
# ============================================================

def contour3(*args, **kwargs):
    ax = plot_manager.prepare_plot(is_3d=True)
    if ax is None:
        return

    unwrapped = [_unwrap(a) for a in args]
    
    if len(unwrapped) == 1:
        Z = np.asarray(unwrapped[0])
        rows, cols = Z.shape
        X, Y = np.meshgrid(np.arange(cols), np.arange(rows))
    elif len(unwrapped) >= 3:
        X, Y, Z = unwrapped[0], unwrapped[1], unwrapped[2]
    else:
        return

    c = ax.contour(X, Y, Z, **_map_matlab_kwargs(kwargs))
    plot_manager.request_draw()
    return GraphicsHandle(c, parent=ax)


def contourf3(*args, **kwargs):
    ax = plot_manager.prepare_plot(is_3d=True)
    if ax is None:
        return

    unwrapped = [_unwrap(a) for a in args]
    
    if len(unwrapped) == 1:
        Z = np.asarray(unwrapped[0])
        rows, cols = Z.shape
        X, Y = np.meshgrid(np.arange(cols), np.arange(rows))
    elif len(unwrapped) >= 3:
        X, Y, Z = unwrapped[0], unwrapped[1], unwrapped[2]
    else:
        return

    c = ax.contourf(X, Y, Z, **_map_matlab_kwargs(kwargs))
    plot_manager.request_draw()
    return GraphicsHandle(c, parent=ax)


# ============================================================
# CAMERA / VIEW / AXES
# ============================================================

def view(az=None, el=None):
    ax = plot_manager.gca(is_3d=True)
    if ax is None:
        return

    if az is None and el is None:
        return

    az_val = _unwrap(az)
    el_val = _unwrap(el) if el is not None else None

    def _to_float(v):
        try:
            return float(v.item()) if isinstance(v, np.ndarray) else float(v)
        except:
            return 0.0

    if el_val is None and isinstance(az_val, (np.ndarray, list, tuple)):
        flat = np.asarray(az_val).flatten()
        if flat.size == 2:
            az_val = flat[0]
            el_val = flat[1]
        elif flat.size == 1:
            az_val = flat[0]

    if el_val is None:
        try:
            val = _to_float(az_val)
            if val == 2:
                ax.view_init(elev=90, azim=-90)
            elif val == 3:
                ax.view_init(elev=30, azim=-60)
        except Exception:
            pass 
    else:
        try:
            ax.view_init(elev=_to_float(el_val), azim=_to_float(az_val))
        except Exception:
            pass

    plot_manager.request_draw()


def axis_equal():
    plot_manager.axis_equal(True)
    plot_manager.request_draw()


def zlim(lim):
    """
    zlim([min max]) - Set z-axis limits.
    """
    ax = plot_manager.gca(is_3d=True)
    if ax:
        # [FIX] Ensure Matplotlib gets float args
        try:
            val = np.asarray(_unwrap(lim)).flatten()
            if val.size >= 2:
                # Check for 3D compatibility to avoid AttributeErrors
                if hasattr(ax, 'set_zlim'):
                    ax.set_zlim(val[0], val[1])
        except Exception:
            pass
        plot_manager.request_draw()


def axis(mode):
    """
    axis([xmin xmax ymin ymax zmin zmax]) - Set 3D axis limits.
    """
    ax = plot_manager.gca(is_3d=True)
    if ax is None:
        return

    val = _unwrap(mode)
    # Handle numeric array input for axis limits
    if isinstance(val, (list, tuple, np.ndarray)):
        arr = np.asarray(val).flatten()
        if arr.size >= 6:
            ax.set_xlim(arr[0], arr[1])
            ax.set_ylim(arr[2], arr[3])
            # [FIX] Check for 3D capability before setting Z limits
            if hasattr(ax, 'set_zlim'):
                ax.set_zlim(arr[4], arr[5])
    else:
        # String mode
        try:
            ax.axis(str(mode).lower())
        except Exception:
            pass

    plot_manager.request_draw()


# ============================================================
# LIGHTING / SHADING
# ============================================================

def camlight():
    plot_manager.request_draw()


def lighting(mode="flat"):
    plot_manager.request_draw()

def shading(mode="flat"):
    ax = plot_manager.gca(is_3d=True)
    if ax is None:
        return

    mode = str(mode).lower()

    for artist in ax.collections:
        try:
            if mode == "flat":
                artist.set_edgecolor("none")
            elif mode in ("interp", "gouraud"):
                artist.set_edgecolor("none")
            elif mode == "faceted":
                artist.set_edgecolor("k")
        except Exception:
            pass

    plot_manager.request_draw()


# ============================================================
# AXES LABELS
# ============================================================

def xlabel(t):
    ax = plot_manager.gca(is_3d=True)
    if ax:
        ax.set_xlabel(str(_unwrap(t)))
        plot_manager.request_draw()


def ylabel(t):
    ax = plot_manager.gca(is_3d=True)
    if ax:
        ax.set_ylabel(str(_unwrap(t)))
        plot_manager.request_draw()


def zlabel(t):
    ax = plot_manager.gca(is_3d=True)
    # [FIX] Check for 3D capability before setting label
    if ax and hasattr(ax, 'set_zlabel'):
        ax.set_zlabel(str(_unwrap(t)))
        plot_manager.request_draw()