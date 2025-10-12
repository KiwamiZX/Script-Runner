from __future__ import annotations

import datetime as dt
from typing import Optional

from PySide6.QtCore import QProcess, QObject, Signal


class ScriptProcess(QObject):
    """Wrapper around QProcess adding timestamped output."""

    output_ready = Signal(str)
    finished = Signal(int, QProcess.ExitStatus)
    error = Signal(QProcess.ProcessError, str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._handle_output)
        self._process.errorOccurred.connect(self._handle_error)
        self._process.finished.connect(self._forward_finished)

    @property
    def qprocess(self) -> QProcess:
        return self._process

    def start(self, program: str, arguments: list[str], working_dir: str | None = None) -> None:
        if working_dir:
            self._process.setWorkingDirectory(working_dir)
        self._process.setProgram(program)
        self._process.setArguments(arguments)
        self._process.start()

    def write(self, text: str) -> None:
        self._process.write(text.encode())

    def terminate(self) -> None:
        self._process.kill()

    def is_running(self) -> bool:
        return self._process.state() != QProcess.NotRunning

    def _handle_output(self) -> None:
        data = self._process.readAllStandardOutput()
        line = bytes(data).decode(errors="replace")
        timestamp = dt.datetime.now().strftime("[%H:%M:%S] ")
        self.output_ready.emit("".join(f"{timestamp}{segment}" for segment in line.splitlines(True)))

    def _handle_error(self, err: QProcess.ProcessError) -> None:
        message = self._process.errorString()
        self.error.emit(err, message)

    def _forward_finished(self, exit_code: int, status: QProcess.ExitStatus) -> None:
        self.finished.emit(exit_code, status)
