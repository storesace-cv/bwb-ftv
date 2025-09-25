"""Helpers for persisting active ReportBro model selections."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, MutableMapping

from utils.paths import get_project_root

PROJECT_ROOT = get_project_root()
ACTIVE_MODELS_PATH = PROJECT_ROOT / "app" / "templates_store" / "active_models.json"


def _ensure_absolute(path_value: str | Path | None) -> Path | None:
    """Return ``path_value`` as an absolute :class:`Path` or ``None``."""

    if not path_value:
        return None

    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    else:
        path = path.resolve()
    return path


def _serialise_path(path_value: str | Path | None) -> str:
    """Serialise ``path_value`` into a string suitable for JSON storage."""

    absolute = _ensure_absolute(path_value)
    if absolute is None:
        return ""

    try:
        return str(absolute.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(absolute)


def load_active_models() -> dict[str, dict[str, str]]:
    """Load the mapping of active models from disk.

    The result always contains normalised absolute paths represented as strings.
    Missing files yield an empty mapping.
    """

    if not ACTIVE_MODELS_PATH.exists():
        return {}

    try:
        raw = json.loads(ACTIVE_MODELS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    if not isinstance(raw, Mapping):
        return {}

    models: dict[str, dict[str, str]] = {}
    for key, value in raw.items():
        if not isinstance(value, Mapping):
            continue

        folder_raw = value.get("folder") if isinstance(value, Mapping) else None
        template_raw = value.get("template") if isinstance(value, Mapping) else None
        folder_abs = _ensure_absolute(folder_raw)
        template_abs = _ensure_absolute(template_raw)
        models[key] = {
            "folder": str(folder_abs) if folder_abs else "",
            "template": str(template_abs) if template_abs else "",
        }

    return models


def save_active_models(mapping: Mapping[str, Mapping[str, str | Path | None]]) -> None:
    """Persist ``mapping`` to :data:`ACTIVE_MODELS_PATH` as JSON."""

    serialised: MutableMapping[str, dict[str, str]] = {}
    for key, value in mapping.items():
        if not isinstance(value, Mapping):
            continue

        serialised[key] = {
            "folder": _serialise_path(value.get("folder")),
            "template": _serialise_path(value.get("template")),
        }

    ACTIVE_MODELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_MODELS_PATH.write_text(
        json.dumps(serialised, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def save_active_model(
    identifier: str, folder: str | Path | None, template: str | Path | None
) -> None:
    """Update the mapping with ``identifier`` using ``folder`` and ``template``."""

    models = load_active_models()
    models[identifier] = {
        "folder": str(_ensure_absolute(folder) or ""),
        "template": str(_ensure_absolute(template) or ""),
    }
    save_active_models(models)


def resolve_active_model_template(identifier: str) -> Path | None:
    """Return the resolved template path for ``identifier`` if available."""

    mapping = load_active_models()
    data = mapping.get(identifier)
    if not data:
        return None

    return _ensure_absolute(data.get("template"))
