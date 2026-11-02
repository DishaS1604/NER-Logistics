"""Data-access layer. Today: one JSON file. Later: replace with database / API calls."""
import json
import os
import tempfile
from pathlib import Path

from .seed import initial_state

DEFAULT_PATH = Path(os.environ.get("NER_STATE_FILE") or Path(__file__).resolve().parent.parent / "data" / "state.json")


def load_state(now, path=DEFAULT_PATH):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return initial_state(now)


def save_state(state, path=DEFAULT_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, path)  # atomic write so a crash never leaves a half-written file


def clear_state(path=DEFAULT_PATH):
    try:
        os.remove(path)
    except OSError:
        pass
