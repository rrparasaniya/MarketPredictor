"""Save and load trained models with metadata."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import joblib

from settings import resolve_path


def artifact_path(cfg: dict[str, Any], kind: str, index_name: str, run: str) -> Path:
    """Where the ``kind`` model (e.g. ``direction``) for an index/run is stored."""
    return resolve_path(cfg["models"]["artifacts_dir"]) / f"{index_name}_{run}_{kind}.joblib"


def save_artifact(path: Path, model: Any, meta: dict[str, Any]) -> None:
    """Write ``{"model", "meta"}`` with joblib (atomic replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {**meta, "saved_at": datetime.now().astimezone().isoformat()}
    tmp = path.with_suffix(".tmp")
    joblib.dump({"model": model, "meta": meta}, tmp)
    tmp.replace(path)


def load_artifact(path: Path) -> tuple[Any, dict[str, Any]] | None:
    """Return ``(model, meta)``, or None if the artifact doesn't exist."""
    if not path.exists():
        return None
    obj = joblib.load(path)
    return obj["model"], obj["meta"]
