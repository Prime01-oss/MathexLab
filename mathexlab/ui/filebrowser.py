# mathexlab/ui/filebrowser.py
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, 
    QLineEdit, QToolButton, QFileSystemModel, QFileDialog,
    QHeaderView
)
from PySide6.QtCore import Qt, QDir, Signal

class FileBrowser(QWidget):
    """
    MATLAB-style 'Current Folder' browser.
    Features:
    - Address Bar (Editable)
    - Up / Browse Buttons
    - File Tree (Double click folder -> enter, Double click file -> open)
    """
    
    file_open_requested = Signal(str)  # Emitted when a file is double-clicked
    path_changed = Signal(str)         # Emitted when CWD changes

    def __init__(self):
        super().__init__()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # --------------------------------------------------
        # 1. Navigation Bar (Address Bar)
        # --------------------------------------------------
        self.nav_bar = QWidget()
        self.nav_bar.setStyleSheet("background: #252526; border-bottom: 1px solid #333;")
        nav_layout = QHBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(2, 2, 2, 2)
        nav_layout.setSpacing(2)

        # "Up" Button
        self.btn_up = QToolButton()
        self.btn_up.setText("↑")
        self.btn_up.setToolTip("Up One Level")
        self.btn_up.clicked.connect(self.go_up)
        nav_layout.addWidget(self.btn_up)

        # Address Input
        self.address_bar = QLineEdit()
        self.address_bar.setStyleSheet("""
            QLineEdit { background: #333; color: #ccc; border: 1px solid #3e3e42; }
        """)
        self.address_bar.returnPressed.connect(lambda: self.set_path(self.address_bar.text()))
        nav_layout.addWidget(self.address_bar)

        # "Browse" Button
        self.btn_browse = QToolButton()
        self.btn_browse.setText("...")
        self.btn_browse.setToolTip("Browse Folder")
        self.btn_browse.clicked.connect(self.browse_folder)
        nav_layout.addWidget(self.btn_browse)

        self.layout.addWidget(self.nav_bar)

        # --------------------------------------------------
        # 2. File Tree
        # --------------------------------------------------
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        # Filter: Show only relevant coding files
        self.model.setNameFilters(["*.m", "*.py", "*.txt", "*.mat", "*.json"])
        self.model.setNameFilterDisables(False)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(os.getcwd()))
        
        # Hide Size/Type/Date columns to look like MATLAB's default docked view
        self.tree.hideColumn(1) # Size
        self.tree.hideColumn(2) # Type
        self.tree.hideColumn(3) # Date
        self.tree.setHeaderHidden(True)
        
        self.tree.setStyleSheet("""
            QTreeView { background: #1e1e1e; color: #cccccc; border: none; }
            QTreeView::item:hover { background: #2a2d2e; }
            QTreeView::item:selected { background: #094771; color: white; }
        """)
        
        self.tree.doubleClicked.connect(self._on_item_double_clicked)
        self.layout.addWidget(self.tree)

        # Init
        self.set_path(os.getcwd())

    def set_path(self, path):
        if os.path.exists(path) and os.path.isdir(path):
            self.current_path = path
            self.address_bar.setText(path)
            self.tree.setRootIndex(self.model.index(path))
            os.chdir(path) # Actually change Python's working dir
            self.path_changed.emit(path)

    def go_up(self):
        parent = os.path.dirname(self.current_path)
        self.set_path(parent)

    def browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Folder", self.current_path)
        if path:
            self.set_path(path)

    def _on_item_double_clicked(self, index):
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self.set_path(path)
        else:
            self.file_open_requested.emit(path)