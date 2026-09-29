"""
Helper utilities for configuration loading, path resolution, and serialization.
"""

from pathlib import Path
from typing import Any
import yaml


def get_project_root() -> Path:
    """Return the absolute path to the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def load_yaml_config(relative_path: str) -> dict[str, Any]:
    """
    Load a YAML configuration file relative to the project root.
    """
    root = get_project_root()
    config_path = root / relative_path
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_directory(path: str | Path) -> Path:
    """Ensure directory exists and return Path object."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
