# mathexlab/ui/variable_inspector.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
)
from PySide6.QtCore import Qt, Signal  # [FIX] Added Signal
from PySide6.QtGui import QColor
import numpy as np


class VariableInspector(QDialog):
    """
    Shows the contents of a workspace variable in a grid (MATLAB-like).
    Supports editing values.
    """
    
    # [NEW] Signal to notify parent that the variable has been modified
    value_changed = Signal(object)

    def __init__(self, name, value, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Variable Inspector: {name}")
        self.resize(650, 450)
        
        # Keep references to source data for editing
        self.var_name = name
        self.var_value = value 
        self._is_loading = False # Prevent update loops

        layout = QVBoxLayout(self)
        
        # Info Label for Slicing Status
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #888; font-style: italic; margin-bottom: 4px;")
        layout.addWidget(self.info_label)

        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                gridline-color: #555;
                selection-background-color: #264f78;
                selection-color: white;
            }
            QHeaderView::section {
                background-color: #2b2b2b;
                color: #cccccc;
                padding: 4px;
            }
        """)
        layout.addWidget(self.table)
        
        # Connect edit signal
        self.table.itemChanged.connect(self._on_item_changed)

        self.load_data(value)

    def load_data(self, value):
        self._is_loading = True # Block signals while loading
        self.info_label.setText("") # Reset label
        
        # Unwrap MatlabArray if present
        if hasattr(value, "_data"):
            data = value._data
        else:
            data = value

        # Convert to numpy array when possible for display logic
        try:
            arr = np.array(data)
        except Exception:
            arr = None

        # CASE 1: Scalar or None
        if arr is None or np.isscalar(arr) or arr.ndim == 0:
            self.table.setRowCount(1)
            self.table.setColumnCount(1)
            self.table.setHorizontalHeaderLabels(["Value"])
            self.table.setVerticalHeaderLabels(["1"])
            self._set_item(0, 0, data)
            self._is_loading = False
            return

        # CASE 2: 1D Vector
        if arr.ndim == 1:
            n = len(arr)
            self.table.setRowCount(n)
            self.table.setColumnCount(1)
            self.table.setHorizontalHeaderLabels(["Value"])
            self.table.setVerticalHeaderLabels([str(i + 1) for i in range(n)])
            for i, v in enumerate(arr):
                self._set_item(i, 0, v)

        # CASE 3: 2D Matrix
        elif arr.ndim == 2:
            rows, cols = arr.shape
            self.table.setRowCount(rows)
            self.table.setColumnCount(cols)
            self.table.setHorizontalHeaderLabels([str(i + 1) for i in range(cols)])
            self.table.setVerticalHeaderLabels([str(i + 1) for i in range(rows)])
            for r in range(rows):
                for c in range(cols):
                    self._set_item(r, c, arr[r, c])

        # CASE 4: ND Arrays (Slice View)
        else:
            # We will show the first 2D slice: arr[:, :, 0, 0...]
            view_arr = arr
            
            # Peel layers until we have 2D
            extra_dims_count = arr.ndim - 2
            for _ in range(extra_dims_count):
                if view_arr.ndim > 2:
                    view_arr = view_arr[..., 0] 

            # Double check we are down to 2D
            while view_arr.ndim > 2:
                view_arr = view_arr[0]
            
            # Update Info Label
            slice_desc = f"[:,:,{','.join(['0']*extra_dims_count)}]"
            self.info_label.setText(f"Showing slice {slice_desc} of {arr.shape} array. Read-only view.")
            self.setWindowTitle(f"Variable Inspector: {self.var_name} (Slice View)")

            rows, cols = view_arr.shape
            self.table.setRowCount(rows)
            self.table.setColumnCount(cols)
            self.table.setHorizontalHeaderLabels([str(i + 1) for i in range(cols)])
            self.table.setVerticalHeaderLabels([str(i + 1) for i in range(rows)])
            
            for r in range(rows):
                for c in range(cols):
                    item = QTableWidgetItem(self.format_val(view_arr[r, c]))
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable) 
                    self.table.setItem(r, c, item)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._is_loading = False

    def _set_item(self, r, c, val):
        """Helper to set item and enable editing."""
        item = QTableWidgetItem(self.format_val(val))
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.table.setItem(r, c, item)

    def format_val(self, v):
        if isinstance(v, (float, np.floating)):
            return f"{v:.6f}"
        return str(v)

    def _on_item_changed(self, item):
        """Handle user edits."""
        if self._is_loading: return
        
        row = item.row()
        col = item.column()
        text = item.text()
        
        # 1. Parse Input
        try:
            if 'j' in text: new_val = complex(text)
            elif '.' in text: new_val = float(text)
            else: new_val = int(text)
        except ValueError:
            return # Ignore invalid input

        # 2. Update Source Data
        target = self.var_value
        updated = False

        if hasattr(target, "_data"):
            # Update MatlabArray data
            d = target._data
            if np.isscalar(d) or (isinstance(d, np.ndarray) and d.ndim == 0):
                # Wrapped Scalar: We update the internal data if possible, or replace
                if isinstance(d, np.ndarray):
                    d[()] = new_val # Update 0-d array in place
                    updated = True
                else:
                    # Immutable python type inside wrapper -> Must update wrapper
                    target._data = new_val
                    updated = True
            elif d.ndim == 1:
                d[row] = new_val
                updated = True
            elif d.ndim == 2:
                d[row, col] = new_val
                updated = True
        elif isinstance(target, np.ndarray):
            # Pure Numpy Array
            if target.ndim == 1:
                target[row] = new_val
                updated = True
            elif target.ndim == 2:
                target[row, col] = new_val
                updated = True
        else:
            # Pure Python Scalar (int/float/complex)
            # These are immutable, so we must replace 'self.var_value' entirely
            self.var_value = new_val
            updated = True
        
        # 3. Emit Signal to Workspace
        if updated:
            self.value_changed.emit(self.var_value)