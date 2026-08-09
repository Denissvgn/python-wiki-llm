"""Actual-checkout helper planning parity for non-editable installations."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import TypedDict, cast

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
LOCAL_VENV_PIP = PROJECT_ROOT / ".venv" / "bin" / "pip"
_RESULT_PREFIX = "WCI_HELPER_PLAN="
_CANDIDATE_ROOT_FILES = (
    "LICENSE",
    "MANIFEST.in",
    "README.md",
    "pyproject.toml",
    "release_build_backend.py",
)
_CANDIDATE_COPY_IGNORE = shutil.ignore_patterns(
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.egg-info",
    "build",
    "dist",
    "node_modules",
    "target",
)


class _PlanPayload(TypedDict):
    package_file: str
    selected_languages: list[str]
    prepared_languages: list[str]
    helper_source_paths: dict[str, list[str]]
    all_source_paths: list[str]
    package_markers: list[str]
    selection_inputs: list[str]

_EXPECTED_TYPESCRIPT_PATHS = [
    "integrations/obsidian/llm-wiki/main.js",
    "integrations/obsidian/llm-wiki/src/main.ts",
]
_BUNDLED_IMPLEMENTATION_PATHS = {
    "src/llm_wiki_cli/extractors/go_scripts/main.go",
    "src/llm_wiki_cli/extractors/haskell_scripts/Inventory.hs",
    "src/llm_wiki_cli/extractors/haskell_scripts/Json.hs",
    "src/llm_wiki_cli/extractors/haskell_scripts/Main.hs",
    "src/llm_wiki_cli/extractors/haskell_scripts/Parser.hs",
    "src/llm_wiki_cli/extractors/haskell_scripts/Paths.hs",
    "src/llm_wiki_cli/extractors/rust_scripts/src/main.rs",
    "src/llm_wiki_cli/extractors/ts_scripts/extract.js",
}
_BUNDLED_PACKAGE_MARKERS = {
    "src/llm_wiki_cli/extractors/go_scripts/go.mod",
    "src/llm_wiki_cli/extractors/rust_scripts/Cargo.lock",
    "src/llm_wiki_cli/extractors/rust_scripts/Cargo.toml",
    "src/llm_wiki_cli/extractors/ts_scripts/package-lock.json",
    "src/llm_wiki_cli/extractors/ts_scripts/package.json",
}
_BUNDLED_SELECTION_INPUTS = {
    "src/llm_wiki_cli/extractors/rust_scripts/.gitignore",
    "src/llm_wiki_cli/extractors/ts_scripts/.gitignore",
}

_PLAN_PROBE = textwrap.dedent(
    f"""\
    import json
    import pathlib
    import sys
    import types

    import llm_wiki_cli
    from llm_wiki_cli.commands import prepare_extractors_cmd
    from llm_wiki_cli.services.extractor_helpers import (
        HelperPrepareResult,
        SUPPORTED_HELPERS,
    )
    from llm_wiki_cli.services.source_snapshot import build_source_snapshot

    checkout = pathlib.Path(sys.argv[1]).resolve(strict=True)
    expected_import_root = pathlib.Path(sys.argv[2]).resolve(strict=True)
    helper_cache = pathlib.Path(sys.argv[3]).resolve()
    package_file = pathlib.Path(llm_wiki_cli.__file__).resolve(strict=True)
    try:
        package_file.relative_to(expected_import_root)
    except ValueError as exc:
        raise AssertionError(
            f"imported package {{package_file}} escaped {{expected_import_root}}"
        ) from exc

    snapshot = build_source_snapshot(checkout)
    selected_languages = prepare_extractors_cmd._languages_from_snapshot(
        str(checkout)
    )
    prepared_languages = []

    def fake_prepare(language, cache_root):
        prepared_languages.append(language)
        return HelperPrepareResult(language, "prepared", "packaging proof seam")

    prepare_extractors_cmd.prepare_helper = fake_prepare
    prepare_extractors_cmd.run(
        types.SimpleNamespace(
            src_dir=str(checkout),
            cache_dir=str(helper_cache),
            language=None,
            allow_external_src=True,
        )
    )

    payload = {{
        "package_file": str(package_file),
        "selected_languages": selected_languages,
        "prepared_languages": prepared_languages,
        "helper_source_paths": {{
            language: snapshot.language_paths(language)
            for language in SUPPORTED_HELPERS
        }},
        "all_source_paths": list(snapshot.all_source_paths),
        "package_markers": [
            source_file.rel_path for source_file in snapshot.package_markers
        ],
        "selection_inputs": sorted(
            path
            for path, kinds in snapshot.captured_input_kinds.items()
            if "selection" in kinds
        ),
    }}
    print({_RESULT_PREFIX!r} + json.dumps(payload, sort_keys=True))
    """
)


def _isolated_python_environment(import_root: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(import_root.resolve())
    environment["PYTHONNOUSERSITE"] = "1"
    environment.pop("PYTHONHOME", None)
    environment.pop("PYTHONSTARTUP", None)
    return environment


def _python_executable() -> Path:
    """Use the mandated project venv locally and the active CI Python elsewhere."""

    if LOCAL_VENV_PYTHON.is_file() and LOCAL_VENV_PIP.is_file():
        return LOCAL_VENV_PYTHON
    return Path(sys.executable)


def _pip_command() -> list[str]:
    """Use direct project-venv pip locally without making CI create another venv."""

    if LOCAL_VENV_PYTHON.is_file() and LOCAL_VENV_PIP.is_file():
        return [str(LOCAL_VENV_PIP)]
    return [str(_python_executable()), "-m", "pip"]


def _stage_candidate_source(destination: Path) -> None:
    """Copy only candidate build inputs, excluding disposable build state."""

    destination.mkdir()
    for relative_path in _CANDIDATE_ROOT_FILES:
        source = PROJECT_ROOT / relative_path
        shutil.copy2(source, destination / relative_path)

    for relative_path in (
        Path("docs/standalone-documentation.md"),
        Path("examples/plugins/documentation-hooks"),
        Path("src/llm_wiki_cli"),
    ):
        source = PROJECT_ROOT / relative_path
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, ignore=_CANDIDATE_COPY_IGNORE)
        else:
            shutil.copy2(source, target)


def _tree_metadata(root: Path) -> tuple[tuple[str, bool, int, int], ...]:
    """Return enough metadata to detect writes to an ignored checkout tree."""

    if not root.exists():
        return ()
    paths = [root, *sorted(root.rglob("*"))]
    return tuple(
        (
            path.relative_to(PROJECT_ROOT).as_posix(),
            path.is_dir(),
            path.stat().st_mtime_ns,
            path.stat().st_size,
        )
        for path in paths
    )


def _checkout_packaging_output_state() -> tuple[tuple[str, bool, int, int], ...]:
    return tuple(
        item
        for root in (
            PROJECT_ROOT / "build",
            PROJECT_ROOT / "src/agent_wiki_cli.egg-info",
        )
        for item in _tree_metadata(root)
    )


def _run_checked(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(f"command exceeded {timeout_seconds}s timeout: {command!r}")
    assert completed.returncode == 0, (
        f"command failed ({completed.returncode}): {command!r}\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    return completed


def _probe_plan(
    *,
    import_root: Path,
    expected_import_root: Path,
    working_directory: Path,
    helper_cache: Path,
) -> _PlanPayload:
    completed = _run_checked(
        [
            str(_python_executable()),
            "-c",
            _PLAN_PROBE,
            str(PROJECT_ROOT),
            str(expected_import_root),
            str(helper_cache),
        ],
        cwd=working_directory,
        env=_isolated_python_environment(import_root),
        timeout_seconds=60,
    )
    result_lines = [
        line.removeprefix(_RESULT_PREFIX)
        for line in completed.stdout.splitlines()
        if line.startswith(_RESULT_PREFIX)
    ]
    assert len(result_lines) == 1, completed.stdout
    payload = json.loads(result_lines[0])
    assert isinstance(payload, dict)
    return cast(_PlanPayload, payload)


def _assert_preferred_actual_repository_plan(payload: _PlanPayload) -> None:
    helper_source_paths = payload["helper_source_paths"]
    assert helper_source_paths == {
        "typescript": _EXPECTED_TYPESCRIPT_PATHS,
        "go": [],
        "rust": [],
        "haskell": [],
    }
    assert payload["selected_languages"] == ["typescript"]
    assert payload["prepared_languages"] == ["typescript"]

    all_source_paths = set(payload["all_source_paths"])
    assert _BUNDLED_IMPLEMENTATION_PATHS.isdisjoint(all_source_paths)
    assert _BUNDLED_PACKAGE_MARKERS <= set(payload["package_markers"])
    assert _BUNDLED_SELECTION_INPUTS <= set(payload["selection_inputs"])


@pytest.mark.slow
def test_noneditable_install_matches_editable_actual_repository_helper_plan(tmp_path):
    """A target install must preserve the checkout's intentional helper plan."""

    if (LOCAL_VENV_PYTHON.exists(), LOCAL_VENV_PIP.exists()) != (False, False):
        assert LOCAL_VENV_PYTHON.is_file() and LOCAL_VENV_PIP.is_file(), (
            "the project .venv must provide both bin/python and bin/pip"
        )

    site_target = tmp_path / "target" / "site"
    site_target.mkdir(parents=True)
    candidate_source = tmp_path / "candidate-source"
    _stage_candidate_source(candidate_source)
    pip_environment = os.environ.copy()
    pip_environment["PYTHONNOUSERSITE"] = "1"
    pip_environment.pop("PYTHONPATH", None)
    pip_environment.pop("PYTHONHOME", None)
    checkout_packaging_state = _checkout_packaging_output_state()
    _run_checked(
        [
            *_pip_command(),
            "install",
            "--disable-pip-version-check",
            "--no-build-isolation",
            "--no-deps",
            "--target",
            str(site_target),
            ".",
        ],
        cwd=candidate_source,
        env=pip_environment,
        timeout_seconds=180,
    )
    assert _checkout_packaging_output_state() == checkout_packaging_state

    editable_payload = _probe_plan(
        import_root=PROJECT_ROOT / "src",
        expected_import_root=PROJECT_ROOT / "src",
        working_directory=tmp_path,
        helper_cache=tmp_path / "editable-helper-cache",
    )
    noneditable_payload = _probe_plan(
        import_root=site_target,
        expected_import_root=site_target,
        working_directory=tmp_path,
        helper_cache=tmp_path / "noneditable-helper-cache",
    )

    assert Path(noneditable_payload["package_file"]).resolve().is_relative_to(
        site_target.resolve()
    )
    _assert_preferred_actual_repository_plan(editable_payload)
    _assert_preferred_actual_repository_plan(noneditable_payload)

    comparable_fields = {
        "selected_languages",
        "prepared_languages",
        "helper_source_paths",
        "all_source_paths",
        "package_markers",
        "selection_inputs",
    }
    assert {key: editable_payload[key] for key in comparable_fields} == {
        key: noneditable_payload[key] for key in comparable_fields
    }
