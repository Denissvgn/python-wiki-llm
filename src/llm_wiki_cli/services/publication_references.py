"""Explicit, inert reference inputs for public documentation review.

Each declared provider kind is served by a
:class:`~.reference_providers.ReferenceProvider` of the active domain pack.
"""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Mapping

from .knowledge_evidence import hash_json
from .publication_config import publication_path
from .reference_providers import reference_provider


MAX_REFERENCE_BYTES = 8 * 1024 * 1024
MAX_CAPTURE_BYTES = 64 * 1024 * 1024


def reference_identity(provider: str, configuration: Mapping[str, Any]) -> str:
    return hash_json({"provider": provider, "configuration": configuration})


def _installed_contract(kind, cache):
    """Capture each opt-in provider once during this observation."""
    if kind not in cache:
        cache[kind] = reference_provider(kind).capture()
    return cache[kind]


def capture_reference_inputs(config, baseline, root, session):
    """Read current and former providers through the caller's guarded session."""
    declarations = {}
    for policy in ([] if baseline is None else [baseline["config"]]) + [config]:
        for provider, configuration in policy.get("reference_providers", {}).items():
            key = reference_identity(provider, configuration)
            declarations[key] = (provider, configuration)
    if not declarations:
        return {}

    captured = {}
    installed = {}
    total = 0
    for key, (provider, configuration) in sorted(declarations.items()):
        if "path" not in configuration:
            contract = deepcopy(_installed_contract(configuration["kind"], installed))
        else:
            path = publication_path(root, configuration["path"])
            contract = None
            if path.exists():
                raw = session.read(configuration["path"], MAX_REFERENCE_BYTES)
                contract = reference_provider(configuration["kind"]).parse(raw)
        total += len(
            json.dumps(
                contract, sort_keys=True, ensure_ascii=False, allow_nan=False
            ).encode("utf-8")
        )
        if total > MAX_CAPTURE_BYTES:
            raise ValueError(
                "Captured reference contracts exceed the publication budget"
            )
        captured[key] = {
            "provider": provider,
            "configuration": deepcopy(configuration),
            "contract": contract,
        }
    return captured


def recheck_reference_inputs(captured, root):
    """Recheck missing files and installed declarations after capture."""
    if not captured:
        return
    installed = {}
    for reference in captured.values():
        configuration = reference["configuration"]
        if "path" not in configuration:
            if (
                _installed_contract(configuration["kind"], installed)
                != reference["contract"]
            ):
                label = reference_provider(configuration["kind"]).label
                raise ValueError(
                    f"Installed {label} declarations changed during publication capture"
                )
        elif (
            reference["contract"] is None
            and publication_path(root, configuration["path"]).exists()
        ):
            raise ValueError("Reference contract appeared during publication capture")


def reference_dependency_basis(dep, basis, providers):
    """Commit a complete reference or the part of it the dependency selects."""
    configuration = providers.get(dep["reference"])
    if configuration is None:
        return None
    key = reference_identity(dep["reference"], configuration)
    reference = basis.get("references", {}).get(key)
    if reference is None or reference["contract"] is None:
        return None
    selected = reference_provider(configuration["kind"]).select(
        reference["contract"], dep
    )
    if selected is None:
        return None
    return {"provider": deepcopy(configuration), "contract": selected}
