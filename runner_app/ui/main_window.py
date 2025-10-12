from __future__ import annotations

import datetime as dt
import sys
import os
import shlex
from functools import partial
from typing import Dict, List, Optional
import subprocess

from PySide6.QtCore import Qt, QTimer, QUrl, QStringListModel, QProcess
from PySide6.QtGui import QDesktopServices, QFont, QIcon, QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QCompleter,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..config import load_config, save_config
from ..highlighting import LogHighlighter
from ..paths import LOG_DIR, resource_path
from ..process import ScriptProcess
from ..settings import SettingsDialog, InterpreterProfile
from .theme import build_stylesheet

COMMON_ARGUMENTS = [
    "--help",
    "--verbose",
    "--quiet",
    "--log-level",
    "--config",
    "--dry-run",
    "--input",
    "--output",
    "--limit",
    "--env",
]

COMMAND_TEMPLATES: Dict[str, List[tuple[str, str]]] = {
    "Python": [
        ("Data analysis (pandas)", "--input data.csv --summary report.json"),
        ("Web scraping", "--url https://example.com --depth 2 --export output.json"),
        ("Automation task", "--config settings.yaml --dry-run"),
    ],
    "Bash": [
        ("Server log tail", "tail -f /var/log/syslog"),
        ("Deployment", "./deploy.sh --stage staging --confirm"),
    ],
    "PowerShell": [
        ("List services", "Get-Service | Sort-Object Status"),
        ("Scheduled task", "Register-ScheduledTask -TaskName MyJob -Xml task.xml"),
    ],
    "Node.js": [
        ("Express dev server", "npm run dev"),
        ("Build project", "npm run build"),
    ],
}

HISTORY_TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S"


def _timestamp() -> str:
    return dt.datetime.now().strftime(HISTORY_TIMESTAMP_FMT)


def _with_timestamp(text: str) -> str:
    stamp = dt.datetime.now().strftime("[%H:%M:%S] ")
    lines = text.splitlines() or [""]
    return "\n".join(f"{stamp}{line}" for line in lines)


def _classify_log(path: str) -> str:
    tags = {"error": ["error", "exception", "traceback"], "warning": ["warning"], "success": ["success", "done"]}
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            head = handle.read(4096).lower()
    except OSError:
        return "other"

    for label, needles in tags.items():
        if any(needle in head for needle in needles):
            return label
    return "other"


def _normalize_history(history: List) -> List[Dict[str, str]]:
    normalised: List[Dict[str, str]] = []
    for entry in history:
        if isinstance(entry, dict):
            normalised.append(
                {
                    "path": entry.get("path", ""),
                    "timestamp": entry.get("timestamp", _timestamp()),
                    "arguments": entry.get("arguments", ""),
                }
            )
        elif isinstance(entry, str):
            normalised.append({"path": entry, "timestamp": _timestamp(), "arguments": ""})
    return [item for item in normalised if item["path"]]


class ScriptRunnerWindow(QWidget):
    """Main application window with console, history and controls."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Script Runner")
        self.setWindowIcon(QIcon(resource_path("app_icon.ico")))
        self.setAcceptDrops(True)

        self.config = load_config()
        self.history = _normalize_history(self.config.get("history", []))
        stored_args = [arg for arg in self.config.get("argument_suggestions", []) if isinstance(arg, str)]
        self.argument_bank = list(dict.fromkeys(COMMON_ARGUMENTS + stored_args))
        self.profiles = [
            InterpreterProfile.from_dict(data) for data in self.config.get("interpreter_profiles", [])
        ]

        self.script_path: Optional[str] = None
        self.local_python: Optional[str] = None
        self.process = ScriptProcess(self)
        self.process.output_ready.connect(partial(self._append_output, stamp=False))
        self.process.error.connect(self._handle_process_error)
        self.process.finished.connect(self._process_finished)

        self._terminated_by_user = False
        self._log_cache: Dict[str, str] = {}
        self._current_stylesheet = ""

        self._build_ui()
        self.apply_theme(self.config.get("theme", "dark"))
        self._refresh_history()
        self._refresh_logs()
        self._refresh_templates()
        self._apply_profiles()
        self._bind_shortcuts()

        # UI layout and widgets
    def _build_ui(self) -> None:
        self.setObjectName("rootWindow")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        # Header with main actions
        header = QFrame()
        header.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 24, 24, 24)
        header_layout.setSpacing(18)

        self.script_label = QLabel("Script: none selected")
        self.script_label.setObjectName("scriptLabel")
        header_layout.addWidget(self.script_label, 1)

        self.browse_btn = self._make_button("Browse", self.browse_script)
        header_layout.addWidget(self.browse_btn)

        self.template_box = QComboBox()
        self.template_box.addItem("Insert Template…")
        self.template_box.currentIndexChanged.connect(self._apply_template)
        header_layout.addWidget(self.template_box)

        self.run_btn = self._make_button("Run", self.run_script)
        self.run_btn.setObjectName("runButton")
        header_layout.addWidget(self.run_btn)

        self.stop_btn = self._make_button("Stop", self.stop_script)
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.setEnabled(False)
        header_layout.addWidget(self.stop_btn)

        self.clear_btn = self._make_button("Clear", self.clear_output)
        header_layout.addWidget(self.clear_btn)

        self.save_btn = self._make_button("Save Log", self.save_log)
        header_layout.addWidget(self.save_btn)

        self.settings_btn = self._make_button("Settings", self.open_settings)
        header_layout.addWidget(self.settings_btn)

        layout.addWidget(header)

        # Split main area
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, 1)

        # Sidebar: history and logs
        sidebar = QFrame()
        sidebar.setObjectName("leftPanel")
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(16)

        self.sidebar_tabs = QTabWidget()
        side_layout.addWidget(self.sidebar_tabs, 1)

        # History tab
        history_page = QWidget()
        history_layout = QVBoxLayout(history_page)
        history_layout.setContentsMargins(12, 12, 12, 12)
        history_layout.setSpacing(10)

        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("Search history…")
        self.history_search.textChanged.connect(self._filter_history)
        history_layout.addWidget(self.history_search)

        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        self.history_list.itemDoubleClicked.connect(self._load_history_entry)
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._history_context_menu)
        history_layout.addWidget(self.history_list, 1)

        history_buttons = QHBoxLayout()
        history_buttons.setSpacing(8)
        history_buttons.addStretch()
        self.history_open_btn = self._make_button("Open", self._open_selected_history)
        history_buttons.addWidget(self.history_open_btn)
        self.history_delete_btn = self._make_button("Delete", self._delete_selected_history)
        history_buttons.addWidget(self.history_delete_btn)
        history_buttons.addStretch()
        history_layout.addLayout(history_buttons)

        self.sidebar_tabs.addTab(history_page, "History")

        # Logs tab
        logs_page = QWidget()
        logs_layout = QVBoxLayout(logs_page)
        logs_layout.setContentsMargins(12, 12, 12, 12)
        logs_layout.setSpacing(10)

        self.log_filter = QComboBox()
        self.log_filter.addItems(["All", "Errors", "Warnings", "Success"])
        self.log_filter.currentIndexChanged.connect(lambda _: self._refresh_logs())
        logs_layout.addWidget(self.log_filter)

        self.logs_list = QListWidget()
        self.logs_list.setObjectName("logsList")
        self.logs_list.itemDoubleClicked.connect(self._open_log)
        self.logs_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.logs_list.customContextMenuRequested.connect(self._logs_context_menu)
        logs_layout.addWidget(self.logs_list, 1)

        logs_buttons = QHBoxLayout()
        logs_buttons.setSpacing(8)
        logs_buttons.addStretch()
        self.logs_open_btn = self._make_button("Open", self._open_selected_log)
        logs_buttons.addWidget(self.logs_open_btn)
        self.logs_delete_btn = self._make_button("Delete", self._delete_selected_log)
        logs_buttons.addWidget(self.logs_delete_btn)
        logs_buttons.addStretch()
        logs_layout.addLayout(logs_buttons)

        self.sidebar_tabs.addTab(logs_page, "Logs")

        splitter.addWidget(sidebar)

        # Main panel
        main_panel = QFrame()
        main_panel.setObjectName("rightPanel")
        main_layout = QVBoxLayout(main_panel)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        controls = QFrame()
        controls.setObjectName("controlsFrame")
        controls_layout = QGridLayout(controls)
        controls_layout.setContentsMargins(24, 24, 24, 24)
        controls_layout.setHorizontalSpacing(24)
        controls_layout.setVerticalSpacing(18)
        controls.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        interpreter_label = QLabel("Interpreter")
        interpreter_label.setObjectName("fieldLabel")
        controls_layout.addWidget(interpreter_label, 0, 0)

        self.interpreter_box = QComboBox()
        self.interpreter_box.addItems(["Python", "Bash", "PowerShell", "Node.js"])
        self.interpreter_box.currentIndexChanged.connect(lambda _: self._refresh_templates())
        controls_layout.addWidget(self.interpreter_box, 0, 1)

        profile_label = QLabel("Profile")
        profile_label.setObjectName("fieldLabel")
        controls_layout.addWidget(profile_label, 1, 0)

        self.profile_box = QComboBox()
        self.profile_box.currentIndexChanged.connect(self._profile_changed)
        controls_layout.addWidget(self.profile_box, 1, 1)

        args_label = QLabel("Arguments")
        args_label.setObjectName("fieldLabel")
        controls_layout.addWidget(args_label, 2, 0)

        self.arg_input = QLineEdit()
        self.arg_input.setObjectName("argInput")
        self.arg_input.setPlaceholderText("Flags or parameters for your script")
        self.arg_input.textChanged.connect(self._validate_arguments)
        controls_layout.addWidget(self.arg_input, 2, 1)

        self.arg_completer = QCompleter(self.argument_bank, self)
        self.arg_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.arg_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.arg_input.setCompleter(self.arg_completer)

        main_layout.addWidget(controls)

        output_frame = QFrame()
        output_frame.setObjectName("outputFrame")
        output_layout = QVBoxLayout(output_frame)
        output_layout.setContentsMargins(24, 24, 24, 24)
        output_layout.setSpacing(16)
        output_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        output_label = QLabel("Console")
        output_label.setObjectName("sectionTitle")
        output_layout.addWidget(output_label)

        self.output_box = QTextEdit()
        self.output_box.setObjectName("outputBox")
        self.output_box.setReadOnly(True)
        self.output_box.setFont(QFont("Cascadia Mono", 11))
        self.highlighter = LogHighlighter(self.output_box.document())
        output_layout.addWidget(self.output_box, 1)

        console_row = QHBoxLayout()
        console_row.setSpacing(14)

        console_label = QLabel("Input")
        console_label.setObjectName("fieldLabel")
        console_row.addWidget(console_label)

        self.console_input = QLineEdit()
        self.console_input.setObjectName("consoleInput")
        self.console_input.setPlaceholderText("Type a response or command, press Enter to send")
        self.console_input.returnPressed.connect(self.send_console_input)
        self.console_input.setEnabled(False)
        console_row.addWidget(self.console_input, 1)

        self.send_btn = self._make_button("Send", self.send_console_input)
        self.send_btn.setEnabled(False)
        console_row.addWidget(self.send_btn)

        output_layout.addLayout(console_row)

        main_layout.addWidget(output_frame, 1)

        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(24, 14, 24, 14)
        status_layout.setSpacing(12)

        self.status_label = QLabel(self._ready_status())
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label, 1)

        main_layout.addWidget(status_frame)
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 6)
        main_layout.setStretch(2, 0)

        splitter.addWidget(main_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

    def _make_button(self, label: str, handler) -> QPushButton:
        btn = QPushButton(label)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(38)
        btn.clicked.connect(handler)
        return btn

    def _bind_shortcuts(self) -> None:
        shortcuts = [
            (QKeySequence("Ctrl+R"), self.run_script),
            (QKeySequence("Ctrl+Shift+R"), self.stop_script),
            (QKeySequence("Ctrl+L"), self.clear_output),
            (QKeySequence("Ctrl+O"), self.browse_script),
        ]
        for seq, handler in shortcuts:
            shortcut = QShortcut(seq, self)
            shortcut.activated.connect(handler)

    def _ready_status(self) -> str:
        return "Ready  •  Ctrl+R run  •  Ctrl+Shift+R stop  •  Ctrl+L clear"

    # Theme styling
    def apply_theme(self, theme: str) -> None:
        stylesheet = build_stylesheet(theme if theme in ("dark", "light") else "dark")
        self._current_stylesheet = stylesheet
        self.setStyleSheet(stylesheet)

    # Configuration dialogs
    def open_settings(self) -> None:
        dialog = SettingsDialog(self.config, self)
        if self._current_stylesheet:
            dialog.setStyleSheet(self._current_stylesheet)
        if not dialog.exec():
            return
        updates, actions = dialog.result_config()
        self.config.update(updates)
        self.profiles = [InterpreterProfile.from_dict(data) for data in self.config.get("interpreter_profiles", [])]
        self.apply_theme(self.config["theme"])
        self._apply_profiles()
        save_config(self.config)
        if actions.get("clear_history"):
            self._clear_history_entries()
        if actions.get("clear_logs"):
            self._clear_all_logs()

        # Script picking and drag/drop
    def browse_script(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Script", "", "Scripts (*.py *.sh *.ps1 *.js *.bat)")
        if path:
            self.load_script(path)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.endswith((".py", ".sh", ".ps1", ".js", ".bat")):
                self.load_script(path)

    def load_script(self, path: str) -> None:
        self.script_path = path
        self.script_label.setText(f"Script: {os.path.basename(path)}")
        interpreter = self._detect_interpreter(path)
        if interpreter:
            index = self.interpreter_box.findText(interpreter)
            if index >= 0:
                self.interpreter_box.setCurrentIndex(index)
        self.local_python = self._locate_local_python(path)
        self._remember_history(path)

    def _detect_interpreter(self, path: str) -> Optional[str]:
        ext = os.path.splitext(path)[1].lower()
        mapping = {".py": "Python", ".sh": "Bash", ".ps1": "PowerShell", ".js": "Node.js", ".bat": "Bash"}
        if ext in mapping:
            return mapping[ext]
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                head = handle.readline()
        except OSError:
            return None
        if "python" in head:
            return "Python"
        if "node" in head:
            return "Node.js"
        if "bash" in head or "sh" in head:
            return "Bash"
        if "powershell" in head.lower():
            return "PowerShell"
        return None

        # Script execution
    def run_script(self) -> None:
        if self.process.is_running():
            self._append_output("> A script is already running. Stop it first.", stamp=True)
            return
        if not self.script_path:
            self._append_output("> No script selected.", stamp=True)
            return
        try:
            args = shlex.split(self.arg_input.text(), posix=(os.name != "nt")) if self.arg_input.text() else []
        except ValueError as error:
            self._append_output(f"> Argument parsing error: {error}", stamp=True)
            return
        for argument in args:
            if argument not in self.argument_bank:
                self.argument_bank.append(argument)
        dynamic = [item for item in self.argument_bank if item not in COMMON_ARGUMENTS]
        self.config["argument_suggestions"] = dynamic[-60:]
        save_config(self.config)
        self._update_completer()

        interpreter = self.interpreter_box.currentText()
        program, extra = self._resolve_interpreter(interpreter)
        arguments = extra + [self.script_path, *args]

        if self.config.get("external_console", False):
            self._launch_external(program, arguments)
            return

        self.output_box.clear()
        preview = " ".join(shlex.quote(part) for part in [program, *arguments])
        self._append_output(f"> Running {os.path.basename(self.script_path)}", stamp=True)
        self._append_output(f"> {preview}", stamp=True)

        working_dir = os.path.dirname(self.script_path)
        self.process.start(program, arguments, working_dir)
        self._terminated_by_user = False
        self._set_running_state(True)

    def _resolve_interpreter(self, name: str) -> tuple[str, List[str]]:
        profile = next((p for p in self.profiles if p.name == self.profile_box.currentText()), None)
        if profile and profile.command:
            return profile.command, list(profile.arguments)
        if name == "Python" and self.local_python:
            return self.local_python, []
        default_map = {
            "Python": (self._python_exec(), []),
            "Bash": ("bash", []),
            "PowerShell": ("powershell", ["-ExecutionPolicy", "Bypass", "-File"]),
            "Node.js": ("node", []),
        }
        return default_map.get(name, ("python", []))

    def _python_exec(self) -> str:
        env_override = os.environ.get("SCRIPT_RUNNER_PYTHON")
        if env_override:
            return env_override

        config_default = self.config.get("fallback_python")
        if config_default:
            return config_default

        base_exec = getattr(sys, "_base_executable", "")
        if base_exec and os.path.isfile(base_exec):
            return base_exec

        executable = sys.executable or ""
        base = os.path.basename(executable).lower()
        if base.startswith("python"):
            return executable

        # When packaged, fall back to system python on PATH.
        return "python"

    def _locate_local_python(self, script_path: str) -> Optional[str]:
        if not script_path:
            return None
        directory = os.path.abspath(os.path.dirname(script_path))
        candidates = [".venv", "venv", "env"]
        while True:
            for name in candidates:
                candidate_dir = os.path.join(directory, name)
                if os.path.isdir(candidate_dir):
                    if sys.platform.startswith("win"):
                        python_path = os.path.join(candidate_dir, "Scripts", "python.exe")
                    else:
                        python_path = os.path.join(candidate_dir, "bin", "python")
                    if os.path.isfile(python_path):
                        return python_path
            new_directory = os.path.dirname(directory)
            if new_directory == directory:
                break
            directory = new_directory
        return None

    def _launch_external(self, program: str, arguments: List[str]) -> None:
        try:
            creation_flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            kwargs = {"creationflags": creation_flags} if creation_flags else {}
            subprocess.Popen([program, *arguments], **kwargs)
            self._append_output("> Script launched in a separate console.", stamp=True)
            self.status_label.setText("External console")
        except Exception as error:
            self._append_output(f"> Failed to launch external console: {error}", stamp=True)
            self.status_label.setText("Launch failed")

    def stop_script(self) -> None:
        if not self.process.is_running():
            self._append_output("> There is no running script.", stamp=True)
            return
        self._append_output("> Stopping script…", stamp=True)
        self._terminated_by_user = True
        self.process.terminate()

    def _process_finished(self, exit_code: int, status: QProcess.ExitStatus) -> None:
        if self._terminated_by_user:
            message = f"> Script stopped by user (exit code {exit_code})."
        elif status == QProcess.Crashed:
            message = f"> Script crashed with exit code {exit_code}."
        else:
            message = f"> Script finished with exit code {exit_code}."
        self._append_output(message, stamp=True)
        self._set_running_state(False)

    def _handle_process_error(self, error, message: str) -> None:
        self._append_output(f"> Process error: {message}", stamp=True)
        self._set_running_state(False)

    def _set_running_state(self, running: bool) -> None:
        self.run_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.console_input.setEnabled(running)
        self.send_btn.setEnabled(running)
        self.status_label.setText("Running" if running else self._ready_status())
        if not running:
            self.console_input.clear()
            old_process = self.process
            self.process = ScriptProcess(self)
            self.process.output_ready.connect(partial(self._append_output, stamp=False))
            self.process.error.connect(self._handle_process_error)
            self.process.finished.connect(self._process_finished)
            self._terminated_by_user = False
            if old_process is not None:
                old_process.deleteLater()

    def send_console_input(self) -> None:
        text = self.console_input.text()
        if not self.process.is_running():
            if text:
                self._append_output(f"$ {text}", stamp=True)
            self.console_input.clear()
            return

        display = f"$ {text}" if text else "$"
        self._append_output(display, stamp=True)
        self.process.write(f"{text}\n")
        if text and text not in self.argument_bank:
            self.argument_bank.append(text)
            dynamic = [item for item in self.argument_bank if item not in COMMON_ARGUMENTS]
            self.config["argument_suggestions"] = dynamic[-60:]
            save_config(self.config)
            self._update_completer()
        self.console_input.clear()

    def clear_output(self) -> None:
        self.output_box.clear()
        self.status_label.setText("Console cleared")

        # History tracking
    def _remember_history(self, path: str) -> None:
        entry = {"path": path, "timestamp": _timestamp(), "arguments": self.arg_input.text()}
        self.history = [item for item in self.history if item["path"] != path]
        self.history.insert(0, entry)
        self.history = self.history[:40]
        self.config["history"] = self.history
        save_config(self.config)
        self._refresh_history()

    def _refresh_history(self) -> None:
        query = self.history_search.text().lower()
        self.history_list.clear()
        for item in self.history:
            text = f'{item["timestamp"]}  |  {os.path.basename(item["path"])}'
            widget = QListWidgetItem(text)
            widget.setData(Qt.UserRole, item)
            match = query in text.lower() or query in item["path"].lower()
            self.history_list.addItem(widget)
            widget.setHidden(bool(query) and not match)

    def _filter_history(self, text: str) -> None:
        self._refresh_history()
        for index in range(self.history_list.count()):
            item = self.history_list.item(index)
            match = text.lower() in (item.data(Qt.UserRole)["path"].lower())
            item.setHidden(not match)

    def _load_history_entry(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.UserRole)
        path = data["path"]
        if os.path.exists(path):
            self.load_script(path)
            self.arg_input.setText(data.get("arguments", ""))
        else:
            self._append_output(f"> File not found: {path}", stamp=True)

    def _open_selected_history(self) -> None:
        item = self.history_list.currentItem()
        if item:
            self._load_history_entry(item)

    def _history_context_menu(self, position) -> None:
        item = self.history_list.itemAt(position)
        menu = QMenu(self)
        if item:
            remove_action = menu.addAction("Remove entry")
            if menu.exec(self.history_list.mapToGlobal(position)) == remove_action:
                self._delete_selected_history()
        else:
            clear_action = menu.addAction("Clear history")
            if menu.exec(self.history_list.mapToGlobal(position)) == clear_action:
                self._clear_history_entries()

    def _delete_selected_history(self) -> None:
        item = self.history_list.currentItem()
        if not item:
            return
        data = item.data(Qt.UserRole)
        self.history = [entry for entry in self.history if entry["path"] != data["path"]]
        self.config["history"] = self.history
        save_config(self.config)
        self._refresh_history()

    def _clear_history_entries(self) -> None:
        self.history.clear()
        self.config["history"] = []
        save_config(self.config)
        self._refresh_history()

    # Log handling
    def _refresh_logs(self) -> None:
        self.logs_list.clear()
        filter_map = {0: None, 1: "error", 2: "warning", 3: "success"}
        active_filter = filter_map.get(self.log_filter.currentIndex())

        try:
            files = sorted(
                (os.path.join(LOG_DIR, name) for name in os.listdir(LOG_DIR) if name.lower().endswith(".log")),
                key=os.path.getmtime,
                reverse=True,
            )
        except OSError:
            files = []

        for full_path in files:
            label = os.path.basename(full_path)
            category = self._log_cache.get(full_path) or _classify_log(full_path)
            self._log_cache[full_path] = category
            if active_filter and category != active_filter:
                continue
            display = f"{label}  •  {category.upper()}"
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, full_path)
            self.logs_list.addItem(item)

    def _open_log(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.UserRole)
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _open_selected_log(self) -> None:
        item = self.logs_list.currentItem()
        if not item:
            return
        path = item.data(Qt.UserRole)
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _logs_context_menu(self, position) -> None:
        item = self.logs_list.itemAt(position)
        menu = QMenu(self)
        if item:
            delete_action = menu.addAction("Delete log")
            if menu.exec(self.logs_list.mapToGlobal(position)) == delete_action:
                self._delete_selected_log()
        else:
            clear_action = menu.addAction("Clear all logs")
            if menu.exec(self.logs_list.mapToGlobal(position)) == clear_action:
                self._clear_all_logs()

    def _delete_selected_log(self) -> None:
        item = self.logs_list.currentItem()
        if not item:
            return
        path = item.data(Qt.UserRole)
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
        self._refresh_logs()

    def _clear_all_logs(self) -> None:
        for entry in os.listdir(LOG_DIR):
            full_path = os.path.join(LOG_DIR, entry)
            if entry.lower().endswith(".log") and os.path.isfile(full_path):
                try:
                    os.remove(full_path)
                except OSError:
                    pass
        self._refresh_logs()

    def save_log(self) -> None:
        if not self.output_box.toPlainText().strip():
            self._append_output("> Nothing to save yet.", stamp=True)
            return
        timestamp = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base = os.path.splitext(os.path.basename(self.script_path or "output"))[0]
        filename = f"{base}_{timestamp}.log"
        path = os.path.join(LOG_DIR, filename)
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(self.output_box.toPlainText())
            self._append_output(f"> Log saved to {path}", stamp=True)
            self._refresh_logs()
        except OSError as error:
            self._append_output(f"> Failed to save log: {error}", stamp=True)

        # Templates and interpreter profiles
    def _refresh_templates(self) -> None:
        current = self.template_box.currentText()
        interpreter = self.interpreter_box.currentText()
        self.template_box.blockSignals(True)
        self.template_box.clear()
        self.template_box.addItem("Insert Template…")
        for label, snippet in COMMAND_TEMPLATES.get(interpreter, []):
            self.template_box.addItem(label, snippet)
        self.template_box.setCurrentIndex(0)
        self.template_box.blockSignals(False)

    def _apply_template(self, index: int) -> None:
        if index <= 0:
            return
        snippet = self.template_box.currentData()
        if snippet:
            self.arg_input.setText(snippet)
        self.template_box.setCurrentIndex(0)

    def _apply_profiles(self) -> None:
        self.profile_box.blockSignals(True)
        self.profile_box.clear()
        self.profile_box.addItem("Default")
        for profile in self.profiles:
            self.profile_box.addItem(profile.name)
        self.profile_box.blockSignals(False)
        active = self.config.get("active_profile")
        if active:
            index = self.profile_box.findText(active)
            if index >= 0:
                self.profile_box.setCurrentIndex(index)
        else:
            self.profile_box.setCurrentIndex(0)

    def _profile_changed(self, index: int) -> None:
        name = self.profile_box.itemText(index)
        if name == "Default":
            self.config["active_profile"] = None
        else:
            self.config["active_profile"] = name
        save_config(self.config)

        # Argument helpers
    def _update_completer(self) -> None:
        model = QStringListModel(self.argument_bank)
        self.arg_completer.setModel(model)

    def _validate_arguments(self, text: str) -> None:
        if not text:
            self.arg_input.setProperty("error", False)
            self.arg_input.style().unpolish(self.arg_input)
            self.arg_input.style().polish(self.arg_input)
            return
        try:
            shlex.split(text, posix=(os.name != "nt"))
        except ValueError:
            self.arg_input.setStyleSheet("border: 2px solid #ff5b5b;")
        else:
            self.arg_input.setStyleSheet("")

        # Output helpers
    def _append_output(self, text: str, stamp: bool = False) -> None:
        if not text:
            return
        payload = _with_timestamp(text) if stamp else text
        cursor = self.output_box.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(payload if payload.endswith("\n") else f"{payload}\n")
        self.output_box.setTextCursor(cursor)
        self.output_box.ensureCursorVisible()

        # Autorun support
    def schedule_autorun(self) -> None:
        if not self.config.get("auto_run"):
            return
        if len(sys.argv) <= 1:
            return
        candidate = sys.argv[1]
        if not os.path.isfile(candidate):
            self._append_output(f"> Auto-run skipped: not a file -> {candidate}", stamp=True)
            return

        def trigger() -> None:
            self.load_script(candidate)
            self.run_script()

        QTimer.singleShot(0, trigger)


