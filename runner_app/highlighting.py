from __future__ import annotations

import re
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat


class LogHighlighter(QSyntaxHighlighter):
    """Highlights common log keywords for quick scanning."""

    KEYWORDS = [
        (re.compile(r"\bERROR\b", re.IGNORECASE), "#ff6b6b"),
        (re.compile(r"\bWARNING\b", re.IGNORECASE), "#ffb86c"),
        (re.compile(r"\bSUCCESS\b|\bDONE\b", re.IGNORECASE), "#69db7c"),
        (re.compile(r"\bINFO\b", re.IGNORECASE), "#74c0fc"),
        (re.compile(r"Traceback|Exception|Failed", re.IGNORECASE), "#ff8787"),
    ]

    def highlightBlock(self, text: str) -> None:  # type: ignore[override]
        for pattern, color in self.KEYWORDS:
            for match in pattern.finditer(text):
                style = QTextCharFormat()
                style.setForeground(QColor(color))
                self.setFormat(match.start(), match.end() - match.start(), style)
