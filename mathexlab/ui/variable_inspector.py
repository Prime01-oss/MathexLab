from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableView, QHeaderView, QLabel
)
from PySide6.QtCore import Qt, Signal, QAbstractTableModel, QModelIndex
import numpy as np

class ArrayModel(QAbstractTableModel):
    """
    Virtual Model that allows displaying 1,000,000+ cells instantly.
    It reads directly from the numpy array without creating sub-objects.
    """
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=QModelIndex()):
        if self._data is None: return 0
        if self._data.ndim == 0: return 1
        return self._data.shape[0]

    def columnCount(self, parent=QModelIndex()):
        if self._data is None: return 0
        if self._data.ndim < 2: return 1
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid(): return None
        
        row, col = index.row(), index.column()

        if role == Qt.DisplayRole or role == Qt.EditRole:
            # Safe Access logic
            if self._data.ndim == 0:
                val = self._data[()]
            elif self._data.ndim == 1:
                val = self._data[row]
            else:
                val = self._data[row, col]
                
            # Formatting
            if isinstance(val, (float, np.floating)):
                return f"{val:.5f}"
            if isinstance(val, (complex, np.complexfloating)):
                return f"{val.real:.3f}+{val.imag:.3f}j"
            return str(val)
            
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or role != Qt.EditRole: return False
        
        row, col = index.row(), index.column()
        
        try:
            # Simple Type Inference
            if 'j' in value: new_val = complex(value)
            elif '.' in value: new_val = float(value)
            else: new_val = int(value)
            
            if self._data.ndim == 0:
                self._data[()] = new_val
            elif self._data.ndim == 1:
                self._data[row] = new_val
            else:
                self._data[row, col] = new_val
            
            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            return True
        except ValueError:
            return False

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            # MATLAB uses 1-based indexing for headers
            return str(section + 1)
        return None

class VariableInspector(QDialog):
    """
    High-Performance Variable Inspector (Virtual Mode).
    """
    value_changed = Signal(object)

    def __init__(self, name, value, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Variable Inspector: {name}")
        self.resize(700, 500)
        
        self.var_name = name
        
        # Unwrap MatlabArray/MathexLab types to get raw storage
        self.raw_data = value._data if hasattr(value, "_data") else value
        
        # Ensure NumPy array for the model
        if not isinstance(self.raw_data, np.ndarray):
            self.raw_data = np.array(self.raw_data)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        
        # Info Label
        self.info_label = QLabel()
        self.info_label.setStyleSheet("""
            background-color: #252526; 
            color: #888; 
            font-style: italic; 
            padding: 5px;
            border-bottom: 1px solid #333;
        """)
        self.layout.addWidget(self.info_label)

        # High-Performance Table View
        self.table = QTableView()
        self.table.setStyleSheet("""
            QTableView {
                background-color: #1e1e1e;
                color: #ffffff;
                gridline-color: #444;
                selection-background-color: #264f78;
                border: none;
            }
            QHeaderView::section {
                background-color: #2b2b2b;
                color: #ccc;
                padding: 4px;
                border: 1px solid #333;
            }
            QTableCornerButton::section {
                background-color: #2b2b2b;
                border: 1px solid #333;
            }
        """)
        self.layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        arr = self.raw_data
        
        # Handle Slicing for ND Arrays (Show first 2D slice)
        if arr.ndim > 2:
            extra_dims = arr.ndim - 2
            view_arr = arr
            # Peel dimensions until 2D
            for _ in range(extra_dims): view_arr = view_arr[..., 0]
            
            slice_desc = f"[:,:,{','.join(['0']*extra_dims)}]"
            self.info_label.setText(f" {slice_desc} of {arr.shape}")
            self.model = ArrayModel(view_arr)
        else:
            self.model = ArrayModel(arr)
            self.info_label.setText(f" Size: {arr.shape}")

        self.table.setModel(self.model)
        
        # Connect Edit Signal
        self.model.dataChanged.connect(self._on_data_changed)
    
    def _on_data_changed(self):
        # Notify workspace of changes
        # Since the model modifies the numpy array in-place, 
        # the original wrapper in the workspace is already updated.
        # We simply emit the signal to trigger any necessary refreshes.
        self.value_changed.emit(self.raw_data)