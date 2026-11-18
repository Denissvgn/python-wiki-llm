"""Benchmark, report and release helper scripts load without running anything."""

from __future__ import annotations

from pathlib import Path

from release import native_published_artifacts
from tests import (
    knowledge_locality_benchmark,
    knowledge_pack_scale,
    knowledge_performance_fixture,
    knowledge_runtime_benchmark,
    run_provider_artifact_checks,
    verify_20260910_120000_report,
    verify_v201_report,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    knowledge_locality_benchmark,
    knowledge_pack_scale,
    knowledge_performance_fixture,
    knowledge_runtime_benchmark,
    run_provider_artifact_checks,
    verify_20260910_120000_report,
    verify_v201_report,
    native_published_artifacts,
)


def test_helper_scripts_import_from_this_checkout_without_side_effects(tmp_path, monkeypatch):
    # Importing happened at collection; nothing may have written beside them.
    for module in SCRIPTS:
        path = Path(module.__file__).resolve()
        assert path.is_relative_to(ROOT)
        assert path.parent.name in {"tests", "release"}
    assert callable(run_provider_artifact_checks.main)
    assert callable(native_published_artifacts.main)
