from PySide6.QtWidgets import QPlainTextEdit, QTextEdit
from PySide6.QtGui import QFont, QColor, QTextFormat, QPainter
from PySide6.QtCore import Qt, QRect

from .gutter import LineNumberArea
from .syntax import MatlabHighlighter


class CodeEditor(QPlainTextEdit):
    """
    MATLAB-style editor with:
    - Line numbers
    - Breakpoint gutter click
    - Current-line highlight
    """
    def __init__(self):
        super().__init__()

        self.setFont(QFont("Consolas", 11))
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.highlighter = MatlabHighlighter(self.document())

        self.breakpoints = set()

        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #181818;
                color: #d4d4d4;
                border: none;
                selection-background-color: #264f78;
            }
        """)

        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width()
        self.highlight_current_line()

    # -------------------------------------------------------
    # Layout helpers
    # -------------------------------------------------------
    def line_number_area_width(self):
        digits = len(str(self.blockCount()))
        return 10 + self.fontMetrics().horizontalAdvance('9') * digits

    def update_line_number_area_width(self):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(
                0, rect.y(), self.lineNumberArea.width(), rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    # -------------------------------------------------------
    # Painting gutter
    # -------------------------------------------------------
    def line_number_area_paint_event(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor("#252526"))

        block = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor("#787878"))
                painter.drawText(
                    0, top,
                    self.lineNumberArea.width() - 4,
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    str(block_num + 1)
                )

                if (block_num + 1) in self.breakpoints:
                    radius = 5
                    cx = 6
                    cy = top + self.fontMetrics().ascent()
                    painter.setBrush(QColor("#c74e39"))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(cx, cy - radius, radius * 2, radius * 2)

            block = block.next()
            block_num += 1
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())

    # -------------------------------------------------------
    # Highlight current line
    # -------------------------------------------------------
    def highlight_current_line(self):
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor("#2a2d2e"))
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])

    # -------------------------------------------------------
    # Breakpoint toggling
    # -------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().x() < self.line_number_area_width():
            block = self.cursorForPosition(event.pos()).block()
            line = block.blockNumber() + 1

            if line in self.breakpoints:
                self.breakpoints.remove(line)
            else:
                self.breakpoints.add(line)

            self.lineNumberArea.update()
            return
        super().mousePressEvent(event)