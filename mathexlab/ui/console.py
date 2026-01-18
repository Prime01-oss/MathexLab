# mathexlab/ui/console.py
from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtGui import (
    QTextCursor, QFont, QColor,
    QTextCharFormat, QKeySequence
)
from PySide6.QtCore import Qt, Signal


class ConsoleWidget(QPlainTextEdit):
    """
    MATLAB-grade Command Window UI (Strict Transcript Model)

    Rules:
    - Transcript is read-only
    - Prompt is immutable
    - Input allowed ONLY after prompt
    - Cursor/selection NEVER crosses prompt boundary
    """

    command_entered = Signal(str)

    # ------------------------------------------------------------
    # VISUAL CONSTANTS (STRICT COLOR RULES)
    # ------------------------------------------------------------
    COLOR_BG = "#1e1e1e"
    
    # Text meant for output and the '>>' prompt is WHITE
    COLOR_TRANSCRIPT = "#ffffff"  
    COLOR_PROMPT = "#ffffff"      
    
    # Text typed by the user (after '>>') is GREYISH
    COLOR_INPUT = "#aaaaaa"       
    
    COLOR_ERROR = "#ff5555"

    PROMPT = ">> "
    CONTINUATION = "... "

    # ------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------
    def __init__(self):
        super().__init__()

        self._setup_ui()
        self._reset_state()
        self._init_console()

    def initialize(self, text=""):
        """Public API used by app.py"""
        self.clear()
        if text:
            self._append_transcript(text)
        self._insert_prompt()

    # ------------------------------------------------------------
    # UI SETUP
    # ------------------------------------------------------------
    def _setup_ui(self):
        self.setUndoRedoEnabled(False)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setFrameShape(QPlainTextEdit.NoFrame)

        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {self.COLOR_BG};
                color: {self.COLOR_TRANSCRIPT};
                border: none;
                padding: 4px;
                selection-background-color: #264f78;
                selection-color: #ffffff;
            }}
        """)

    # ------------------------------------------------------------
    # STATE
    # ------------------------------------------------------------
    def _reset_state(self):
        self.history = []
        self.history_index = -1
        self.multi_line_buffer = []
        self.locked_pos = 0  # absolute transcript boundary

    # ------------------------------------------------------------
    # FORMATTING HELPERS
    # ------------------------------------------------------------
    def _fmt(self, color):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        return fmt

    # ------------------------------------------------------------
    # CONSOLE CORE
    # ------------------------------------------------------------
    def _init_console(self):
        self.clear()
        self._append_transcript("MathexLab Console Environment\n")
        self._insert_prompt()

    def _insert_prompt(self, continuation=False):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)

        # 1. Insert Prompt (WHITE)
        prompt = self.CONTINUATION if continuation else self.PROMPT
        cursor.insertText(prompt, self._fmt(self.COLOR_PROMPT))

        # 2. Move Cursor After Prompt
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

        # 3. Set Format for FUTURE typing (GREY)
        self.setCurrentCharFormat(self._fmt(self.COLOR_INPUT))

        # 🔒 HARD LOCK
        self.locked_pos = cursor.position()

    def _append_transcript(self, text, color=None):
        if color is None:
            color = self.COLOR_TRANSCRIPT

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)

        if self.document().characterCount() > 1 and not self.document().toPlainText().endswith("\n"):
            cursor.insertText("\n")

        cursor.insertText(text.rstrip("\n") + "\n", self._fmt(color))
        self.setTextCursor(cursor)

    # ------------------------------------------------------------
    # BOUNDARY ENFORCEMENT (ABSOLUTE)
    # ------------------------------------------------------------
    def _enforce_boundary(self):
        cursor = self.textCursor()

        if cursor.position() < self.locked_pos:
            cursor.setPosition(self.locked_pos)
            self.setTextCursor(cursor)

        if cursor.hasSelection() and cursor.selectionStart() < self.locked_pos:
            cursor.setPosition(self.locked_pos)
            cursor.setPosition(cursor.selectionEnd(), QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
        
        # [FIX] Enforce Input Color if cursor is in input area
        # This fixes the issue where clicking back to the prompt line resets color
        if cursor.position() >= self.locked_pos:
            self.setCurrentCharFormat(self._fmt(self.COLOR_INPUT))

    # ------------------------------------------------------------
    # KEY HANDLING
    # ------------------------------------------------------------
    def keyPressEvent(self, event):
        cursor = self.textCursor()

        in_transcript = cursor.position() < self.locked_pos
        selection_crosses = (
            cursor.hasSelection() and cursor.selectionStart() < self.locked_pos
        )

        # ---- DISABLED GLOBALS ----
        if event.matches(QKeySequence.SelectAll):
            return
        if event.matches(QKeySequence.Undo) or event.matches(QKeySequence.Redo):
            return

        # ---- COPY ALWAYS OK ----
        if event.matches(QKeySequence.Copy):
            super().keyPressEvent(event)
            return

        # ---- PASTE SAFETY ----
        if event.matches(QKeySequence.Paste):
            if in_transcript or selection_crosses:
                cursor.clearSelection()
                cursor.movePosition(QTextCursor.End)
                self.setTextCursor(cursor)
            
            # [FIX] Enforce Grey Color on Paste
            self.setCurrentCharFormat(self._fmt(self.COLOR_INPUT))
            super().keyPressEvent(event)
            return

        # ---- CUT ----
        if event.matches(QKeySequence.Cut):
            if selection_crosses:
                return
            super().keyPressEvent(event)
            return

        # ---- HOME ----
        if event.key() == Qt.Key_Home and not event.modifiers():
            cursor.setPosition(self.locked_pos)
            self.setTextCursor(cursor)
            # [FIX] Enforce Color on Navigation
            self.setCurrentCharFormat(self._fmt(self.COLOR_INPUT))
            return

        # ---- CLEAR ----
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_L:
            self.clear()
            self._insert_prompt()
            return

        # ---- HISTORY ----
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            self._handle_history(event.key())
            return

        # ---- ENTER ----
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._handle_enter()
            return

        # ---- DESTRUCTIVE BLOCK ----
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            if in_transcript or selection_crosses:
                return
            if event.key() == Qt.Key_Backspace and cursor.position() == self.locked_pos:
                return

        # ---- TYPING ----
        if event.text() and (in_transcript or selection_crosses):
            cursor.clearSelection()
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)

        # [FIX] AGGRESSIVE COLOR ENFORCEMENT
        # Before any typing happens, ensure we are using the GREY input color.
        # This overrides any "inheritance" from the White prompt character.
        if event.text() and not event.modifiers():
             self.setCurrentCharFormat(self._fmt(self.COLOR_INPUT))

        super().keyPressEvent(event)
        self._enforce_boundary()

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        self._enforce_boundary()

    # ------------------------------------------------------------
    # COMMAND HANDLING
    # ------------------------------------------------------------
    def _handle_enter(self):
        cursor = self.textCursor()
        cursor.setPosition(self.locked_pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cmd = cursor.selectedText().strip()

        cursor.clearSelection()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
        self.appendPlainText("")

        if cmd.endswith("..."):
            self.multi_line_buffer.append(cmd[:-3])
            self._insert_prompt(continuation=True)
            return

        full_cmd = cmd
        if self.multi_line_buffer:
            self.multi_line_buffer.append(cmd)
            full_cmd = " ".join(self.multi_line_buffer)
            self.multi_line_buffer.clear()

        if full_cmd:
            self._push_history(full_cmd)
            self.command_entered.emit(full_cmd)
        else:
            self._insert_prompt()

    # ------------------------------------------------------------
    # HISTORY
    # ------------------------------------------------------------
    def _push_history(self, cmd):
        if not self.history or self.history[-1] != cmd:
            self.history.append(cmd)
        self.history_index = len(self.history)

    def _handle_history(self, key):
        if not self.history:
            return

        if key == Qt.Key_Up and self.history_index > 0:
            self.history_index -= 1
        elif key == Qt.Key_Down and self.history_index < len(self.history):
            self.history_index += 1

        text = (
            self.history[self.history_index]
            if 0 <= self.history_index < len(self.history)
            else ""
        )

        cursor = self.textCursor()
        cursor.setPosition(self.locked_pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        
        # [FIX] Insert History using GREY INPUT COLOR
        cursor.insertText(text, self._fmt(self.COLOR_INPUT))
        self.setTextCursor(cursor) # Move cursor to end of inserted text

    # ------------------------------------------------------------
    # OUTPUT API (USED BY KERNEL)
    # ------------------------------------------------------------
    def write_output(self, text):
        if "\f" in text:
            self.clear()
            text = text.replace("\f", "")
        
        if text:
            self._append_transcript(text, self.COLOR_TRANSCRIPT)
            
        self._insert_prompt()

    def write_error(self, text):
        self._append_transcript(text, self.COLOR_ERROR)
        self._insert_prompt()

    def _print_text(self, text, color):
        """Helper to print a system message and restore the prompt."""
        self._append_transcript(text, color)
        self._insert_prompt()

    # ------------------------------------------------------------
    # EXECUTION LIFECYCLE HOOK
    # ------------------------------------------------------------
    def execution_finished(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

        block_text = self.document().lastBlock().text()
        if not (block_text.startswith(self.PROMPT) or block_text.startswith(self.CONTINUATION)):
            self._insert_prompt()
            
    # [FIX] Helper method required by is_at_prompt/move_cursor_to_prompt
    def _prompt_end_pos(self):
        return self.locked_pos

    def is_at_prompt(self) -> bool:
        cursor = self.textCursor()
        return cursor.position() >= self._prompt_end_pos()

    def move_cursor_to_prompt(self):
        cursor = self.textCursor()
        cursor.setPosition(self._prompt_end_pos())
        self.setTextCursor(cursor)

    def get_current_input(self) -> str:
        cursor = self.textCursor()
        cursor.setPosition(self._prompt_end_pos())
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        return cursor.selectedText()

    def clear_input_only(self):
        cursor = self.textCursor()
        cursor.setPosition(self._prompt_end_pos())
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        self.setTextCursor(cursor)

    def reset_input_line(self):
        self.clear_input_only()
        self.move_cursor_to_prompt()

    def echo_command(self, cmd: str):
        self.write_output(cmd)

    def show_busy(self):
        self.busy = True

    def show_ready(self):
        self.busy = False

    def write_warning(self, text):
        self._print_text(f"Warning: {text}", QColor("#ffaa00"))

    def write_info(self, text):
        self._print_text(text, QColor("#7aa2f7"))

    def repeat_last_command(self):
        if not self.history:
            return
        self.reset_input_line()
        # [FIX] Ensure repeated command is also Grey
        self.setCurrentCharFormat(self._fmt(self.COLOR_INPUT))
        self.insertPlainText(self.history[-1])