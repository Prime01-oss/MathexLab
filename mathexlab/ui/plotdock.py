# mathexlab/ui/plotdock.py
"""
PlotDock - container for the MathexLab plotting surface.

Improvements in this version:
  * Automatically registers the internal PlotWidget with plot_manager so
    the kernel/session finds the widget even if the UI order varies.
  * Re-registers the widget on showEvent (prevents lost registration when docks
    are hidden/restored).
  * Ensures the canvas container and widget use expanding size policies so the
    Matplotlib canvas receives a non-zero geometry.
  * Small defensive guards to avoid importing plot_manager at module import time
    (avoids circular import during app/module initialization).
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QEvent

# Import the backend widget (Matplotlib canvas)
from mathexlab.plotting.mpl_backend import PlotWidget


class PlotDock(QWidget):
    """
    Professional container for Matplotlib figures.

    Structure:
      [ optional top bar ]
      [ canvas container -> PlotWidget ]
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # 1. Main Layout (zero margins for edge-to-edge look)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # 2. Top Bar (placeholder for toolbar/controls)
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(0)  # hidden by default
        self.top_bar.setStyleSheet("background: #252526; border-bottom: 1px solid #333;")
        self.layout.addWidget(self.top_bar)

        # 3. Canvas container (ensures canvas gets expanding geometry)
        self.canvas_container = QFrame()
        self.canvas_container.setStyleSheet("background-color: #1e1e1e;")
        self.canvas_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Layout for the canvas container
        self.canvas_layout = QVBoxLayout(self.canvas_container)
        self.canvas_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas_layout.setSpacing(0)

        # 4. The actual Matplotlib widget
        self.canvas_widget = PlotWidget(parent=self.canvas_container)
        # ensure the widget will expand to fill the container
        self.canvas_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas_layout.addWidget(self.canvas_widget)

        # Add container to main layout
        self.layout.addWidget(self.canvas_container)

        # Attempt to register the widget with plot_manager now (defensive / non-fatal)
        try:
            # import here to avoid module-level circular imports
            from mathexlab.plotting.state import plot_manager
            plot_manager.set_widget(self.canvas_widget)
        except Exception:
            # non-fatal: app will register later when ready
            pass

    def showEvent(self, event):
        """
        Re-register the canvas widget with the plot manager when the dock becomes visible.
        This handles cases where docks are hidden/restored and the plot_manager lost the binding.
        """
        try:
            from mathexlab.plotting.state import plot_manager
            # Only re-register if it isn't already set
            if getattr(plot_manager, "widget", None) is not self.canvas_widget:
                plot_manager.set_widget(self.canvas_widget)
        except Exception:
            pass
        super().showEvent(event)

    def get_canvas(self):
        """Returns the internal PlotWidget for external use."""
        return self.canvas_widget

    def set_toolbar_visible(self, visible: bool):
        """Toggle the top toolbar area (keeps the top_bar placeholder in sync)."""
        h = 32 if visible else 0
        self.top_bar.setFixedHeight(h)
        # If the backend exposes a toolbar element, toggle it as well (defensive)
        try:
            tb = getattr(self.canvas_widget, "toolbar", None)
            if tb is not None:
                tb.setVisible(visible)
        except Exception:
            pass
