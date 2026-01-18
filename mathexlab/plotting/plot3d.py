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


# ============================================================
# CORE 3D PLOTS
# ============================================================

def plot3(x, y, z, *args, **kwargs):
    ax = plot_manager.prepare_plot(is_3d=True)
    if ax is None:
        return

    lines = ax.plot(
        _unwrap(x),
        _unwrap(y),
        _unwrap(z),
        *args,
        **_map_matlab_kwargs(kwargs),
    )
    plot_manager.request_draw()
    
    handles = [LineHandle(l, parent=ax) for l in lines]
    return handles[0] if len(handles) == 1 else handles


def scatter3(x, y, z, *args, **kwargs):
    ax = plot_manager.prepare_plot(is_3d=True)
    if ax is None:
        return

    sc = ax.scatter(
        _unwrap(x),
        _unwrap(y),
        _unwrap(z),
        *args,
        **_map_matlab_kwargs(kwargs),
    )
    plot_manager.request_draw()
    return ScatterHandle(sc, parent=ax)


def quiver3(x, y, z, u, v, w, **kwargs):
    ax = plot_manager.prepare_plot(is_3d=True)
    if ax is None:
        return

    q = ax.quiver(
        _unwrap(x), _unwrap(y), _unwrap(z),
        _unwrap(u), _unwrap(v), _unwrap(w),
        **_map_matlab_kwargs(kwargs)
    )
    plot_manager.request_draw()
    return GraphicsHandle(q, parent=ax)


# ============================================================
# TEXT & ANNOTATION
# ============================================================

def text(x, y, z, s, **kwargs):
    """
    text(x, y, z, str) - Add text to 3D plot.
    """
    ax = plot_manager.prepare_plot(is_3d=True)
    if ax is None: return

    # Unwrap args
    x = float(_unwrap(x)) if hasattr(_unwrap(x), 'item') else _unwrap(x)
    y = float(_unwrap(y)) if hasattr(_unwrap(y), 'item') else _unwrap(y)
    z = float(_unwrap(z)) if hasattr(_unwrap(z), 'item') else _unwrap(z)
    s = str(_unwrap(s))
    
    # Map kwargs
    kw = _map_matlab_kwargs(kwargs)
    
    # Defaults for MATLAB look
    if 'fontsize' not in kw: kw['fontsize'] = 10
    if 'color' not in kw: kw['color'] = '#eeeeee' # Default to light text in dark theme
    
    # Matplotlib 3D text uses the same .text() method but with z dir
    t = ax.text(x, y, z, s, **kw)
    plot_manager.request_draw()
    return TextHandle(t, parent=ax)


# ============================================================
# SURFACE / MESH
# ============================================================

def surf(*args, **kwargs):
    """
    surf(Z)
    surf(X, Y, Z)
    """
    ax = plot_manager.prepare_plot(is_3d=True)
    if ax is None:
        return

    # Handle single-argument surf(Z)
    unwrapped = [_unwrap(a) for a in args]
    
    if len(unwrapped) == 1:
        # surf(Z) -> generate X, Y indices
        Z = np.asarray(unwrapped[0])
        rows, cols = Z.shape
        X, Y = np.meshgrid(np.arange(cols), np.arange(rows))
    elif len(unwrapped) == 3:
        # surf(X, Y, Z)
        X, Y, Z = unwrapped
    else:
        return

    mpl_kwargs = _map_matlab_kwargs(kwargs)
    
    if 'cmap' not in mpl_kwargs and 'color' not in mpl_kwargs:
        mpl_kwargs['cmap'] = 'turbo'
    
    if 'linewidth' not in mpl_kwargs:
        mpl_kwargs['linewidth'] = 0
        
    if 'antialiased' not in mpl_kwargs:
        mpl_kwargs['antialiased'] = False

    poly = ax.plot_surface(X, Y, Z, **mpl_kwargs)
    plot_manager.request_draw()
    return SurfaceHandle(poly, parent=ax)


def mesh(*args, **kwargs):
    """
    mesh(Z)
    mesh(X, Y, Z)
    """
    ax = plot_manager.prepare_plot(is_3d=True)
    if ax is None:
        return

    # Handle single-argument mesh(Z)
    unwrapped = [_unwrap(a) for a in args]
    
    if len(unwrapped) == 1:
        Z = np.asarray(unwrapped[0])
        rows, cols = Z.shape
        X, Y = np.meshgrid(np.arange(cols), np.arange(rows))
    elif len(unwrapped) == 3:
        X, Y, Z = unwrapped
    else:
        return

    mpl_kwargs = _map_matlab_kwargs(kwargs)
    
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
        # [FIX] Flatten to ensure Matplotlib receives exactly 2 args,
        # avoiding "ValueError: not enough values to unpack" with 2D arrays.
        val = np.asarray(_unwrap(lim)).flatten()
        if val.size >= 2:
            ax.set_zlim(val[0], val[1])
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
    if ax:
        ax.set_zlabel(str(_unwrap(t)))
        plot_manager.request_draw()