from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QPushButton,
    QHBoxLayout, QLabel
)
from PySide6.QtCore import Qt


class GuideDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("MathexLab User Guide")
        self.resize(800, 600)

        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QTextBrowser {
                background-color: #252526;
                color: #e0e0e0;
                border: 1px solid #3e3e42;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1177bb; }
            QPushButton:pressed { background-color: #094771; }

            QScrollBar:vertical {
                background: #1e1e1e;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 20px;
                border-radius: 5px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QHBoxLayout()
        title = QLabel("MathexLab Documentation")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #61afef;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setHtml(self._content())
        layout.addWidget(self.browser)

        footer = QHBoxLayout()
        footer.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)

        layout.addLayout(footer)

    def _content(self):
        return """
<!DOCTYPE html>
<html>
<head>
<style>
body {
    color: #d4d4d4;
    font-family: 'Segoe UI', sans-serif;
    line-height: 1.6;
}
h2 {
    color: #98c379;
    border-bottom: 1px solid #3e3e42;
    padding-bottom: 5px;
    margin-top: 20px;
}
h3 { color: #e5c07b; }
code {
    background-color: #3e3e42;
    padding: 2px 5px;
    border-radius: 3px;
    font-family: Consolas, monospace;
    color: #dcdcaa;
}
.shortcut {
    background-color: #0e639c;
    color: white;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 0.9em;
    font-weight: bold;
}
</style>
</head>

<body>

<h2>Overview</h2>
<p>
MathexLab is a scientific computing environment designed for compatibility
with MATLAB-style scripting. It features a fast kernel, live workspace,
and an advanced plotting system.
</p>

<h2>User Interface</h2>
<ul>
<li><b>Editor:</b> Write and edit <code>.m</code> scripts.</li>
<li><b>File Browser:</b> Navigate project files.</li>
<li><b>Workspace:</b> Inspect variables in memory.</li>
<li><b>Command Window:</b> Execute single-line commands.</li>
<li><b>Figures:</b> View 2D and 3D plots.</li>
</ul>

<h2>Executing Code</h2>
<ul>
<li>Use the Run button or <b>Run → Execute Script</b>.</li>
<li>Type commands directly in the Command Window.</li>
</ul>

<h2>Plot Interaction</h2>
<ul>
<li><b>Zoom:</b> Mouse scroll</li>
<li><b>Pan:</b> Right-click drag</li>
<li><b>Rotate (3D):</b> Left-click drag</li>
<li><b>Reset:</b> Home icon</li>
</ul>

<h2>Workspace Commands</h2>
<ul>
<li><code>clear</code> – remove variables</li>
<li><code>clc</code> – clear console</li>
<li><code>clf</code> / <code>close all</code> – reset figures</li>
</ul>

<p style="margin-top:30px; font-size:0.9em; color:#888;">
MathexLab v0.1.0 Alpha © 2026
</p>

</body>
</html>
"""
