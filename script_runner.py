import sys, os, subprocess, re, datetime, json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFileDialog, QComboBox, QLineEdit, QListWidget,
    QSplitter, QTabWidget
)
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QIcon, QDesktopServices
from PySide6.QtCore import Qt, QThread, Signal, QUrl

# ---------------------------
# Paths & Config
# ---------------------------
APP_DIR = os.path.join(os.path.expanduser("~"), ".script_runner")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
LOG_DIR = os.path.join(APP_DIR, "logs")
os.makedirs(APP_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

DEFAULT_CONFIG = {"theme": "dark", "history": []}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

def resource_path(relative_path):
    """Resolve path for dev and PyInstaller bundle"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# ---------------------------
# Syntax Highlighter
# ---------------------------
class LogHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self.rules = [
            (re.compile(r"\bERROR\b", re.IGNORECASE), QColor("#ff6b6b")),
            (re.compile(r"\bWARNING\b", re.IGNORECASE), QColor("#ffb86c")),
            (re.compile(r"\bSUCCESS\b|\bDONE\b", re.IGNORECASE), QColor("#69db7c")),
            (re.compile(r"\bINFO\b", re.IGNORECASE), QColor("#74c0fc")),
            (re.compile(r"Traceback|Exception|Failed", re.IGNORECASE), QColor("#ff8787")),
        ]

    def highlightBlock(self, text):
        for pattern, color in self.rules:
            for match in pattern.finditer(text):
                fmt = QTextCharFormat()
                fmt.setForeground(color)
                self.setFormat(match.start(), match.end() - match.start(), fmt)

# ---------------------------
# Worker Thread
# ---------------------------
class ScriptWorker(QThread):
    output = Signal(str)
    finished = Signal(int)

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd
        self._stop_requested = False

    def run(self):
        ret = -1
        try:
            process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                self.output.emit(line.rstrip("\n"))
                if self._stop_requested:
                    process.terminate()
                    self.output.emit("> Script terminated by user.")
                    break
            ret = process.wait()
        except Exception as e:
            self.output.emit(f"> Error: {e}")
        self.finished.emit(ret)

    def stop(self):
        self._stop_requested = True

# ---------------------------
# Main App
# ---------------------------
class ScriptRunner(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Script Runner")
        self.setWindowIcon(QIcon(resource_path("app_icon.ico")))
        self.setAcceptDrops(True)

        self.script_path = None
        self.worker = None
        self.config = load_config()
        self.theme = self.config.get("theme", "dark")

        self.setup_ui()
        self.apply_theme(self.theme)
        self.refresh_logs_list()
        self.refresh_history_list()

    # ---------------------------
    # UI Setup
    # ---------------------------
    def setup_ui(self):
        main = QHBoxLayout()
        self.setLayout(main)

        splitter = QSplitter(Qt.Horizontal)
        main.addWidget(splitter)

        # Sidebar
        self.sidebar = QTabWidget()
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.load_selected_history)
        self.logs_list = QListWidget()
        self.logs_list.itemDoubleClicked.connect(self.open_selected_log)

        self.sidebar.addTab(self.history_list, "History")
        self.sidebar.addTab(self.logs_list, "Logs")

        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout()
        sidebar_widget.setLayout(sidebar_layout)
        sidebar_layout.addWidget(self.sidebar)

        btn_row = QHBoxLayout()
        refresh_btn = QPushButton("Refresh Logs")
        refresh_btn.clicked.connect(self.refresh_logs_list)
        open_dir_btn = QPushButton("Open Logs Folder")
        open_dir_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(LOG_DIR)))
        btn_row.addWidget(refresh_btn)
        btn_row.addWidget(open_dir_btn)
        sidebar_layout.addLayout(btn_row)

        splitter.addWidget(sidebar_widget)

        # Main content
        content = QWidget()
        content_layout = QVBoxLayout()
        content.setLayout(content_layout)
        splitter.addWidget(content)
        splitter.setStretchFactor(1, 3)

        # Top bar
        top = QHBoxLayout()
        self.script_label = QLabel("📂 No script selected")
        top.addWidget(self.script_label)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_script)
        top.addWidget(browse_btn)

        self.type_box = QComboBox()
        self.type_box.addItems(["Python", "Bash", "PowerShell"])
        top.addWidget(self.type_box)

        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self.run_script)
        top.addWidget(self.run_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_script)
        top.addWidget(self.stop_btn)

        self.theme_btn = QPushButton("Theme: Dark" if self.theme == "dark" else "Theme: Light")
        self.theme_btn.clicked.connect(self.toggle_theme)
        top.addWidget(self.theme_btn)

        content_layout.addLayout(top)

        # Args
        arg_row = QHBoxLayout()
        arg_row.addWidget(QLabel("🧾 Args:"))
        self.arg_input = QLineEdit()
        self.arg_input.setPlaceholderText("e.g. --verbose --debug")
        arg_row.addWidget(self.arg_input)
        content_layout.addLayout(arg_row)

        # Output
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setFont(QFont("Consolas", 11))
        self.highlighter = LogHighlighter(self.output_box.document())
        content_layout.addWidget(self.output_box)

        # Bottom
        bottom = QHBoxLayout()
        self.save_btn = QPushButton("💾 Save Log")
        self.save_btn.clicked.connect(self.save_log)
        bottom.addStretch()
        bottom.addWidget(self.save_btn)
        content_layout.addLayout(bottom)

    # ---------------------------
    # Theme
    # ---------------------------
    def apply_theme(self, theme):
        if theme == "dark":
            stylesheet = """
                QWidget { background-color: #1e1e1e; color: #e0e0e0; font-family: Segoe UI; font-size: 14px; }
                QPushButton { background-color: #2c2c2c; border: 1px solid #555; padding: 6px; border-radius: 6px; }
                QPushButton:hover { background-color: #3c3c3c; }
                QLineEdit, QTextEdit { background-color: #2a2a2a; border: 1px solid #444; color: #e0e0e0; border-radius: 6px; }
                QComboBox { background-color: #2a2a2a; border: 1px solid #444; color: #e0e0e0; border-radius: 6px; }

                /* Força fundo escuro nas listas */
                QListWidget, QTabWidget::pane {
                    background-color: #2a2a2a;
                    border: 1px solid #444;
                    color: #e0e0e0;
                }
                QTabBar::tab {
                    background: #2a2a2a;
                    padding: 6px 10px;
                    border: 1px solid #444;
                    border-bottom: none;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                }
                QTabBar::tab:selected { background: #3a3a3a; }
            """

        else:  # light theme
            stylesheet = """
                QWidget { background-color: #f4f4f4; color: #202020; font-family: Segoe UI; font-size: 14px; }
                QPushButton { background-color: #ffffff; border: 1px solid #ccc; padding: 6px; border-radius: 6px; }
                QPushButton:hover { background-color: #f0f0f0; }
                QLineEdit, QTextEdit { background-color: #ffffff; border: 1px solid #ccc; color: #202020; border-radius: 6px; }
                QComboBox { background-color: #ffffff; border: 1px solid #ccc; color: #202020; border-radius: 6px; }
                QListWidget { background-color: #ffffff; border: 1px solid #ccc; color: #202020; }
            """
        self.setStyleSheet(stylesheet)
        self.theme_btn.setText("Theme: Dark" if theme == "dark" else "Theme: Light")

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.apply_theme(self.theme)
        self.config["theme"] = self.theme
        save_config(self.config)

    # ---------------------------
    # Script loading
    # ---------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.endswith((".py", ".sh", ".ps1")):
                self.load_script(path)

    def browse_script(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Script", "", "Scripts (*.py *.sh *.ps1)")
        if path:
            self.load_script(path)

    def load_script(self, path):
        self.script_path = path
        self.script_label.setText(f"📂 {os.path.basename(path)}")
        ext = os.path.splitext(path)[1].lower()
        if ext == ".py":
            self.type_box.setCurrentText("Python")
        elif ext == ".sh":
            self.type_box.setCurrentText("Bash")
        elif ext == ".ps1":
            self.type_box.setCurrentText("PowerShell")

        # Atualiza histórico
        hist = self.config.get("history", [])
        if path in hist:
            hist.remove(path)
        hist.insert(0, path)
        self.config["history"] = hist[:20]
        save_config(self.config)
        self.refresh_history_list()

    # ---------------------------
    # Execução de scripts
    # ---------------------------
    def run_script(self):
        if not self.script_path:
            self.output_box.append("No script selected.")
            return

        args = self.arg_input.text().split()
        mode = self.type_box.currentText()

        if mode == "Python":
            cmd = ["python", self.script_path] + args
        elif mode == "Bash":
            cmd = ["bash", self.script_path] + args
        elif mode == "PowerShell":
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", self.script_path] + args
        else:
            self.output_box.append("Unsupported script type.")
            return

        self.output_box.clear()
        self.output_box.append(f"> Running {os.path.basename(self.script_path)}...\n")

        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self.worker = ScriptWorker(cmd)
        self.worker.output.connect(self.output_box.append)
        self.worker.finished.connect(self.script_finished)
        self.worker.start()

    def stop_script(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()

    def script_finished(self, code):
        self.output_box.append(f"\n> Script finished with exit code {code}.")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    # ---------------------------
    # Logs e histórico
    # ---------------------------
    def save_log(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base = os.path.splitext(os.path.basename(self.script_path or "output"))[0]
        filename = f"{base}_{timestamp}.log"
        path = os.path.join(LOG_DIR, filename)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.output_box.toPlainText())
            self.output_box.append(f"\n> Log saved to {path}")
            self.refresh_logs_list()
        except Exception as e:
            self.output_box.append(f"\n> Failed to save log: {e}")

    def refresh_logs_list(self):
        self.logs_list.clear()
        try:
            files = sorted(
                [f for f in os.listdir(LOG_DIR) if f.lower().endswith(".log")],
                key=lambda x: os.path.getmtime(os.path.join(LOG_DIR, x)),
                reverse=True
            )
            for f in files:
                self.logs_list.addItem(f)
        except Exception:
            pass

    def open_selected_log(self):
        item = self.logs_list.currentItem()
        if not item:
            return
        path = os.path.join(LOG_DIR, item.text())
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def refresh_history_list(self):
        self.history_list.clear()
        for p in self.config.get("history", []):
            self.history_list.addItem(p)

    def load_selected_history(self):
        item = self.history_list.currentItem()
        if item:
            self.load_script(item.text())

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScriptRunner()
    window.resize(1050, 600)

    # Suporte a "Abrir com"
    if len(sys.argv) > 1:
        window.load_script(sys.argv[1])

    window.show()
    sys.exit(app.exec())
