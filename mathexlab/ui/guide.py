from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QPushButton,
    QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

class GuideDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("MathexLab User Guide")
        self.resize(950, 700)

        # ----------------------------------------------------------------------
        # GLOBAL STYLING (Matches app.py Dark Theme)
        # ----------------------------------------------------------------------
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #cccccc;
            }
            QTextBrowser {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                padding: 15px;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 2px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1177bb; }
            QPushButton:pressed { background-color: #094771; }

            /* Scrollbar Styling */
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 20px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover { background: #505050; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ----------------------------------------------------------------------
        # HEADER
        # ----------------------------------------------------------------------
        header = QFrame()
        header.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #3e3e42;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        title = QLabel("MathexLab Documentation")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #cccccc;")
        
        subtitle = QLabel("  |  v0.1.0. Alpha")
        subtitle.setStyleSheet("font-size: 14px; color: #61afef;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addStretch()
        layout.addWidget(header)

        # ----------------------------------------------------------------------
        # CONTENT (HTML)
        # ----------------------------------------------------------------------
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setHtml(self._content())
        layout.addWidget(self.browser)

        # ----------------------------------------------------------------------
        # FOOTER
        # ----------------------------------------------------------------------
        footer = QFrame()
        footer.setStyleSheet("background-color: #1e1e1e; border-top: 1px solid #3e3e42;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 15, 20, 15)
        
        # footer_layout.addStretch()
        # close_btn = QPushButton("Close Guide")
        # close_btn.setFixedWidth(120)
        # close_btn.clicked.connect(self.accept)
        # footer_layout.addWidget(close_btn)

        layout.addWidget(footer)

    def _content(self):
        # Using a rich HTML structure to organize the comprehensive guide
        return """
<!DOCTYPE html>
<html>
<head>
<style>
    body { color: #d4d4d4; font-family: 'Segoe UI', sans-serif; line-height: 1.6; }
    
    /* Headers */
    h1 { color: #61afef; border-bottom: 2px solid #3e3e42; padding-bottom: 10px; margin-top: 0px; }
    h2 { color: #98c379; margin-top: 30px; margin-bottom: 10px; font-size: 1.4em; }
    h3 { color: #e5c07b; margin-top: 20px; font-size: 1.1em; }
    
    /* Text Blocks */
    p { margin-bottom: 10px; }
    li { margin-bottom: 5px; }
    
    /* Code Styling */
    code {
        background-color: #3e3e42;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Consolas', monospace;
        color: #ce9178;
        font-size: 0.95em;
    }
    pre {
        background-color: #1e1e1e;
        border: 1px solid #3e3e42;
        padding: 15px;
        border-radius: 5px;
        font-family: 'Consolas', monospace;
        color: #9cdcfe;
        overflow-x: auto;
    }
    
    /* Key Concepts Tags */
    .tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
        margin-right: 5px;
    }
    .tag-blue { background-color: #0e639c; color: white; }
    .tag-green { background-color: #388e3c; color: white; }
    .tag-purple { background-color: #6a1b9a; color: white; }

</style>
</head>

<body>

<h1>Welcome to MathexLab</h1>
<p>
    <b>MathexLab</b> is a high-fidelity research environment designed to replace standard MATLAB workflows 
    for PhD students and engineers. It combines the syntax you know with the power of the Python scientific stack.
</p>

<h2>🚀 Interface Overview</h2>

<h3>1. The Command Window (Transcript Mode)</h3>
<p>
    Unlike standard Python shells, the MathexLab console implements a <b>Strict Transcript Model</b>.
    <ul>
        <li><b>Immutable History:</b> You cannot edit previous commands or outputs (White text).</li>
        <li><b>Input Locking:</b> You can only type after the <code>>></code> prompt.</li>
        <li><b>History Navigation:</b> Use <span class="tag tag-blue">Up</span> / <span class="tag tag-blue">Down</span> arrows to cycle through previous commands.</li>
    </ul>
</p>

<h3>2. The Workspace Inspector</h3>
<p>
    A live view of all variables in memory. 
    <br><b>Feature:</b> Double-click any variable to open the <b>Deep Inspector</b>. 
    For large 3D arrays (e.g., MRI data), it automatically generates 2D "slice views" to prevent UI freezing.
</p>

<h3>3. Plot Dock</h3>
<p>
    Matplotlib figures are integrated directly into the IDE. Use the mouse to interact:
    <ul>
        <li><b>Zoom:</b> Scroll Wheel</li>
        <li><b>Pan:</b> Right-Click + Drag</li>
        <li><b>Rotate (3D):</b> Left-Click + Drag</li>
    </ul>
</p>

<hr style="border: 0; border-top: 1px solid #3e3e42; margin: 20px 0;">

<h2>🧠 PhD Research Toolboxes</h2>
<p>MathexLab includes specialized solvers for advanced research.</p>

<h3>Partial Differential Equations (PDE)</h3>
<pre>
sol = pdepe(m, pdefun, icfun, bcfun, xmesh, tspan)
</pre>
<p>
    Solves systems of parabolic and elliptic PDEs in one spatial variable.
    Supports <span class="tag tag-green">Slab (m=0)</span>, <span class="tag tag-green">Cylindrical (m=1)</span>, and <span class="tag tag-green">Spherical (m=2)</span> geometries.
</p>

<h3>Constrained Optimization</h3>
<pre>
x = fmincon(fun, x0, A, b, Aeq, beq, lb, ub, nonlcon)
</pre>
<p>
    Finds the minimum of a constrained non-linear multivariable function. 
    Essential for engineering design optimization (e.g., minimizing weight subject to stress constraints).
</p>

<h3>Control Systems</h3>
<p>
    Analyze Linear Time-Invariant (LTI) systems using transfer functions and root locus plots.
</p>
<pre>
sys = tf([1], [1, 2, 1]);  % Create Transfer Function
rlocus(sys);               % Plot Root Locus
</pre>

<hr style="border: 0; border-top: 1px solid #3e3e42; margin: 20px 0;">

<h2>⚡ Language & Compatibility</h2>
<p>
    The built-in <b>Transpiler</b> allows you to write MATLAB-style code which is compiled to Python on the fly.
</p>

<h3>Supported Features</h3>
<ul>
    <li><b>1-based Indexing:</b> <code>A(1)</code> automatically maps to Python's <code>A[0]</code>.</li>
    <li><b>Matrix Math:</b> <code>*</code> is matrix multiplication, <code>.*</code> is element-wise.</li>
    <li><b>Object Oriented:</b> Full support for <code>classdef</code>, <code>properties</code>, and <code>methods</code>.</li>
    <li><b>Structures:</b> Support for struct arrays and cell arrays (e.g., <code>s(1).val = 5</code>).</li>
    <li><b>Control Flow:</b> <code>switch-case</code> (including cell cases), <code>try-catch</code>, and <code>if-elseif-else</code>.</li>
</ul>

<h3>Example Class Definition</h3>
<pre>
classdef Particle
    properties
        Mass
        Velocity
    end
    methods
        function obj = Particle(m, v)
            obj.Mass = m;
            obj.Velocity = v;
        end
        function E = energy(obj)
            E = 0.5 * obj.Mass * obj.Velocity^2;
        end
    end
end
</pre>

<hr style="border: 0; border-top: 1px solid #3e3e42; margin: 20px 0;">

<h2>⌨️ Keyboard Shortcuts</h2>
<table style="width:100%; text-align:left; border-collapse:collapse;">
    <tr><th style="border-bottom:1px solid #555; padding:5px;">Action</th><th style="border-bottom:1px solid #555; padding:5px;">Shortcut</th></tr>
    <tr><td style="padding:5px;">Run Script</td><td style="padding:5px; color:#9cdcfe;">F5</td></tr>
    <tr><td style="padding:5px;">Clear Console</td><td style="padding:5px; color:#9cdcfe;">Ctrl + L / clc</td></tr>
    <tr><td style="padding:5px;">Clear Variables</td><td style="padding:5px; color:#9cdcfe;">clear</td></tr>
    <tr><td style="padding:5px;">Close Figures</td><td style="padding:5px; color:#9cdcfe;">close all</td></tr>
    <tr><td style="padding:5px;">History Previous</td><td style="padding:5px; color:#9cdcfe;">Up Arrow</td></tr>
    <tr><td style="padding:5px;">History Next</td><td style="padding:5px; color:#9cdcfe;">Down Arrow</td></tr>
</table>

<p style="margin-top:40px; font-size:0.9em; color:#666; text-align:center;">
    MathexLab © 2026 | Built with Python 3.11 & Qt6
</p>

</body>
</html>
"""