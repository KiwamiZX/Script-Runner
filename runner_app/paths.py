from __future__ import annotations

import os
import sys

APP_DIR = os.path.join(os.path.expanduser("~"), ".script_runner")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
LOG_DIR = os.path.join(APP_DIR, "logs")

os.makedirs(APP_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def resource_path(relative_path: str) -> str:
    """Resolve resource paths that work for PyInstaller bundles and dev runs."""
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative_path)
