# mathexlab/ui/editor/scripteditor.py
from pathlib import Path
from PySide6.QtWidgets import QTabWidget, QFileDialog
from PySide6.QtCore import Qt

from .codeeditor import CodeEditor


class ScriptEditor(QTabWidget):
    """
    MATLAB-like multi-file M-editor:
    - Multiple tabs
    - New files
    - Close tabs
    - Get current filename + code
    """
    def __init__(self):
        super().__init__()

        self.setTabsClosable(True)
        self.setMovable(True)

        self.tabCloseRequested.connect(self.close_tab)

        self.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #333333; background: #1e1e1e; }
            QTabBar::tab {
                background: #2d2d2d;
                color: #cccccc;
                padding: 6px 20px;
                border-right: 1px solid #444;
            }
            QTabBar::tab:selected {
                background: #1e1e1e;
                border-bottom: 2px solid #007acc;
                color: white;
            }
            QTabBar::tab:hover { background: #383838; }
        """)

        self.new_file()

    def current_editor(self):
        """Returns the CodeEditor widget of the currently active tab."""
        return self.currentWidget()

    def new_file(self):
        editor = CodeEditor()
        # Attach a 'filename' attribute to the editor to track its save path
        editor.filename = None 
        idx = self.addTab(editor, "Untitled.m")
        self.setCurrentIndex(idx)
        editor.setFocus()

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "MATLAB Files (*.m);;All Files (*)"
        )
        if file_path:
            try:
                text = Path(file_path).read_text(encoding='utf-8')
                
                editor = CodeEditor()
                editor.setPlainText(text)
                editor.filename = file_path
                
                idx = self.addTab(editor, Path(file_path).name)
                self.setCurrentIndex(idx)
                editor.setFocus()
            except Exception as e:
                print(f"Error opening file: {e}")

    def save_current(self):
        editor = self.current_editor()
        if not editor:
            return

        # If we already have a filename, save directly; otherwise, "Save As"
        if getattr(editor, 'filename', None):
            self._save_to_path(editor, editor.filename)
        else:
            self.save_as()

    def save_as(self):
        editor = self.current_editor()
        if not editor:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "Untitled.m", "MATLAB Files (*.m);;All Files (*)"
        )
        if file_path:
            self._save_to_path(editor, file_path)
            editor.filename = file_path
            self.setTabText(self.currentIndex(), Path(file_path).name)

    def _save_to_path(self, editor, path):
        try:
            Path(path).write_text(editor.toPlainText(), encoding='utf-8')
        except Exception as e:
            print(f"Error saving file: {e}")

    def close_current(self):
        idx = self.currentIndex()
        if idx != -1:
            self.close_tab(idx)

    def close_tab(self, index):
        # Prevent closing the last tab if you want to keep at least one open
        if self.count() > 1:
            self.removeTab(index)
        else:
            # Optional: if they close the last tab, just clear it or make a new one
            self.removeTab(index)
            self.new_file()

    def get_current_code(self):
        editor = self.currentWidget()
        return editor.toPlainText() if editor else ""

    def get_current_filename(self):
        return self.tabText(self.currentIndex())
    
    def open_file_by_path(self, path_str):
        path = Path(path_str)
        if not path.exists(): return
        
        try:
            text = path.read_text(encoding='utf-8')
            editor = CodeEditor()
            editor.setPlainText(text)
            editor.filename = str(path)
            
            idx = self.addTab(editor, path.name)
            self.setCurrentIndex(idx)
            editor.setFocus()
        except Exception as e:
            print(f"Error opening file: {e}")

    def open_file_by_path(self, file_path):
        """Opens a specific file path directly without a dialog."""
        path = Path(file_path)
        if not path.exists():
            return

        # Check if already open
        for i in range(self.count()):
            editor = self.widget(i)
            if hasattr(editor, 'filename') and editor.filename == str(path):
                self.setCurrentIndex(i)
                return

        try:
            text = path.read_text(encoding='utf-8')
            
            editor = CodeEditor()
            editor.setPlainText(text)
            editor.filename = str(path)
            
            idx = self.addTab(editor, path.name)
            self.setCurrentIndex(idx)
            editor.setFocus()
        except Exception as e:
            print(f"Error opening file: {e}")