from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / ".github" / "scripts" / "llm-wiki-helper-cache.py"
SPEC = importlib.util.spec_from_file_location("llm_wiki_helper_cache", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
CACHE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CACHE
SPEC.loader.exec_module(CACHE)


def _write_project(root: Path, *, version: str = "1.2.3") -> Path:
    (root / "release").mkdir(parents=True)
    (root / "release" / "toolchain-lock.json").write_text(
        '{"schema":"toolchains/v1"}\n', encoding="utf-8"
    )
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "agent-wiki-cli"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    contract = root / CACHE.HELPER_CONTRACT
    contract.parent.mkdir(parents=True)
    contract.write_text("HELPER_MANIFEST_VERSION = 2\n", encoding="utf-8")
    for relative_names in CACHE.HELPER_FILES.values():
        for relative_name in relative_names:
            source = root / relative_name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(f"fixture:{relative_name}\n", encoding="utf-8")
    return root


def _write_plan(root: Path, languages: tuple[str, ...]) -> Path:
    plan = root / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "schema": CACHE.PLAN_SCHEMA,
                "languages": list(languages),
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    return plan


def _key(
    root: Path,
    *,
    languages: tuple[str, ...] = CACHE.SUPPORTED_HELPERS,
    runner_os: str = "Linux",
    runner_arch: str = "X64",
    action_ref: str = "",
) -> str:
    return CACHE.cache_key(
        project_root=root,
        lock_path=root / "release" / "toolchain-lock.json",
        languages=languages,
        runner_os=runner_os,
        runner_arch=runner_arch,
        action_ref=action_ref,
    )


def test_helper_cache_key_covers_every_required_identity_dimension(
    tmp_path: Path,
) -> None:
    root = _write_project(tmp_path / "project")
    base = _key(root)

    assert re.fullmatch(
        r"llm-wiki-helpers-v1-linux-x64-[0-9a-f]{64}", base
    )
    assert _key(root, runner_os="macOS") != base
    assert _key(root, runner_arch="ARM64") != base
    assert _key(root, languages=("typescript",)) != base
    assert _key(root, action_ref="a" * 40) != base
    assert _key(_write_project(tmp_path / "next-version", version="1.2.4")) != base

    mutations = (
        root / "release" / "toolchain-lock.json",
        root / CACHE.HELPER_CONTRACT,
        *(
            root / relative
            for language in CACHE.SUPPORTED_HELPERS
            for relative in CACHE.HELPER_FILES[language]
        ),
    )
    for index, candidate in enumerate(mutations):
        original = candidate.read_bytes()
        candidate.write_bytes(original + f"mutation-{index}\n".encode())
        assert _key(root) != base
        candidate.write_bytes(original)
        assert _key(root) == base


def test_helper_cache_key_tracks_an_optional_go_lock_appearing_or_missing(
    tmp_path: Path,
) -> None:
    root = _write_project(tmp_path / "project")
    go_sum = root / CACHE.HELPER_FILES["go"][2]
    with_lock = _key(root, languages=("go",))

    go_sum.unlink()

    assert _key(root, languages=("go",)) != with_lock


def test_helper_cache_key_ignores_unselected_helper_sources(tmp_path: Path) -> None:
    root = _write_project(tmp_path / "project")
    base = _key(root, languages=("typescript",))
    unselected = root / CACHE.HELPER_FILES["haskell"][0]
    unselected.write_text("changed but unselected\n", encoding="utf-8")

    assert _key(root, languages=("typescript",)) == base


@pytest.mark.parametrize(
    "payload",
    (
        "[]",
        '{"languages":[],"schema":"llm-wiki-prepare-extractors-plan/v1"}',
        '{"schema":"wrong","languages":[]}',
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":["rust","go"]}',
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":["go","go"]}',
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":["python"]}',
        '{"schema":"llm-wiki-prepare-extractors-plan/v1","languages":[NaN]}',
    ),
)
def test_helper_cache_identity_rejects_noncanonical_plans(
    tmp_path: Path, payload: str
) -> None:
    plan = tmp_path / "plan.json"
    plan.write_text(payload, encoding="utf-8")

    with pytest.raises(CACHE.HelperCacheContractError):
        CACHE.load_plan(plan)


@pytest.mark.parametrize("action_ref", ("main", "v1.6.0", "a" * 39, "g" * 40))
def test_helper_cache_identity_rejects_mutable_or_invalid_action_refs(
    tmp_path: Path, action_ref: str
) -> None:
    root = _write_project(tmp_path / "project")

    with pytest.raises(CACHE.HelperCacheContractError, match="immutable"):
        _key(root, action_ref=action_ref)


def test_helper_cache_metrics_are_bounded_and_path_free(tmp_path: Path) -> None:
    root = _write_project(tmp_path / "project")
    plan = _write_plan(root, ("typescript", "rust"))
    output = root / "metrics.json"

    result = subprocess.run(
        [
            sys.executable,
            "-I",
            str(SCRIPT_PATH),
            "metrics",
            "--plan",
            str(plan),
            "--cache-hit",
            "true",
            "--started-ns",
            "1000000",
            "--finished-ns",
            "2500001",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    raw = output.read_bytes()
    assert len(raw) <= 1024
    assert str(tmp_path).encode() not in raw
    assert json.loads(raw) == {
        "schema": "llm-wiki-helper-cache-metrics/v1",
        "cache_key_schema": "llm-wiki-helpers-v1",
        "cache_attempted": True,
        "cache_hit": True,
        "selected_languages": ["typescript", "rust"],
        "prepare_elapsed_ms": 2,
    }


def test_helper_cache_metrics_record_a_no_helper_miss_without_attempting_cache() -> None:
    assert CACHE.metrics_payload(
        languages=(), cache_hit="", started_ns=10, finished_ns=10
    ) == {
        "schema": "llm-wiki-helper-cache-metrics/v1",
        "cache_key_schema": "llm-wiki-helpers-v1",
        "cache_attempted": False,
        "cache_hit": False,
        "selected_languages": [],
        "prepare_elapsed_ms": 0,
    }


@pytest.mark.parametrize(
    ("cache_hit", "started_ns", "finished_ns"),
    (
        ("yes", 0, 0),
        ("", -1, 0),
        ("false", 2, 1),
        ("true", 0, 3_600_000_000_001),
    ),
)
def test_helper_cache_metrics_reject_invalid_or_unbounded_values(
    cache_hit: str, started_ns: int, finished_ns: int
) -> None:
    with pytest.raises(CACHE.HelperCacheContractError):
        CACHE.metrics_payload(
            languages=("typescript",),
            cache_hit=cache_hit,
            started_ns=started_ns,
            finished_ns=finished_ns,
        )


def test_helper_cache_identity_cli_emits_only_fixed_outputs(tmp_path: Path) -> None:
    root = _write_project(tmp_path / "project")
    plan = _write_plan(root, ("typescript",))
    github_output = root / "github-output"

    result = subprocess.run(
        [
            sys.executable,
            "-I",
            str(SCRIPT_PATH),
            "identity",
            "--plan",
            str(plan),
            "--project-root",
            str(root),
            "--lock",
            str(root / "release" / "toolchain-lock.json"),
            "--runner-os",
            "Linux",
            "--runner-arch",
            "X64",
            "--action-ref",
            "a" * 40,
            "--github-output",
            str(github_output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    lines = github_output.read_text(encoding="utf-8").splitlines()
    assert re.fullmatch(
        r"cache-key=llm-wiki-helpers-v1-linux-x64-[0-9a-f]{64}", lines[0]
    )
    assert lines[1] == "has-helpers=true"
