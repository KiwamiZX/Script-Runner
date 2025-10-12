from __future__ import annotations

from typing import Literal

ThemeName = Literal["dark", "light"]


def build_stylesheet(theme: ThemeName) -> str:
    if theme == "dark":
        run_color = "#00d47b"
        stop_color = "#ff5b5b"
        return f"""
            QWidget#rootWindow {{
                background-color: #020907;
                color: #dcffe8;
                font-family: 'Segoe UI';
                font-size: 14px;
            }}
            QDialog {{
                background-color: #04140d;
                color: #dcffe8;
                border: 2px solid #00ff9f;
                border-radius: 14px;
            }}
            QLabel {{
                color: #dcffe8;
            }}
            QCheckBox {{
                color: #dcffe8;
            }}
            QFrame#headerFrame,
            QFrame#controlsFrame,
            QFrame#outputFrame,
            QFrame#statusFrame {{
                background-color: #05140f;
                border: 2px solid #00ff9f;
                border-radius: 14px;
            }}
            QFrame#leftPanel {{
                background-color: transparent;
            }}
            QLabel#scriptLabel {{
                font-size: 19px;
                font-weight: 700;
                letter-spacing: 0.6px;
                color: #7cffc8;
            }}
            QLabel#sectionTitle {{
                font-size: 16px;
                font-weight: 700;
                margin-bottom: 6px;
                color: #7cffc8;
            }}
            QLabel#fieldLabel {{
                font-weight: 600;
                text-transform: uppercase;
                color: #4af0b8;
                letter-spacing: 1px;
            }}
            QLabel#statusLabel {{
                font-weight: 600;
                color: #00ff9f;
            }}
            QPushButton {{
                background-color: #04301f;
                border: 2px solid #00ff9f;
                border-radius: 12px;
                padding: 10px 20px;
                color: #dcffe8;
                font-weight: 600;
                letter-spacing: 0.4px;
            }}
            QPushButton#runButton {{
                background-color: {run_color};
                border-color: #12ffac;
                color: #00140a;
            }}
            QPushButton#stopButton {{
                background-color: {stop_color};
                border-color: #ff8f8f;
                color: #2b0000;
            }}
            QPushButton:hover {{
                background-color: #0b4630;
            }}
            QPushButton:pressed {{
                background-color: #052b1b;
            }}
            QPushButton:disabled {{
                background-color: #0a1912;
                border-color: #155238;
                color: #4f7f69;
            }}
            QLineEdit,
            QTextEdit {{
                background-color: #040e0b;
                border: 2px solid #00ff9f;
                border-radius: 12px;
                padding: 9px 12px;
                color: #dcffe8;
                selection-background-color: #00ff9f;
                selection-color: #00140a;
            }}
            QTextEdit#outputBox {{
                padding: 16px;
            }}
            QComboBox {{
                background-color: #040e0b;
                border: 2px solid #00ff9f;
                border-radius: 12px;
                padding: 8px 12px;
                color: #dcffe8;
            }}
            QComboBox QAbstractItemView {{
                background-color: #030b08;
                border: 2px solid #00ff9f;
                color: #dcffe8;
                selection-background-color: #00ff9f;
                selection-color: #00140a;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 8px 12px;
                color: #dcffe8;
            }}
            QListWidget {{
                background-color: #030b08;
                border: 2px solid #00ff9f;
                border-radius: 12px;
            }}
            QListWidget::item {{
                padding: 8px 10px;
                color: #d0ffe8;
            }}
            QListWidget::item:hover {{
                background: #093826;
            }}
            QListWidget::item:selected {{
                background: #00ff9f;
                color: #00140a;
            }}
            QTabWidget::pane {{
                background: #020907;
                border: 2px solid #00ff9f;
                border-radius: 14px;
                margin-top: 12px;
            }}
            QTabBar::tab {{
                background: #020907;
                border: 2px solid #00ff9f;
                border-bottom: none;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                padding: 9px 20px;
                color: #00ff9f;
                margin-right: 6px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: #00ff9f;
                color: #00140a;
            }}
            QSplitter::handle {{
                background-color: #04150f;
                border: 1px solid #00ff9f;
                margin: 6px 0;
            }}
            QListView#historyList::item[data-match='false'] {{
                color: #1b5f40;
            }}
            QScrollBar:vertical {{
                background: #03120d;
                width: 14px;
                border: 1px solid #00ff9f;
                border-radius: 7px;
            }}
            QScrollBar::handle:vertical {{
                background: #00ff9f;
                min-height: 40px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #40ffb9;
            }}
            QScrollBar::sub-line:vertical,
            QScrollBar::add-line:vertical {{
                height: 0;
                background: none;
                border: none;
            }}
            QScrollBar:horizontal {{
                background: #03120d;
                height: 14px;
                border: 1px solid #00ff9f;
                border-radius: 7px;
            }}
            QScrollBar::handle:horizontal {{
                background: #00ff9f;
                min-width: 40px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: #40ffb9;
            }}
            QScrollBar::sub-line:horizontal,
            QScrollBar::add-line:horizontal {{
                width: 0;
                background: none;
                border: none;
            }}
        """
    else:
        return """
            QWidget#rootWindow {
                background-color: #f5fffa;
                color: #063523;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QDialog {
                background-color: #ffffff;
                color: #063523;
                border: 2px solid #14b371;
                border-radius: 14px;
            }
            QLabel {
                color: #063523;
            }
            QCheckBox {
                color: #063523;
            }
            QFrame#headerFrame,
            QFrame#controlsFrame,
            QFrame#outputFrame,
            QFrame#statusFrame {
                background-color: #ffffff;
                border: 2px solid #14b371;
                border-radius: 14px;
            }
            QLabel#scriptLabel {
                font-size: 19px;
                font-weight: 700;
                color: #0b7c4b;
            }
            QLabel#sectionTitle {
                font-size: 16px;
                font-weight: 700;
                margin-bottom: 6px;
                color: #0b7c4b;
            }
            QLabel#fieldLabel {
                font-weight: 600;
                color: #0f9d60;
                letter-spacing: 1px;
            }
            QLabel#statusLabel {
                font-weight: 600;
                color: #0b7c4b;
            }
            QPushButton {
                background-color: #e5fff4;
                border: 2px solid #0f9d60;
                border-radius: 12px;
                padding: 10px 20px;
                color: #0c4d32;
                font-weight: 600;
            }
            QPushButton#runButton {
                background-color: #b8ffd9;
                border-color: #0f9d60;
                color: #044126;
            }
            QPushButton#stopButton {
                background-color: #ffd5d5;
                border-color: #ff8585;
                color: #5b0505;
            }
            QPushButton:hover {
                background-color: #ccf4df;
            }
            QPushButton:pressed {
                background-color: #b3eacb;
            }
            QPushButton:disabled {
                border-color: #88c8a6;
                color: #88c8a6;
            }
            QLineEdit,
            QTextEdit,
            QComboBox,
            QListWidget {
                background-color: #ffffff;
                border: 2px solid #14b371;
                border-radius: 12px;
                color: #083526;
                padding: 9px 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 2px solid #14b371;
                color: #083526;
                selection-background-color: #14b371;
                selection-color: #ffffff;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                color: #083526;
            }
            QListWidget::item {
                padding: 8px 10px;
                color: #083526;
            }
            QListWidget::item:hover {
                background: #d8fae7;
            }
            QListWidget::item:selected {
                background: #14b371;
                color: #ffffff;
            }
            QTabWidget::pane {
                background: #ffffff;
                border: 2px solid #14b371;
                border-radius: 14px;
                margin-top: 12px;
            }
            QTabBar::tab {
                background: #e9ffef;
                border: 2px solid #14b371;
                border-bottom: none;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                padding: 9px 20px;
                color: #0f9d60;
                margin-right: 6px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: #14b371;
                color: #ffffff;
            }
            QSplitter::handle {
                background-color: #dff7ea;
                border: 1px solid #14b371;
                margin: 6px 0;
            }
            QListView#historyList::item[data-match='false'] {
                color: #9dcbb3;
            }
            QScrollBar:vertical {
                background: #f1fff7;
                width: 14px;
                border: 1px solid #14b371;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background: #14b371;
                min-height: 40px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #39d18e;
            }
            QScrollBar::sub-line:vertical,
            QScrollBar::add-line:vertical {
                height: 0;
                background: none;
                border: none;
            }
            QScrollBar:horizontal {
                background: #f1fff7;
                height: 14px;
                border: 1px solid #14b371;
                border-radius: 7px;
            }
            QScrollBar::handle:horizontal {
                background: #14b371;
                min-width: 40px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #39d18e;
            }
            QScrollBar::sub-line:horizontal,
            QScrollBar::add-line:horizontal {
                width: 0;
                background: none;
                border: none;
            }
        """
