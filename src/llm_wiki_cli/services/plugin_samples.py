"""Bundled sample plugin export helpers."""

from __future__ import annotations

import shutil
import warnings
from importlib import resources
from pathlib import Path
from typing import Any

from .plugins import MANIFEST_FILENAME, PluginError

_SAMPLES = {
    "documentation-hooks": "Documentation hooks sample plugin",
}
_DEPRECATED_SAMPLE_ALIASES = {
    "m4-documentation-hooks": "documentation-hooks",
}
_RESOURCE_ROOT = ("examples", "plugins")


def list_samples() -> list[dict[str, str]]:
    """Return bundled sample plugins in deterministic order."""
    return [
        {"id": sample_id, "description": _SAMPLES[sample_id]}
        for sample_id in sorted(_SAMPLES)
    ]


def export_sample(
    sample_id: str,
    dest: str | Path,
    *,
    force: bool = False,
    root: str | Path = ".",
) -> dict[str, Any]:
    """Copy a bundled plugin sample to ``dest``."""
    canonical_id = _resolve_sample_id(sample_id)
    source = _sample_resource(canonical_id)
    target = _resolve_destination(dest, root=root)
    _prepare_destination(target, force=force)
    _copy_resource_tree(source, target)
    return {"id": canonical_id, "path": str(target)}


def _resolve_sample_id(sample_id: str) -> str:
    canonical_id = _DEPRECATED_SAMPLE_ALIASES.get(sample_id, sample_id)
    if canonical_id != sample_id:
        warnings.warn(
            f"Plugin sample {sample_id!r} is deprecated; use "
            f"{canonical_id!r} instead.",
            FutureWarning,
            stacklevel=3,
        )
    if canonical_id not in _SAMPLES:
        available = ", ".join(sorted(_SAMPLES))
        raise PluginError(
            f"Unknown plugin sample {sample_id!r}. Available: {available}"
        )
    return canonical_id


def _sample_resource(sample_id: str):
    if sample_id not in _SAMPLES:
        available = ", ".join(sorted(_SAMPLES))
        raise PluginError(
            f"Unknown plugin sample {sample_id!r}. Available: {available}"
        )

    resource = resources.files("llm_wiki_cli")
    for part in (*_RESOURCE_ROOT, sample_id):
        resource = resource.joinpath(part)
    if not resource.is_dir():
        raise PluginError(f"Bundled plugin sample is unavailable: {sample_id}")
    return resource


def _resolve_destination(dest: str | Path, *, root: str | Path) -> Path:
    raw = Path(dest).expanduser()
    project_root = Path(root).resolve()
    path = raw if raw.is_absolute() else project_root / raw
    resolved = path.resolve()
    if resolved.name in {"", ".", ".."}:
        raise PluginError(f"Invalid plugin sample destination: {dest}")
    if not raw.is_absolute():
        try:
            resolved.relative_to(project_root)
        except ValueError as exc:
            raise PluginError(
                f"Plugin sample destination must stay inside the project root: {dest}"
            ) from exc
    return resolved


def _prepare_destination(path: Path, *, force: bool) -> None:
    if not path.exists():
        return
    if not force:
        raise PluginError(f"Plugin sample destination already exists: {path}")
    if path.is_dir():
        if any(path.iterdir()) and not (path / MANIFEST_FILENAME).is_file():
            raise PluginError(
                f"Refusing to overwrite non-plugin sample directory: {path}"
            )
        shutil.rmtree(path)
        return
    path.unlink()


def _copy_resource_tree(source, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=False)
    for child in source.iterdir():
        if child.name == "__pycache__" or child.name.endswith((".pyc", ".pyo")):
            continue
        child_target = target / child.name
        if child.is_dir():
            _copy_resource_tree(child, child_target)
        else:
            child_target.write_bytes(child.read_bytes())
