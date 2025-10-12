from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from .ui.main_window import ScriptRunnerWindow
from .paths import resource_path


def run(argv: list[str]) -> int:
    app = QApplication(argv)
    app.setWindowIcon(QIcon(resource_path("app_icon.ico")))
    window = ScriptRunnerWindow()
    window.resize(1100, 680)

    if len(argv) > 1:
        path = argv[1]
        window.load_script(path)

    window.show()
    window.schedule_autorun()
    return app.exec()


def main() -> int:
    return run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
