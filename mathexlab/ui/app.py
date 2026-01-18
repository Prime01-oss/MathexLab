import sys
import os
import ctypes
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QApplication, QLabel
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QTimer, QSettings

from mathexlab.kernel.session import KernelSession
from mathexlab.plotting.state import plot_manager
from mathexlab.plotting.engine import PlotEngine
from mathexlab.plotting.figure import init_ui_widget
from mathexlab.ui.kernel_worker import start_kernel_worker

# UI Components
from .console import ConsoleWidget
from .editor import ScriptEditor
from .plotdock import PlotDock
from .workspace import WorkspaceWidget
from .menus import MainMenuBar
from .filebrowser import FileBrowser

class MathexLabApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.settings = QSettings("MathexLab", "IDE")
        PlotEngine.initialize("ui")

        self.setWindowTitle("MathexLab Environment")
        self.resize(1400, 900)

        self._set_window_icon()

        # Status Bar Styling
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QDockWidget { color: #cccccc; border: 1px solid #333333; }
            QDockWidget::title { background: #252526; padding: 6px; font-weight: bold; }
            QStatusBar { 
                background: #2d2d2d; 
                color: #cccccc; 
                border-top: 1px solid #3e3e42;
            }
            QLabel { padding: 0 5px; }
        """)

        # --------------------------------------------------
        # Kernel & UI
        # --------------------------------------------------
        self.session = KernelSession()

        self.editor = ScriptEditor()
        self.console = ConsoleWidget()
        self.workspace = WorkspaceWidget()
        self.plot_dock = PlotDock()
        self.file_browser = FileBrowser()

        pw = self.plot_dock.get_canvas()
        init_ui_widget(pw)

        # --------------------------------------------------
        # Layout
        # --------------------------------------------------
        self.setCentralWidget(self.editor)
        
        self.files_dock = self._add_dock("Current Folder", self.file_browser, Qt.LeftDockWidgetArea)
        self.console_dock = self._add_dock("Command Window", self.console, Qt.BottomDockWidgetArea)
        self.workspace_dock = self._add_dock("Workspace", self.workspace, Qt.RightDockWidgetArea)
        self.plotdock_dock = self._add_dock("Figures", self.plot_dock, Qt.RightDockWidgetArea)

        # Restore Path
        last_path = self.settings.value("last_path", "")
        if last_path:
            self.file_browser.set_path(last_path)

        # --------------------------------------------------
        # Signals
        # --------------------------------------------------
        self.console.command_entered.connect(self._run_code_from_console)
        self.file_browser.file_open_requested.connect(self.editor.open_file_by_path)

        self.workspace.clear_requested.connect(self._clear_workspace)
        self.workspace.save_requested.connect(self._save_workspace)
        self.workspace.load_requested.connect(self._load_workspace)
        
        # [NEW] SYNC WORKSPACE EDITS TO KERNEL
        self.workspace.variable_edited.connect(self._sync_variable_to_kernel)

        self.menu = MainMenuBar(self)
        self.setMenuBar(self.menu)
        self._attach_menu_signals()

        # Dock <-> Menu Sync
        self.files_dock.visibilityChanged.connect(lambda v: self._sync_dock_menu(self.menu.files_action, v))
        self.console_dock.visibilityChanged.connect(lambda v: self._sync_dock_menu(self.menu.console_action, v))
        self.workspace_dock.visibilityChanged.connect(lambda v: self._sync_dock_menu(self.menu.workspace_action, v))
        self.plotdock_dock.visibilityChanged.connect(lambda v: self._sync_dock_menu(self.menu.plot_action, v))

        # --------------------------------------------------
        # Initialization
        # --------------------------------------------------
        self.console.initialize("MathexLab Ready.")
        
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label, 1)
        
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff5555;")
        self.statusBar().addPermanentWidget(self.error_label)

        self._kernel_thread = None
        self._kernel_worker = None
        self._busy = False
        self._error_count = 0

        self._plot_timer = QTimer(self)
        self._plot_timer.timeout.connect(PlotEngine.tick)
        self._plot_timer.start(16)

    def _set_window_icon(self):
        """Finds and sets icon.ico for the Window Titlebar"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        paths = [
            os.path.join(base_dir, 'resources', 'icon.ico'), 
            os.path.join(base_dir, '..', 'resources', 'icon.ico'),
            os.path.join("icon.ico")
        ]
        for p in paths:
            if os.path.exists(p):
                self.setWindowIcon(QIcon(p))
                return

    def createPopupMenu(self):
        return None

    def _add_dock(self, title, widget, area):
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        self.addDockWidget(area, dock)
        return dock

    def _sync_dock_menu(self, action, visible):
        action.blockSignals(True)
        action.setChecked(visible)
        action.blockSignals(False)

    def _attach_menu_signals(self):
        m = self.menu.signals
        m.new_file.connect(self.editor.new_file)
        m.open_file.connect(self.editor.open_file)
        m.save_file.connect(self.editor.save_current)
        m.save_as.connect(self.editor.save_as)
        m.close_file.connect(self.editor.close_current)
        
        m.undo.connect(lambda: self.editor.current_editor().undo())
        m.redo.connect(lambda: self.editor.current_editor().redo())
        m.cut.connect(lambda: self.editor.current_editor().cut())
        m.copy.connect(lambda: self.editor.current_editor().copy())
        m.paste.connect(lambda: self.editor.current_editor().paste())
        m.select_all.connect(lambda: self.editor.current_editor().selectAll())

        m.toggle_files.connect(lambda v: self.files_dock.setVisible(v))
        m.toggle_console.connect(lambda v: self.console_dock.setVisible(v))
        m.toggle_workspace.connect(lambda v: self.workspace_dock.setVisible(v))
        m.toggle_plots.connect(lambda v: self.plotdock_dock.setVisible(v))

        m.run_script.connect(self._run_script)

    def _run_code_from_console(self, code):
        self._run_code(code, task_name="Console Command")

    def _run_script(self):
        code = self.editor.get_current_code()
        filepath = self.editor.get_current_filename()
        if not code.strip():
            self.console.write_error("Nothing to execute.")
            return
        fname = os.path.basename(filepath) if filepath else "Untitled"
        self.console.write_output(f"--- Running: {fname} ---")
        self._run_code(code, task_name=fname)

    def _run_code(self, code: str, task_name: str = "Code"):
        if self._busy:
            self.console.write_error("Kernel busy. Please wait.")
            return
        if not code.strip():
            self.console.execution_finished()
            return
        self._busy = True
        self.console.busy = True
        self._error_count = 0
        self.error_label.setText("")
        self.status_label.setText(f"Busy: Running '{task_name}'...")
        self._kernel_thread, self._kernel_worker = start_kernel_worker(
            self.session, code,
            on_output=self.console.write_output,
            on_error=self._on_kernel_error,
            on_finished=self._on_execution_finished,
        )

    def _on_kernel_error(self, error_msg):
        self._error_count += 1
        self.error_label.setText(f"Errors: {self._error_count}")
        self.console.write_error(error_msg)

    def _on_execution_finished(self):
        self.workspace.update_table(self.session.globals)
        self.console.execution_finished()
        self.console.busy = False
        try:
            w = plot_manager.widget
            if w: w.render(immediate=True)
        except Exception:
            pass
        self._busy = False
        if self._error_count > 0:
            self.status_label.setText("Finished with errors.")
        else:
            self.status_label.setText("Ready")
            self.error_label.setText("")

    # [NEW] SYNC METHOD
    def _sync_variable_to_kernel(self, name, value):
        """Called when Workspace reports a variable edit."""
        # Directly update the kernel session's global dictionary
        self.session.globals[name] = value

    def _clear_workspace(self):
        self.session._clear_user()
        self.workspace.update_table(self.session.globals)
        self.console.write_output("Workspace cleared.")

    def _save_workspace(self):
        self.console.write_info("Workspace saving is coming in the next update!")

    def _load_workspace(self):
        self.console.write_info("Workspace loading is coming in the next update!")

    def closeEvent(self, event):
        if hasattr(self.file_browser, 'current_path'):
            self.settings.setValue("last_path", self.file_browser.current_path)
        try:
            PlotEngine.shutdown()
        except Exception:
            pass
        event.accept()

def run():
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    if os.name == 'nt':
        myappid = 'mathexlab.ide.1.0.0'
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    app = QApplication(sys.argv)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_paths = [
        os.path.join(base_dir, 'resources', 'logo.png'),
        os.path.join(base_dir, '..', 'resources', 'logo.png'),
        os.path.join("logo.png")
    ]
    
    found_logo = False
    for p in logo_paths:
        if os.path.exists(p):
            app.setWindowIcon(QIcon(p))
            found_logo = True
            break
            
    if not found_logo:
        print("[MathexLab] Warning: logo.png not found.")

    win = MathexLabApp()
    win.show()
    sys.exit(app.exec())