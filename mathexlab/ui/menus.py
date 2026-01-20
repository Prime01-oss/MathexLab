from PySide6.QtWidgets import QMenuBar, QMessageBox
from PySide6.QtGui import QAction
from PySide6.QtCore import QObject, Signal

# [NEW] Import the Guide Dialog
from .guide import GuideDialog

class MenuSignals(QObject):
    new_file = Signal()
    open_file = Signal()
    save_file = Signal()
    save_as = Signal()
    close_file = Signal()
    run_script = Signal()

    undo = Signal()
    redo = Signal()
    cut = Signal()
    copy = Signal()
    paste = Signal()
    select_all = Signal()

    # [FIX] Added toggle_files for Current Folder
    toggle_files = Signal(bool)
    toggle_console = Signal(bool)
    toggle_workspace = Signal(bool)
    toggle_plots = Signal(bool)

class MainMenuBar(QMenuBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # Keep reference for dialog parenting
        self.signals = MenuSignals()
        self.build_menus()

    def build_menus(self):
        # ---------- FILE ----------
        file_menu = self.addMenu("File")

        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.signals.new_file.emit)
        file_menu.addAction(new_action)

        open_action = QAction("Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.signals.open_file.emit)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.signals.save_file.emit)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As...", self)
        save_as_action.triggered.connect(self.signals.save_as.emit)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        close_action = QAction("Close File", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.signals.close_file.emit)
        file_menu.addAction(close_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.parent().close)
        file_menu.addAction(exit_action)

        # ---------- EDIT ----------
        edit_menu = self.addMenu("Edit")

        undo = QAction("Undo", self)
        undo.setShortcut("Ctrl+Z")
        undo.triggered.connect(self.signals.undo.emit)
        edit_menu.addAction(undo)

        redo = QAction("Redo", self)
        redo.setShortcut("Ctrl+Y")
        redo.triggered.connect(self.signals.redo.emit)
        edit_menu.addAction(redo)

        edit_menu.addSeparator()

        cut = QAction("Cut", self)
        cut.setShortcut("Ctrl+X")
        cut.triggered.connect(self.signals.cut.emit)
        edit_menu.addAction(cut)

        copy = QAction("Copy", self)
        copy.setShortcut("Ctrl+C")
        copy.triggered.connect(self.signals.copy.emit)
        edit_menu.addAction(copy)

        paste = QAction("Paste", self)
        paste.setShortcut("Ctrl+V")
        paste.triggered.connect(self.signals.paste.emit)
        edit_menu.addAction(paste)

        select_all = QAction("Select All", self)
        select_all.setShortcut("Ctrl+A")
        select_all.triggered.connect(self.signals.select_all.emit)
        edit_menu.addAction(select_all)

        # ---------- VIEW ----------
        view_menu = self.addMenu("View")

        # [FIX] Added Current Folder Action
        self.files_action = QAction("Current Folder", self, checkable=True, checked=True)
        self.files_action.triggered.connect(lambda c: self.signals.toggle_files.emit(c))
        view_menu.addAction(self.files_action)

        self.console_action = QAction("Command Window", self, checkable=True, checked=True)
        self.console_action.triggered.connect(lambda c: self.signals.toggle_console.emit(c))
        view_menu.addAction(self.console_action)

        self.workspace_action = QAction("Workspace", self, checkable=True, checked=True)
        self.workspace_action.triggered.connect(lambda c: self.signals.toggle_workspace.emit(c))
        view_menu.addAction(self.workspace_action)

        self.plot_action = QAction("Figures", self, checkable=True, checked=True)
        self.plot_action.triggered.connect(lambda c: self.signals.toggle_plots.emit(c))
        view_menu.addAction(self.plot_action)

        # ---------- RUN ----------
        run_menu = self.addMenu("Run")

        run_script = QAction("Run Script", self)
        run_script.setShortcut("F5")
        run_script.triggered.connect(self.signals.run_script.emit)
        run_menu.addAction(run_script)

        # ---------- HELP ----------
        help_menu = self.addMenu("Help")
        
        # [NEW] User Guide Action
        guide_act = QAction("User Guide", self)
        guide_act.setShortcut("F1")
        guide_act.triggered.connect(self._show_guide)
        help_menu.addAction(guide_act)
        
        help_menu.addSeparator()
        
        help_action = QAction("About MathexLab", self)
        help_action.triggered.connect(self._show_about)
        help_menu.addAction(help_action)

    # [NEW] Helper to show the guide
    def _show_guide(self):
        try:
            dialog = GuideDialog(self.parent_window)
            dialog.exec()
        except Exception as e:
            print(f"Error launching guide: {e}")

    def _show_about(self):
        QMessageBox.about(
            self, 
            "About MathexLab",
            "<h3>MathexLab Environment</h3>"
            "<p>A professional, MATLAB-compatible Python IDE.</p>"
            "<p><b>Version:</b> 0.1.0-Alpha</p>"
            "<p>Built with PySide6 & NumPy.</p>"
            "<p>Author: <b>Samarjit Patar</b></p>"
        )