"""Release admission catches recorded runtime/preparation failures cheaply."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
import yaml

from release import preflight, readiness

ROOT = Path(__file__).parents[1]


@pytest.fixture
def candidate(tmp_path):
    root = tmp_path / "candidate"
    root.mkdir()
    contract = json.loads((ROOT / readiness.CONTRACT).read_text())
    documents = {}
    for consumer in contract["consumers"]:
        document = documents.setdefault(consumer["path"], {})
        profile = contract["profiles"][consumer["profile"]]
        if consumer["job"] is None:
            job = document.setdefault("runs", {"using": "composite"})
        else:
            job = document.setdefault("jobs", {}).setdefault(consumer["job"], {})
            job["runs-on"] = (
                "ubuntu-24.04" if profile["platform"] == "linux" else "windows-2025"
            )
        job["steps"] = [
            {
                "uses": "actions/setup-python@" + "a" * 40,
                "with": {"python-version": profile["python"][0]},
            }
        ]
        if consumer["selection"] == "matrix-python":
            job["strategy"] = {"matrix": {"python": profile["python"]}}
            job["steps"][0]["with"]["python-version"] = "${{ matrix.python }}"
    for name, document in documents.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(document))
    (root / "release").mkdir(exist_ok=True)
    (root / readiness.CONTRACT).write_text(json.dumps(contract))
    (root / "release/toolchain-lock.json").write_bytes(
        (ROOT / "release/toolchain-lock.json").read_bytes()
    )
    return root


@pytest.fixture
def manifest(tmp_path):
    path = tmp_path / "official-python-manifest.json"
    rows = []
    for version, system, platform_version in [
        ("3.13.16", "win32", None),
        ("3.13.17", "win32", None),
        ("3.13.18", "linux", "24.04"),
    ]:
        rows.append(
            {
                "version": version,
                "stable": True,
                "files": [
                    {
                        "platform": system,
                        "platform_version": platform_version,
                        "arch": "x64",
                        "download_url": "https://github.com/actions/python-versions/releases/download/"
                        + version
                        + "/installer",
                    }
                ],
            }
        )
    path.write_text(json.dumps(rows))
    return path


def inspect_runtime(root, manifest=None):
    return readiness.inspect(root, runtime_only=True, python_manifest=manifest)


def test_complete_runtime_contract_admits_every_owner_but_grants_no_execution_proof(
    candidate, manifest
):
    result = inspect_runtime(candidate, manifest)
    assert (
        result["status"] == "ready"
        and result["blockers"] == result["hosted_pending"] == []
    )
    assert {r["id"] for r in result["runtime_contract"]["consumers"]} == set(
        readiness.REQUIRED_CONSUMERS
    )
    assert len(result["runtime_contract"]["availability"]) == 4
    assert (
        result["target_execution_verified"] is result["publication_authority"] is False
    )


def test_offline_availability_is_explicitly_pending_not_ready(candidate):
    result = inspect_runtime(candidate)
    assert result["status"] == "hosted-required" and not result["blockers"]
    assert result["hosted_pending"][0]["id"] == "python-availability"


def test_offline_cli_returns_pending_exit_and_writes_explicit_unknown(
    candidate, tmp_path
):
    output = tmp_path / "readiness.json"
    assert (
        readiness.main(
            [
                "inspect",
                "--root",
                str(candidate),
                "--runtime-only",
                "--output",
                str(output),
            ]
        )
        == 3
    )
    report = json.loads(output.read_text())
    assert (
        report["status"] == "hosted-required"
        and report["publication_authority"] is False
    )


def test_artifact_smoke_cannot_be_left_floating_or_on_another_patch(
    candidate, manifest
):
    path = candidate / ".github/workflows/release-qualification.yml"
    data = yaml.safe_load(path.read_text())
    data["jobs"]["artifact-smoke"]["steps"][0]["with"]["python-version"] = "3.13"
    data["jobs"]["action"]["steps"][0]["with"]["python-version"] = "3.13.17"
    path.write_text(yaml.safe_dump(data))
    result = inspect_runtime(candidate, manifest)
    assert result["status"] == "blocked"
    assert {r["id"] for r in result["blockers"]} == {
        "runtime-owner:artifact-smoke",
        "runtime-owner:rd10",
    }


def test_runtime_contract_cannot_omit_an_owner_or_reassign_its_cohort(
    candidate, manifest
):
    path = candidate / readiness.CONTRACT
    original = json.loads(path.read_text())
    changed = deepcopy(original)
    changed["consumers"] = [
        r for r in changed["consumers"] if r["id"] != "artifact-smoke"
    ]
    path.write_text(json.dumps(changed))
    assert inspect_runtime(candidate, manifest)["status"] == "blocked"
    changed = deepcopy(original)
    next(r for r in changed["consumers"] if r["id"] == "artifact-smoke")["profile"] = (
        "windows-core"
    )
    path.write_text(json.dumps(changed))
    assert inspect_runtime(candidate, manifest)["status"] == "blocked"


def test_linux_patch_availability_does_not_establish_windows_availability(
    candidate, manifest
):
    rows = json.loads(manifest.read_text())
    rows[1]["files"][0]["platform"] = "linux"
    manifest.write_text(json.dumps(rows))
    result = inspect_runtime(candidate, manifest)
    assert result["status"] == "blocked"
    assert {r["id"] for r in result["blockers"]} == {
        "python-download:windows-core:3.13.17",
        "python-download:windows-probe:3.13.17",
    }


@pytest.mark.parametrize("change", ["arch", "runner", "download-host"])
def test_platform_architecture_and_official_download_origin_are_checked(
    candidate, manifest, change
):
    if change == "download-host":
        rows = json.loads(manifest.read_text())
        rows[2]["files"][0]["download_url"] = (
            "https://example.invalid/actions/python-versions/releases/download/not-official"
        )
        manifest.write_text(json.dumps(rows))
    else:
        path = candidate / ".github/workflows/release-qualification.yml"
        document = yaml.safe_load(path.read_text())
        job = document["jobs"]["artifact-smoke"]
        if change == "arch":
            job["steps"][0]["with"]["architecture"] = "arm64"
        else:
            job["runs-on"] = "windows-2025"
        path.write_text(yaml.safe_dump(document))
    assert inspect_runtime(candidate, manifest)["status"] == "blocked"


@pytest.mark.parametrize(
    "raw", [b"[]", b'{"version":NaN}', b'[{"version":"x","version":"y"}]']
)
def test_invalid_or_ambiguous_availability_document_fails_closed(
    candidate, manifest, raw
):
    manifest.write_bytes(raw)
    result = inspect_runtime(candidate, manifest)
    assert (
        result["status"] == "blocked" and result["runtime_contract"]["manifest"] is None
    )


def test_availability_reads_are_bounded_and_do_not_follow_links(tmp_path):
    source = tmp_path / "source.json"
    source.write_bytes(b"[" + b" " * readiness.MAX_MANIFEST + b"]")
    with pytest.raises(ValueError, match="oversized"):
        readiness.python_manifest(source)
    link = tmp_path / "link.json"
    link.symlink_to(source)
    with pytest.raises(ValueError, match="Redirected"):
        readiness.python_manifest(link)


def test_all_missing_selected_tools_and_helpers_are_reported_together(
    candidate, monkeypatch
):
    from llm_wiki_cli.services import extractor_helpers as helpers

    monkeypatch.setattr(helpers, "get_prepared_binary", lambda *a: None)
    monkeypatch.setattr(readiness.importlib.util, "find_spec", lambda name: object())
    report = readiness.capabilities(
        candidate,
        environment={"tools": {}},
        helper={"status": "unavailable"},
        native_languages=readiness.LANGUAGES,
    )
    ids = {r["id"] for r in report["blockers"]}
    assert {
        "tool:node",
        "tool:npm",
        "tool:actionlint",
        "tool:go",
        "tool:rust",
        "tool:cargo",
        "tool:haskell",
        *("helper:" + s for s in readiness.LANGUAGES),
    } <= ids
    assert not report["hosted_pending"]


def test_unselected_native_capabilities_remain_hosted_pending(candidate, monkeypatch):
    from llm_wiki_cli.services import extractor_helpers as helpers

    monkeypatch.setattr(helpers, "get_prepared_binary", lambda *a: None)
    monkeypatch.setattr(readiness.importlib.util, "find_spec", lambda name: object())
    report = readiness.capabilities(
        candidate,
        stages=("freeze",),
        environment={"tools": {}},
        helper={"status": "unavailable"},
        native_languages=[],
    )
    assert report["blockers"] == []
    assert {r["id"] for r in report["hosted_pending"]} == {
        "helper:" + s for s in readiness.LANGUAGES
    }


def test_selected_cache_base_is_explicit_and_used_by_native_consumers(
    candidate, monkeypatch
):
    from llm_wiki_cli.services import extractor_helpers as helpers

    cache = candidate / "private/cache-base"
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(cache))
    observed = []
    monkeypatch.setattr(
        helpers,
        "get_prepared_binary",
        lambda language, root, base: observed.append(base),
    )
    report = readiness.capabilities(
        candidate,
        stages=("freeze",),
        environment={"tools": {}},
        helper={"status": "unavailable"},
        native_languages=[],
    )
    assert report["cache_base"] == str(cache) and observed == [str(cache)] * 3
    assert {r["cache_root"] for r in report["capabilities"]} == {
        str(cache / "llm-wiki-extractors")
    }


def test_preflight_helper_does_not_fall_back_to_a_different_cache_base(
    candidate, monkeypatch
):
    from llm_wiki_cli.services import extractor_helpers as helpers

    base = candidate / "private/prepared"
    cache = base / "llm-wiki-extractors/typescript"
    package = cache / "owned-package"
    module = package / "node_modules/ts-morph"
    module.mkdir(parents=True)
    (module / "module.js").write_text("module.exports={};")
    for name in ("extract.js", "package.json", "package-lock.json"):
        (package / name).write_text("{}")
    (cache / "current.json").write_text(
        json.dumps(
            {
                "path": str(module),
                "root": str(package),
                "toolchain": "node v24.18.0; npm 11.16.0",
            }
        )
    )
    calls = []
    monkeypatch.setattr(
        helpers, "_manifest_current", lambda root, language: calls.append(root) or {}
    )
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(base))
    environment = {
        "tools": {"node": {"version": "v24.18.0"}, "npm": {"version": "11.16.0"}}
    }
    assert preflight._helper(candidate, environment)["status"] == "ready"
    assert calls == [base / "llm-wiki-extractors"]
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(candidate / "wrong-base"))
    assert preflight._helper(candidate, environment)["status"] == "unavailable"


def test_readiness_output_is_fresh_and_never_overwrites_or_redirects(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    output = tmp_path / "out/report.json"
    readiness.write_report(output, {"status": "blocked"}, root=root)
    saved = output.read_bytes()
    with pytest.raises(FileExistsError):
        readiness.write_report(output, {"status": "ready"}, root=root)
    assert output.read_bytes() == saved
    alias = tmp_path / "alias"
    alias.symlink_to(output.parent, target_is_directory=True)
    with pytest.raises(ValueError, match="Redirected"):
        readiness.write_report(alias / "new.json", {}, root=root)
    assert not (output.parent / "new.json").exists()


def test_runtime_matrix_must_actually_feed_interpreter_setup(candidate, manifest):
    path = candidate / ".github/workflows/windows-measurement.yml"
    document = yaml.safe_load(path.read_text())
    document["jobs"]["measurement"]["steps"][0]["with"]["python-version"] = "3.13"
    path.write_text(yaml.safe_dump(document))
    result = inspect_runtime(candidate, manifest)
    assert result["status"] == "blocked"
    assert [r["id"] for r in result["blockers"]] == ["runtime-owner:windows-probe"]


def test_selected_helper_cache_does_not_follow_aliases(tmp_path, monkeypatch):
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(alias))
    with pytest.raises(ValueError, match="Redirected"):
        readiness.helper_cache_base(tmp_path)


def test_same_version_stale_provider_is_rejected_by_actual_namespace_bytes(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace
    import llm_wiki_cli

    root = tmp_path / "candidate"
    source = root / "src/llm_wiki_cli"
    source.mkdir(parents=True)
    (source / "__init__.py").write_text('VALUE = "candidate"\n')
    (root / "pyproject.toml").write_text(
        '[project]\nversion="4.0.1"\n[tool.setuptools.package-data]\nllm_wiki_cli=[]\n'
    )
    prefix = tmp_path / "environment"
    installed = prefix / "site-packages/llm_wiki_cli"
    installed.mkdir(parents=True)
    (installed / "__init__.py").write_text('VALUE = "old-version-same-metadata"\n')
    monkeypatch.setattr(llm_wiki_cli, "__file__", str(installed / "__init__.py"))
    monkeypatch.setattr(readiness, "sys", SimpleNamespace(prefix=str(prefix)))
    monkeypatch.setattr(readiness.importlib.metadata, "version", lambda name: "4.0.1")
    with pytest.raises(ValueError, match="namespace differs"):
        readiness.provider_observation(root)
    (installed / "__init__.py").write_bytes((source / "__init__.py").read_bytes())
    assert readiness.provider_observation(root)["files"] == 1
