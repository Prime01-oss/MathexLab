"""
Qt-based Matplotlib render widget for MathexLab UI.
"MATLAB-Grade" Edition - Public Layout API & Pro UI.

Responsibilities (STRICT):
- Provide Figure + Canvas + Toolbar
- Provide axes creation helpers
- Provide user interaction (zoom / pan / datacursor)
- NEVER decide WHEN to draw
- NEVER throttle
- NEVER schedule draws
"""

from __future__ import annotations

import numpy as np
import warnings
import traceback
import logging
import time

# [FIX] Essential for 3D plotting to work
import mpl_toolkits.mplot3d 

# Conditional imports for Headless mode support
try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QLabel, QSizePolicy, QHBoxLayout, QFrame, QSpacerItem
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QPalette, QFont
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
    from matplotlib.backend_bases import MouseButton
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QWidget = object # Mock

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.pyplot as plt

# Filter out harmless layout warnings to keep the "Professional" feel
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)


# ============================================================
# Helpers
# ============================================================

def _unwrap(v):
    """Extract raw numpy data from wrappers."""
    if hasattr(v, '_data'):
        return np.asarray(v._data)
    if isinstance(v, (list, tuple)) and len(v) > 0 and hasattr(v[0], '_data'):
        return np.array([x._data for x in v])
    return v


# ============================================================
# Stable Toolbar (Professional Look)
# ============================================================

if HAS_QT:
    class StableToolbar(NavigationToolbar2QT):
        """
        A 'Rock Solid' toolbar.
        - Transparent coordinate background.
        - Right-aligned coordinates via Spacer.
        """
        def __init__(self, canvas, parent):
            super().__init__(canvas, parent)
            
            # 1. VISUAL STYLE - Flat, Dark, Transparent Labels
            self.setStyleSheet("""
                QToolBar {
                    background-color: #252526;
                    border-bottom: 1px solid #3e3e42;
                    spacing: 4px;
                    padding: 2px;
                }
                QToolButton {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 3px;
                    color: #cccccc;
                    padding: 3px;
                }
                QToolButton:hover {
                    background-color: #3e3e42;
                    border: 1px solid #555555;
                }
                QToolButton:pressed {
                    background-color: #007acc;
                    color: white;
                }
                /* [FIX] Transparent background for coordinates */
                QLabel {
                    color: #eeeeee;
                    background-color: transparent;
                    border: none;
                    font-family: "Segoe UI", "Helvetica", sans-serif;
                    font-size: 11px;
                    font-weight: bold;
                    padding-right: 10px;
                }
            """)

            # 2. REMOVE CLUTTER
            unwanted = ["Subplots", "Customize", "Save"]
            for action in self.actions():
                if action.text() in unwanted:
                    self.removeAction(action)
            
            # 3. [FIX] FORCE RIGHT ALIGNMENT (Qt-Safe Method)
            try:
                empty = QWidget()
                empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                empty.setStyleSheet("background: transparent;")
                
                # Find the action for the coordinates label
                label_action = None
                if hasattr(self, 'locLabel'):
                    for action in self.actions():
                        if self.widgetForAction(action) == self.locLabel:
                            label_action = action
                            break
                
                # Insert spacer before the label
                if label_action:
                    self.insertWidget(label_action, empty)
                else:
                    self.addWidget(empty)
            except Exception:
                pass

            # Ensure label styling allows alignment
            if hasattr(self, 'locLabel'):
                self.locLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        def set_message(self, s):
            """Update coordinates."""
            # [CRITICAL] Call super so the internal label text is updated
            super().set_message(s)
            
            if hasattr(self, 'locLabel'):
                self.locLabel.setVisible(True)
                # Cleanup text format
                if self.coordinates:
                    txt = self.locLabel.text()
                    self.locLabel.setText(txt.replace(', ', '  '))

        def home(self, *args, **kwargs):
            """
            [FIX] Smart Home Reset.
            """
            super().home(*args, **kwargs)
            
            # Check if we need to enforce 3D aspect ratio
            has_3d = any(getattr(ax, 'name', '') == '3d' for ax in self.canvas.figure.axes)
            if has_3d:
                for ax in self.canvas.figure.axes:
                    if getattr(ax, 'name', '') == '3d':
                        try: ax.set_box_aspect((1, 1, 1))
                        except: pass
            
            self.canvas.draw_idle()


else:
    class StableToolbar:
        def __init__(self, *args, **kwargs): pass


# ============================================================
# PlotWidget (Qt) - The Rendering Surface
# ============================================================

class PlotWidget(QWidget):
    """
    Matplotlib Qt render surface.
    Engineered for STABILITY and PERFORMANCE.
    """

    def __init__(self, parent=None):
        if not HAS_QT:
            raise RuntimeError("Qt dependencies missing. Use HeadlessPlotWidget.")
        super().__init__(parent)

        # State tracking
        self._current_layout_mode = None 

        # -------------------------------------------------------
        # 1. Appearance / Defaults (Global Polish)
        # -------------------------------------------------------
        plt.rcParams.update({
            'figure.autolayout': False,             # Disable legacy tight_layout
            'figure.constrained_layout.use': True,  # Default to Constrained for 2D
            'path.simplify': True,           
            'path.simplify_threshold': 1.0,  
            'lines.antialiased': True,       
            'axes.linewidth': 0.8,           
            'xtick.direction': 'in',         
            'ytick.direction': 'in',         
            'font.family': 'sans-serif',
            'font.size': 10,
            'savefig.facecolor': '#1e1e1e',
            'savefig.edgecolor': '#1e1e1e'
        })

        # -------------------------------------------------------
        # 2. Figure / Canvas
        # -------------------------------------------------------
        try:
            self.figure = Figure(figsize=(6, 4), dpi=100, layout='constrained')
            self._current_layout_mode = '2d'
        except Exception:
            self.figure = Figure(figsize=(6, 4), dpi=100, constrained_layout=True)
            
        self.figure.patch.set_facecolor("#1e1e1e")
        
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.updateGeometry()

        self.toolbar = StableToolbar(self.canvas, self)

        # -------------------------------------------------------
        # 3. Layout (Rock Solid)
        # -------------------------------------------------------
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # Interaction State
        self._pan_active = False
        self._pan_start = None
        self._last_click_time = 0
        self._datacursor_enabled = True
        self._line_points = []
        self._annotations = []

        # Connect events
        try:
            self.canvas.mpl_connect("scroll_event", self._on_scroll)
            self.canvas.mpl_connect("button_press_event", self._on_button_press)
            self.canvas.mpl_connect("button_release_event", self._on_button_release)
            self.canvas.mpl_connect("motion_notify_event", self._on_motion)
            self.canvas.mpl_connect("button_press_event", self._on_click_for_datacursor)
        except Exception:
            pass

    # -------------------------------------------------------
    # PUBLIC Layout API (Called by state.py)
    # -------------------------------------------------------

    def configure_layout(self, is_3d: bool):
        """
        Atomically switches layout logic between 2D (Constrained) and 3D (Manual).
        Must be called BEFORE adding axes to the figure.
        """
        target_mode = '3d' if is_3d else '2d'
        
        # Optimization: Don't re-apply if state hasn't changed
        if self._current_layout_mode == target_mode:
            return

        # 1. Disable current engine to unlock everything
        if hasattr(self.figure, 'set_layout_engine'):
            self.figure.set_layout_engine('none')
        elif hasattr(self.figure, 'set_constrained_layout'):
            self.figure.set_constrained_layout(False)

        # 2. Reset margins to Defaults (Crucial to un-stick 3D settings)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                self.figure.subplots_adjust(left=0.125, right=0.9, bottom=0.11, top=0.88, wspace=0.2, hspace=0.2)
            except Exception:
                pass

        # 3. Apply New Mode
        if target_mode == '3d':
            # 3D: Manual Margins (Prevents Jitter)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    self.figure.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95)
                except Exception:
                    pass
        else:
            # 2D: Enable Constrained Layout (Prevents Overlap)
            if hasattr(self.figure, 'set_layout_engine'):
                self.figure.set_layout_engine('constrained')
            elif hasattr(self.figure, 'set_constrained_layout'):
                self.figure.set_constrained_layout(True)

        self._current_layout_mode = target_mode

    # -------------------------------------------------------
    # Axes helpers
    # -------------------------------------------------------

    def gca(self):
        if self.figure.axes:
            ax = self.figure.axes[-1]
            if not getattr(ax, '_mathex_styled', False):
                self._apply_axes_defaults(ax)
            return ax
        return self.new_axes()

    def new_axes(self, projection=None):
        is_3d = (projection == '3d')
        # Ensure layout is correct
        self.configure_layout(is_3d)

        try:
            ax = self.figure.add_subplot(111, projection=projection)
        except Exception:
            ax = self.figure.add_subplot(111)

        self._apply_axes_defaults(ax)
        return ax

    def _apply_axes_defaults(self, ax):
        try:
            ax._mathex_styled = True
            ax.set_facecolor("#252526")
            ax.tick_params(axis="both", colors="#cccccc", which='both', labelsize=9)
            
            for spine in ax.spines.values():
                spine.set_color("#666666")
                spine.set_linewidth(1.0)

            ax.grid(True, linestyle=':', linewidth=0.5, color='#444444', alpha=0.8)

            if getattr(ax, 'name', '') == '3d':
                try: ax.set_box_aspect((1, 1, 1))
                except: pass
                
                pane_color = (0.145, 0.145, 0.149, 1.0) 
                if hasattr(ax, 'xaxis'): ax.xaxis.set_pane_color(pane_color)
                if hasattr(ax, 'yaxis'): ax.yaxis.set_pane_color(pane_color)
                if hasattr(ax, 'zaxis'): ax.zaxis.set_pane_color(pane_color)
                
                grid_color = (0.4, 0.4, 0.4, 0.5)
                if hasattr(ax, 'xaxis') and hasattr(ax.xaxis, '_axinfo'): ax.xaxis._axinfo["grid"]['color'] = grid_color
                if hasattr(ax, 'yaxis') and hasattr(ax.yaxis, '_axinfo'): ax.yaxis._axinfo["grid"]['color'] = grid_color
                if hasattr(ax, 'zaxis') and hasattr(ax.zaxis, '_axinfo'): ax.zaxis._axinfo["grid"]['color'] = grid_color

                if hasattr(ax, 'xaxis'): ax.xaxis.label.set_color("#eeeeee")
                if hasattr(ax, 'yaxis'): ax.yaxis.label.set_color("#eeeeee")
                if hasattr(ax, 'zaxis'): ax.zaxis.label.set_color("#eeeeee")

        except Exception as e:
            print(f"[Warning] Failed to apply axes style: {e}")

    # -------------------------------------------------------
    # Utilities
    # -------------------------------------------------------

    def render(self, *, immediate: bool = False):
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore")
                if self.figure.get_figwidth() <= 0: return
                if immediate:
                    self.canvas.draw()
                    self.canvas.flush_events()
                else:
                    self.canvas.draw_idle()
        except Exception:
            pass

    def savefig(self, path, **kwargs):
        try:
            self.figure.savefig(path, **kwargs)
            return True
        except Exception:
            return False

    def clear(self):
        """Clear figure and RESET layout state to default 2D."""
        try:
            self.figure.clf()
            
            # [RESET] Force clean 2D state for next plot
            self._current_layout_mode = None
            self.configure_layout(is_3d=False)
            
        except Exception:
            pass
        self._line_points.clear()
        self.clear_annotations()
        
        if hasattr(self, 'toolbar') and self.toolbar:
            if hasattr(self.toolbar, '_nav_stack'):
                self.toolbar._nav_stack.clear()
            self.toolbar.update()

    # -------------------------------------------------------
    # Events
    # -------------------------------------------------------
    def ginput(self, n=1, timeout=30, show_clicks=True):
        try:
            self.canvas.draw()
            self.canvas.flush_events()
            return self.figure.ginput(n=n, timeout=timeout, show_clicks=show_clicks, mouse_add=1, mouse_pop=3, mouse_stop=2)
        except Exception:
            return []

    def enable_datacursor(self, enabled=True):
        self._datacursor_enabled = bool(enabled)

    def clear_annotations(self):
        for ann in list(self._annotations):
            try: ann.remove()
            except: pass
        self._annotations.clear()

    def _on_click_for_datacursor(self, event):
        if event.button != 1 or not self._datacursor_enabled: return
        ax = event.inaxes
        if ax is None or getattr(ax, 'name', '') == '3d': return

        best, bestd = None, float("inf")
        for xs, ys in self._line_points:
            dx, dy = xs - event.xdata, ys - event.ydata
            d = dx*dx + dy*dy
            idx = np.nanargmin(d)
            if d[idx] < bestd:
                bestd, best = d[idx], (xs[idx], ys[idx])

        if best:
            self.clear_annotations()
            try:
                ann = ax.annotate(
                    f"X: {best[0]:.4g}\nY: {best[1]:.4g}",
                    xy=best, xytext=(15, 15), textcoords="offset points",
                    color="#f0f0f0", fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="#333333", ec="#555555", alpha=0.9),
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3", color="#999999")
                )
                self._annotations.append(ann)
                self.canvas.draw_idle()
            except: pass

    def _on_scroll(self, event):
        ax = event.inaxes
        if ax is None or getattr(ax, 'name', '') == '3d': return
        scale = 1.15 if event.button == "up" else 1.0/1.15
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        x, y = event.xdata, event.ydata
        new_w, new_h = (xlim[1]-xlim[0])*scale, (ylim[1]-ylim[0])*scale
        rx, ry = (x-xlim[0])/(xlim[1]-xlim[0]), (y-ylim[0])/(ylim[1]-ylim[0])
        ax.set_xlim([x - new_w * rx, x + new_w * (1-rx)])
        ax.set_ylim([y - new_h * ry, y + new_h * (1-ry)])
        self.canvas.draw_idle()

    def _on_button_press(self, event):
        if event.button == 3:
            now = time.time()
            if now - self._last_click_time < 0.3:
                self.toolbar.home()
                return
            self._last_click_time = now
        if event.button == 3 and event.inaxes and getattr(event.inaxes, 'name', '') != '3d':
            self._pan_active = True
            self._pan_start = (event.inaxes, event.xdata, event.ydata)

    def _on_button_release(self, event):
        self._pan_active = False

    def _on_motion(self, event):
        if self._pan_active and event.inaxes:
            ax, x0, y0 = self._pan_start
            dx, dy = event.xdata - x0, event.ydata - y0
            ax.set_xlim(ax.get_xlim() - dx)
            ax.set_ylim(ax.get_ylim() - dy)
            self.canvas.draw_idle()


# ============================================================
# Headless Widget (Mock)
# ============================================================

class HeadlessPlotWidget:
    def __init__(self):
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasAgg(self.figure)
    def gca(self): return self.figure.gca()
    def new_axes(self, projection=None): return self.figure.add_subplot(111, projection=projection)
    def configure_layout(self, is_3d: bool): pass  # API Compatibility
    def render(self, *, immediate=False): pass
    def savefig(self, path, **kwargs): self.figure.savefig(path, **kwargs)
    def clear(self): self.figure.clf()
    def ginput(self, n=1, **k): return []