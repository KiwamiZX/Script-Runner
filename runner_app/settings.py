from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
)


@dataclass
class InterpreterProfile:
    name: str
    command: str
    arguments: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "command": self.command, "arguments": self.arguments}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterpreterProfile":
        return cls(
            name=data.get("name", "Custom"),
            command=data.get("command", ""),
            arguments=list(data.get("arguments", [])),
        )


class SettingsDialog(QDialog):
    """Collects basic preferences plus interpreter profile configuration."""

    def __init__(self, config: Dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)

        self._config = config
        self._profiles = [
            InterpreterProfile.from_dict(item)
            for item in config.get("interpreter_profiles", [])
        ]
        self._clear_history = False
        self._clear_logs = False

        layout = QVBoxLayout(self)

        self.theme_checkbox = QCheckBox("Use dark theme")
        self.theme_checkbox.setChecked(config.get("theme", "dark") == "dark")
        layout.addWidget(self.theme_checkbox)

        self.console_checkbox = QCheckBox("Run in external console")
        self.console_checkbox.setChecked(config.get("external_console", False))
        layout.addWidget(self.console_checkbox)

        self.autorun_checkbox = QCheckBox(
            "Automatically run script at startup (if opened with one)"
        )
        self.autorun_checkbox.setChecked(config.get("auto_run", False))
        layout.addWidget(self.autorun_checkbox)

        # Interpreter profile editor (lightweight)
        form = QFormLayout()
        self.profile_name = QLineEdit()
        self.profile_command = QLineEdit()
        self.profile_args = QLineEdit()
        form.addRow("Profile name", self.profile_name)
        form.addRow("Command", self.profile_command)
        form.addRow("Default arguments", self.profile_args)
        layout.addLayout(form)

        python_row = QHBoxLayout()
        self.python_path_edit = QLineEdit(config.get("fallback_python", ""))
        self.python_path_edit.setPlaceholderText("Path to python.exe (optional)")
        python_row.addWidget(self.python_path_edit)
        browse_python = QPushButton("Browse")
        browse_python.clicked.connect(self._browse_python)
        python_row.addWidget(browse_python)
        layout.addLayout(python_row)

        self.profile_list = QListWidget()
        layout.addWidget(self.profile_list)
        self.profile_list.itemSelectionChanged.connect(self._load_selected_profile)

        button_row = QHBoxLayout()
        self.save_profile_button = QPushButton("Save profile")
        self.save_profile_button.clicked.connect(self._save_profile)
        button_row.addWidget(self.save_profile_button)
        self.delete_profile_button = QPushButton("Delete profile")
        self.delete_profile_button.clicked.connect(self._delete_profile)
        button_row.addWidget(self.delete_profile_button)
        layout.addLayout(button_row)

        maintenance_row = QHBoxLayout()
        self.clear_history_button = QPushButton("Clear history")
        self.clear_history_button.clicked.connect(self._mark_clear_history)
        maintenance_row.addWidget(self.clear_history_button)
        self.clear_logs_button = QPushButton("Clear logs")
        self.clear_logs_button.clicked.connect(self._mark_clear_logs)
        maintenance_row.addWidget(self.clear_logs_button)
        layout.addLayout(maintenance_row)

        self._refresh_profile_list()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_profile_list(self, selected: int | None = None) -> None:
        self.profile_list.clear()
        for profile in self._profiles:
            QListWidgetItem(profile.name, self.profile_list)
        if selected is not None and 0 <= selected < len(self._profiles):
            self.profile_list.setCurrentRow(selected)

    def _load_selected_profile(self) -> None:
        index = self.profile_list.currentRow()
        if index < 0 or index >= len(self._profiles):
            self.profile_name.clear()
            self.profile_command.clear()
            self.profile_args.clear()
            return
        profile = self._profiles[index]
        self.profile_name.setText(profile.name)
        self.profile_command.setText(profile.command)
        self.profile_args.setText(" ".join(profile.arguments))

    def _save_profile(self) -> None:
        selection = self.profile_list.currentRow()
        profile = self._capture_profile_fields()
        if not profile:
            return
        if 0 <= selection < len(self._profiles):
            self._profiles[selection] = profile
            target = selection
        else:
            self._profiles.append(profile)
            target = len(self._profiles) - 1
        self._refresh_profile_list(target)

    def _delete_profile(self) -> None:
        selection = self.profile_list.currentRow()
        if 0 <= selection < len(self._profiles):
            self._profiles.pop(selection)
            self._refresh_profile_list()
            self.profile_name.clear()
            self.profile_command.clear()
            self.profile_args.clear()

    def _capture_profile_fields(self) -> InterpreterProfile | None:
        name = self.profile_name.text().strip()
        command = self.profile_command.text().strip()
        arguments = self.profile_args.text().split()
        if not any([name, command, arguments]):
            return None
        return InterpreterProfile(name=name or "Custom", command=command, arguments=arguments)

    def _mark_clear_history(self) -> None:
        self._clear_history = True

    def _mark_clear_logs(self) -> None:
        self._clear_logs = True

    def _accept(self) -> None:
        profile = self._capture_profile_fields()
        if profile:
            selection = self.profile_list.currentRow()
            if 0 <= selection < len(self._profiles):
                self._profiles[selection] = profile
            else:
                self._profiles.append(profile)
        self.accept()

    def result_config(self) -> tuple[Dict[str, Any], Dict[str, bool]]:
        data = {
            "theme": "dark" if self.theme_checkbox.isChecked() else "light",
            "external_console": self.console_checkbox.isChecked(),
            "auto_run": self.autorun_checkbox.isChecked(),
            "interpreter_profiles": [profile.to_dict() for profile in self._profiles],
            "fallback_python": self.python_path_edit.text().strip(),
        }
        tasks = {"clear_history": self._clear_history, "clear_logs": self._clear_logs}
        return data, tasks

    def _browse_python(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Python executable", "", "Python Executable (python*.exe);;All Files (*)")
        if path:
            self.python_path_edit.setText(path)
