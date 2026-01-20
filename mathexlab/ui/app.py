import sys
import os
import ctypes
import time
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QApplication, QLabel, QWidget,
    QHBoxLayout, QPushButton, QStyle
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QTimer, QSettings, QSize  # [FIX] Added QSize

# --- MathexLab Internal Imports ---
from mathexlab.kernel.session import KernelSession
from mathexlab.plotting.state import plot_manager
from mathexlab.plotting.engine import PlotEngine
from mathexlab.plotting.figure import init_ui_widget
from mathexlab.ui.kernel_worker import start_kernel_worker

# --- UI Components ---
from .console import ConsoleWidget
from .editor import ScriptEditor
from .plotdock import PlotDock
from .workspace import WorkspaceWidget
from .menus import MainMenuBar
from .filebrowser import FileBrowser


NON_TIMED_COMMANDS = {
    "clc",
    "clf",
    "clear",
    "clear all",
    "close",
    "close all",
    "who",
    "whos",
    "format",
}

class DockTitleBar(QWidget):
    def __init__(self, dock: QDockWidget, title: str):
        super().__init__(dock)
        self.dock = dock
        self._is_fullscreen = False
        self._normal_geometry = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #cccccc; font-weight: bold;")
        layout.addWidget(title_label)

        layout.addStretch(1)

        # Fullscreen button (NEW)
        BTN_SIZE = 14
        BTN_STYLE = """
            QPushButton {
                border: none;
                background: transparent;
                color: #9e9e9e;
                font-size: 11px;
                padding: 0px;
            }
            QPushButton:hover {
                color: #d4d4d4;
            }
        """

        # Fullscreen button
        fs_btn = QPushButton("⛶")
        fs_btn.setFixedSize(BTN_SIZE, BTN_SIZE)
        fs_btn.setToolTip("Fullscreen")
        fs_btn.setStyleSheet(BTN_STYLE)
        fs_btn.clicked.connect(self._toggle_fullscreen)
        layout.addWidget(fs_btn)

        # Float / Dock button
        float_btn = QPushButton()
        float_btn.setIcon(dock.style().standardIcon(QStyle.SP_TitleBarNormalButton))
        float_btn.setIconSize(QSize(12, 12))  # [FIX] Removed Qt. prefix
        float_btn.setFixedSize(BTN_SIZE, BTN_SIZE)
        float_btn.setStyleSheet(BTN_STYLE)
        float_btn.clicked.connect(lambda: dock.setFloating(not dock.isFloating()))
        layout.addWidget(float_btn)

        # Close button
        close_btn = QPushButton()
        close_btn.setIcon(dock.style().standardIcon(QStyle.SP_TitleBarCloseButton))
        close_btn.setIconSize(QSize(12, 12))  # [FIX] Removed Qt. prefix
        close_btn.setFixedSize(BTN_SIZE, BTN_SIZE)
        close_btn.setStyleSheet(BTN_STYLE)
        close_btn.clicked.connect(dock.close)
        layout.addWidget(close_btn)


    def _toggle_fullscreen(self):
        if not self._is_fullscreen:
            self._normal_geometry = self.dock.saveGeometry()
            self.dock.setFloating(True)
            self.dock.showFullScreen()
            self._is_fullscreen = True
        else:
            self.dock.showNormal()
            self.dock.setFloating(False)
            if self._normal_geometry:
                self.dock.restoreGeometry(self._normal_geometry)
            self._is_fullscreen = False


class MathexLabApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("MathexLab", "IDE")
        PlotEngine.initialize("ui")

        self.setWindowTitle("MathexLab Environment")
        self.resize(1400, 900)

        self._set_window_icon()

        # --------------------------------------------------
        # Global Styling
        # --------------------------------------------------
        self.setStyleSheet("""
            QMainWindow { background-color: #1A1A1A; }

            QDockWidget { color: #cccccc; border: 1px solid #333333; }
            QDockWidget::title { background: #252526; padding: 6px; font-weight: bold; }

            QStatusBar {
                background: #1A1A1A;
                color: #cccccc;
                border-top: 1px solid #121212;
            }

            QStatusBar::item {
                border: none;
            }

            QLabel {
                padding: 0;
                margin: 0;
                background: transparent;
            }
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
        self.plotdock_dock.setTitleBarWidget(
            DockTitleBar(self.plotdock_dock, "Figures")
        )


        # --------------------------------------------------
        # SESSION RESTORE (Paths & Editor Files)
        # --------------------------------------------------
        
        # 1. Restore Current Folder
        last_path = self.settings.value("last_path", "")
        if last_path:
            self.file_browser.set_path(last_path)

        # 2. Restore Open Editor Files
        open_files = self.settings.value("open_files", [])
        if open_files:
            # If we have saved files, clear the default "Untitled" tab first
            # but only if we are actually going to open something.
            # Using loop to open them.
            
            # (Optional) Close the default tab if it's empty/untitled
            if self.editor.count() == 1:
                current = self.editor.current_editor()
                if not getattr(current, 'filename', None) and not current.toPlainText().strip():
                     self.editor.close_tab(0)

            for fpath in open_files:
                self.editor.open_file_by_path(fpath)

            # Restore active tab index
            last_idx = self.settings.value("active_tab", 0)
            if last_idx:
                self.editor.setCurrentIndex(int(last_idx))

        # --------------------------------------------------
        # Signals
        # --------------------------------------------------
        self.console.command_entered.connect(self._run_code_from_console)
        self.file_browser.file_open_requested.connect(self.editor.open_file_by_path)

        self.workspace.clear_requested.connect(self._clear_workspace)
        self.workspace.save_requested.connect(self._save_workspace)
        self.workspace.load_requested.connect(self._load_workspace)
        self.workspace.variable_edited.connect(self._sync_variable_to_kernel)

        self.menu = MainMenuBar(self)
        self.setMenuBar(self.menu)
        self._attach_menu_signals()

        self.files_dock.visibilityChanged.connect(lambda v: self._sync_dock_menu(self.menu.files_action, v))
        self.console_dock.visibilityChanged.connect(lambda v: self._sync_dock_menu(self.menu.console_action, v))
        self.workspace_dock.visibilityChanged.connect(lambda v: self._sync_dock_menu(self.menu.workspace_action, v))
        self.plotdock_dock.visibilityChanged.connect(lambda v: self._sync_dock_menu(self.menu.plot_action, v))

        # --------------------------------------------------
        # Initialization & Status Bar
        # --------------------------------------------------
        self.console.initialize("MathexLab Ready.")

        # 1. Status Message (Left)
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #98c379; font-weight: bold;")
        self.statusBar().addWidget(self.status_label, 1)

        # Kernel state LED
        self.kernel_led = QLabel("●")
        self.kernel_led.setStyleSheet("color: #98c379;")
        self.statusBar().addWidget(self.kernel_led)

        # Execution time
        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color: #61afef;")
        self.statusBar().addPermanentWidget(self.time_label)

        # Selection length
        self.selection_label = QLabel("")
        self.selection_label.setStyleSheet("color: #c678dd;")
        self.statusBar().addPermanentWidget(self.selection_label)

        # Insert / Overwrite mode
        self.mode_label = QLabel("INS")
        self.mode_label.setStyleSheet("color: #aaaaaa; font-weight: bold;")
        self.statusBar().addPermanentWidget(self.mode_label)

        # 2. Cursor Position (Right)
        self.cursor_label = QLabel("Ln 1, Col 1")
        self.cursor_label.setStyleSheet("""
            color: #aaaaaa;
            background: transparent;
            padding: 0;
            margin: 0;
        """)
        self.statusBar().addPermanentWidget(self.cursor_label)

        # 3. Error Count (Far Right)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e06c75;")
        self.statusBar().addPermanentWidget(self.error_label)

        self._last_connected_editor = None

        self.editor.currentChanged.connect(self._update_cursor_connection)
        self._update_cursor_connection()

        self._kernel_thread = None
        self._kernel_worker = None
        self._busy = False
        self._error_count = 0
        self._exec_start = None

        self._plot_timer = QTimer(self)
        self._plot_timer.timeout.connect(PlotEngine.tick)
        self._plot_timer.start(16)

    # --------------------------------------------------
    # FIX: Helper method moved INSIDE the class
    # --------------------------------------------------
    def _is_non_timed_code(self, code: str) -> bool:
        """
        Returns True if the code contains only housekeeping commands
        that should not be timed.
        """
        lines = [
            line.strip().lower()
            for line in code.splitlines()
            if line.strip() and not line.strip().startswith("%")
        ]

        if not lines:
            return True

        return all(line in NON_TIMED_COMMANDS for line in lines)

    # --------------------------------------------------
    # Cursor Tracking
    # --------------------------------------------------
    def _update_cursor_connection(self):
        new_editor = self.editor.current_editor()
        old_editor = self._last_connected_editor

        if old_editor and old_editor != new_editor:
            try:
                old_editor.cursorPositionChanged.disconnect(self._update_cursor_info)
            except Exception:
                pass

        if new_editor:
            if new_editor != old_editor:
                try:
                    new_editor.cursorPositionChanged.connect(self._update_cursor_info)
                except Exception:
                    pass
            self._update_cursor_info()
        else:
            self.cursor_label.setText("")

        self._last_connected_editor = new_editor

    def _update_cursor_info(self):
        editor = self.editor.current_editor()
        if editor:
            cursor = editor.textCursor()
            ln = cursor.blockNumber() + 1
            col = cursor.columnNumber() + 1
            self.cursor_label.setText(f"Ln {ln}, Col {col}")
            # Insert / Overwrite mode
            self.mode_label.setText("OVR" if editor.overwriteMode() else "INS")

            # Selection length
            if cursor.hasSelection():
                text = cursor.selectedText()
                lines = text.count('\u2029') + 1
                chars = len(text)
                self.selection_label.setText(f"Sel {lines}x{chars}")
            else:
                self.selection_label.setText("")

    # --------------------------------------------------
    # Window Icon
    # --------------------------------------------------
    def _set_window_icon(self):
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

    # --------------------------------------------------
    # Menu Actions
    # --------------------------------------------------
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

    # --------------------------------------------------
    # Execution
    # --------------------------------------------------
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

    # --------------------------------------------------
    # FIX: Robust _run_code with Try/Except Safety Net
    # --------------------------------------------------
    def _run_code(self, code: str, task_name: str = "Code"):
        if self._busy:
            self.console.write_error("Kernel busy. Please wait.")
            return
        if not code.strip():
            self.console.execution_finished()
            return

        # Lock the UI
        self._busy = True

        try:
            self._exec_start = None
            # Now we can safely call the method because it's inside the class
            if not self._is_non_timed_code(code):
                self._exec_start = time.perf_counter()

            self.kernel_led.setStyleSheet("color: #e06c75;")
            self.time_label.setText("")

            self.console.busy = True
            self._error_count = 0
            self.error_label.setText("")

            self.status_label.setStyleSheet("color: #e06c75; font-weight: bold;")
            self.status_label.setText(f"Busy: Running '{task_name}'...")

            self._kernel_thread, self._kernel_worker = start_kernel_worker(
                self.session, code,
                on_output=self.console.write_output,
                on_error=self._on_kernel_error,
                on_finished=self._on_execution_finished,
            )

        except Exception as e:
            # SAFETY NET: Reset busy state if setup fails
            self._busy = False
            self.console.busy = False
            self.console.write_error(f"IDE Error (Execution Setup): {e}")
            self.status_label.setText("Ready (Error)")
            self.kernel_led.setStyleSheet("color: #e06c75;")

    def _on_kernel_error(self, error_msg):
        self._error_count += 1
        self.error_label.setText(f"Errors: {self._error_count}")
        self.console.write_error(error_msg)
        self.workspace.update_table(self.session.globals)

    def _on_execution_finished(self):
        if self._exec_start is not None:
            elapsed = time.perf_counter() - self._exec_start
            self.time_label.setText(f"{elapsed:.3f} s")
        else:
            self.time_label.setText("")

        self.workspace.update_table(self.session.globals)
        self.console.execution_finished()
        self.console.busy = False

        try:
            w = plot_manager.widget
            if w:
                w.render(immediate=True)
        except Exception:
            pass

        self._busy = False

        if self._error_count > 0:
            self.kernel_led.setStyleSheet("color: #e5c07b;")
            self.status_label.setStyleSheet("color: #e06c75; font-weight: bold;")
            self.status_label.setText("Finished with errors.")
        else:
            self.kernel_led.setStyleSheet("color: #98c379;")
            self.status_label.setStyleSheet("color: #98c379; font-weight: bold;")
            self.status_label.setText("Ready")
            self.error_label.setText("")

    # --------------------------------------------------
    # Workspace
    # --------------------------------------------------
    def _sync_variable_to_kernel(self, name, value):
        self.session.globals[name] = value

    def _clear_workspace(self):
        self.session._clear_user()
        self.workspace.update_table(self.session.globals)
        self.console.write_output("Workspace cleared.")

    def _save_workspace(self):
        self.console.write_info("Workspace saving is coming in the next update!")

    def _load_workspace(self):
        self.console.write_info("Workspace loading is coming in the next update!")

    # --------------------------------------------------
    # Shutdown (Save State)
    # --------------------------------------------------
    def closeEvent(self, event):
        # 1. Save Current Folder
        if hasattr(self.file_browser, 'current_path'):
            self.settings.setValue("last_path", self.file_browser.current_path)
            
        # 2. Save Open Files (Session Restore)
        if hasattr(self.editor, 'get_open_filepaths'):
            open_files = self.editor.get_open_filepaths()
            self.settings.setValue("open_files", open_files)
            self.settings.setValue("active_tab", self.editor.currentIndex())
            
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