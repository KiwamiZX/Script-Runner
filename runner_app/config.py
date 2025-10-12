from __future__ import annotations

import json
from typing import Any, Dict

from .paths import CONFIG_PATH

DEFAULT_CONFIG: Dict[str, Any] = {
    "theme": "dark",
    "history": [],
    "external_console": False,
    "auto_run": False,
    "argument_suggestions": [],
    "interpreter_profiles": [],
    "active_profile": None,
}


def load_config() -> Dict[str, Any]:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return DEFAULT_CONFIG.copy()
    except Exception:
        return DEFAULT_CONFIG.copy()

    merged = DEFAULT_CONFIG.copy()
    merged.update(data)
    return merged


def save_config(config: Dict[str, Any]) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2)
    except Exception:
        # Persisting config failures should not crash the UI.
        pass
