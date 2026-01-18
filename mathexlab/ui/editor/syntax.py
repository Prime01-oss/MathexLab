# mathexlab/ui/editor/syntax.py
import re
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

class MatlabHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []

        # --- Define Formats ---
        
        # Keywords (Blue)
        keyword_fmt = QTextCharFormat()
        keyword_fmt.setForeground(QColor("#569cd6"))  # VS Code Blue or MATLAB #0000FF
        keyword_fmt.setFontWeight(QFont.Bold)
        keywords = [
            "function", "end", "if", "else", "elseif", "for", "while", 
            "switch", "case", "otherwise", "try", "catch", "return", 
            "break", "continue", "global", "persistent", "classdef", 
            "properties", "methods", "events"
        ]
        self.add_rule(r"\b(" + "|".join(keywords) + r")\b", keyword_fmt)

        # Built-ins / Logic (Teal/Cyan)
        builtin_fmt = QTextCharFormat()
        builtin_fmt.setForeground(QColor("#4ec9b0"))
        builtins = ["true", "false", "nan", "inf", "pi", "i", "j"]
        self.add_rule(r"\b(" + "|".join(builtins) + r")\b", builtin_fmt)

        # Numbers (Light Green/Mint)
        number_fmt = QTextCharFormat()
        number_fmt.setForeground(QColor("#b5cea8"))
        self.add_rule(r"\b\d+(\.\d*)?([eE][+-]?\d+)?\b", number_fmt)

        # Operators (White/Silver)
        op_fmt = QTextCharFormat()
        op_fmt.setForeground(QColor("#d4d4d4"))
        self.add_rule(r"[\+\-\*/\^=<>!&|~]", op_fmt)

        # Strings (Orange/Brown like MATLAB)
        string_fmt = QTextCharFormat()
        string_fmt.setForeground(QColor("#ce9178"))
        # Single quotes 'string'
        self.add_rule(r"'[^']*'", string_fmt)
        # Double quotes "string"
        self.add_rule(r'"[^"]*"', string_fmt)

        # Comments (Green) - Must be last to override others
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6a9955"))
        self.add_rule(r"%.*", comment_fmt)

    def add_rule(self, pattern, fmt):
        self.rules.append((re.compile(pattern), fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)