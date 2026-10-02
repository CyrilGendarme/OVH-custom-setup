import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = Path(r"c:\Users\User\Desktop\musique\online\dj gratuit\ovh\config.json")


def _load_config() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {}

    with CONFIG_FILE.open(encoding="utf-8") as config_file:
        return json.load(config_file)


CONFIG = _load_config()


def resolve_path(config_path: str) -> Path:
    path = Path(config_path)
    return path if path.is_absolute() else ROOT_DIR / path