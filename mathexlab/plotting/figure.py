"""
MATLAB-style Figure Management for MathexLab
--------------------------------------------

Semantics:
    figure()              -> select/create Figure 1
    figure(n)             -> select/create Figure n
    gcf()                 -> return current Figure
    clf()                 -> clear current Figure
    close()               -> close current Figure
    close(n)              -> close Figure n
    close('all')          -> close all non-UI figures

Rules:
    - Figure 1 is the docked UI figure (if UI exists)
    - figure(n>1) creates standalone PlotWidget figures
    - No backend selection
    - No pyplot usage
"""

from typing import Optional, Dict, Union

from .state import plot_manager
from .mpl_backend import PlotWidget, HeadlessPlotWidget
from .engine import PlotEngine

# ------------------------------------------------------------------
# Internal registry
# ------------------------------------------------------------------

_figures: Dict[int, Union[PlotWidget, HeadlessPlotWidget]] = {}
_current: int = 1

# Injected by UI on startup (optional)
_ui_widget: Optional[PlotWidget] = None


# ------------------------------------------------------------------
# UI bootstrap (called once by UI layer)
# ------------------------------------------------------------------

def init_ui_widget(widget: PlotWidget):
    """
    Register the docked UI PlotWidget as Figure 1.
    """
    global _ui_widget
    _ui_widget = widget
    _figures[1] = widget
    plot_manager.set_widget(widget)


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _create_widget():
    """Factory to create appropriate widget based on engine mode."""
    # Ensure engine is initialized to check mode
    PlotEngine.initialize()
    
    # If in test or CLI mode, use headless
    if PlotEngine._mode in ("test", "cli"):
        return HeadlessPlotWidget()
        
    # Default to Qt widget
    return PlotWidget()

def _ensure_figure_1():
    """
    Guarantee Figure 1 exists.
    """
    if 1 not in _figures:
        if _ui_widget is not None:
            _figures[1] = _ui_widget
        else:
            _figures[1] = _create_widget()


def _activate(num: int):
    """
    Activate figure `num` and bind it to PlotStateManager.
    """
    global _current

    if num == 1:
        _ensure_figure_1()
    else:
        if num not in _figures:
            _figures[num] = _create_widget()

    _current = num
    plot_manager.set_widget(_figures[num])

# ------------------------------------------------------------------
# Auto-Creation Hook
# ------------------------------------------------------------------
def _auto_create_figure():
    """Callback for PlotStateManager to auto-create figure."""
    figure(1)

# Register the hook immediately
plot_manager.set_figure_creator(_auto_create_figure)


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def figure(num: Optional[int] = None, **kwargs) -> int:
    """
    Select or create a figure.

    figure()      -> Figure 1
    figure(n)     -> Figure n
    """
    if num is None:
        num = 1

    try:
        num = int(num)
    except Exception:
        num = 1

    _activate(num)

    # Optional future: Name handling
    name = kwargs.get("Name") or kwargs.get("name")
    if name:
        try:
            widget = _figures[num]
            # Headless widget might not have setWindowTitle
            if hasattr(widget, "setWindowTitle"):
                widget.setWindowTitle(str(name))
            elif hasattr(widget, "parent"):
                 p = widget.parent()
                 if hasattr(p, "setWindowTitle"):
                     p.setWindowTitle(str(name))
        except Exception:
            pass

    return num


def gcf():
    """
    Return the current Matplotlib Figure object.
    """
    _ensure_figure_1()
    widget = _figures.get(_current)
    return getattr(widget, "figure", None)


def clf():
    """
    Clear current figure contents (MATLAB clf).
    """
    _ensure_figure_1()
    try:
        plot_manager.clf()
    except Exception:
        pass


def close(target: Union[int, str, None] = None):
    """
    Close figures.

    close()        -> close current figure
    close(n)       -> close figure n
    close('all')   -> close all non-UI figures
    """
    global _current

    if target is None:
        target = _current

    # Close all non-UI figures
    if isinstance(target, str) and target.lower() == "all":
        for n in list(_figures.keys()):
            if n == 1:
                continue
            w = _figures.pop(n, None)
            if w and hasattr(w, "setParent"):
                try:
                    w.setParent(None)
                except Exception:
                    pass
        _activate(1)
        return

    # Close single figure
    try:
        n = int(target)
    except Exception:
        return

    if n == 1:
        # MATLAB: close(1) clears but does not destroy UI figure
        clf()
        return

    w = _figures.pop(n, None)
    if w and hasattr(w, "setParent"):
        try:
            w.setParent(None)
        except Exception:
            pass

    if _current == n:
        remaining = sorted(_figures.keys())
        _activate(remaining[0] if remaining else 1)


def closeall():
    """Alias for close('all')."""
    close("all")