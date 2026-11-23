"""Configuration loading and validation for Phase 1."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "sources.yaml"


def load_configuration(
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    """Load and minimally validate the Phase 1 configuration."""

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    with config_path.open(encoding="utf-8") as config_file:
        configuration = yaml.safe_load(config_file)

    if not isinstance(configuration, dict):
        raise ValueError("Configuration must contain a YAML object.")

    if "database" not in configuration:
        raise ValueError("Configuration is missing 'database'.")

    if "sources" not in configuration:
        raise ValueError("Configuration is missing 'sources'.")

    if not isinstance(configuration["sources"], dict):
        raise ValueError("'sources' must contain a YAML object.")

    return configuration


def enabled_sources(
    configuration: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return only enabled source configurations."""

    return {
        name: settings
        for name, settings in configuration["sources"].items()
        if settings.get("enabled", False)
    }
