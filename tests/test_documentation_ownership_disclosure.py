"""Explicit custody limits without granting workers native write authority."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import documentation_run as lifecycle
from llm_wiki_cli.services.documentation_policy import hash_bytes
from llm_wiki_cli.services.documentation_run import contracts, integrity, refresh
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.maintenance_protocol import guard_maintenance_owner
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.test_documentation_native_lifecycle import (
    _agent_result,
    _prepare_legacy_wiki_only_run,
    _prepare_source_run,
)


ROOT_FILES = {
    ".llm-wiki-manifest.json",
    ".llm-wiki-surface.json",
    ".llm-wiki-knowledge.json",
    ".llm-wiki-governance.json",
    ".llm-wiki-verification.json",
}
MARKER = ".llm-wiki-maintenance-adoption.json"
OBJECT_DIRS = (
    ".llm-wiki-manifest/objects",
    ".llm-wiki-knowledge/objects",
    ".llm-wiki-knowledge/packs",
    ".llm-wiki-knowledge/pack-index",
    ".llm-wiki-knowledge/index-pages",
)
CURRENT_OBJECT_DIRS = (OBJECT_DIRS[0], OBJECT_DIRS[2], OBJECT_DIRS[4])


def _json(path: Path) -> dict:
    return json.loads(path.read_bytes())


def _bytes(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


def _prepare(tmp_path: Path, mode: str):
    if mode == "source":
        source, workspace, run = _prepare_source_run(tmp_path)
        return source, None, workspace, run
    seed = tmp_path / "seed"
    seed.mkdir()
    source, source_workspace, _ = _prepare_source_run(seed)
    input_wiki = source_workspace / "wiki"
    workspace = tmp_path / "imported-workspace"
    run = lifecycle.prepare_documentation_run(
        workspace,
        baseline_strategy="adopt_existing_wiki",
        input_wiki_root=input_wiki,
        freshness_policy="allow-unverified",
        site_name="Native custody",
        project_purpose="Explain native custody.",
        audiences=["operator"],
        audience_intent={"operator": "review custody"},
    )
    return source, input_wiki, workspace, run


@pytest.mark.parametrize("mode", ["source", "imported"])
def test_prepare_discloses_exact_inventory_and_omitted_custody(
    tmp_path: Path, mode: str
):
    source, input_wiki, workspace, run = _prepare(tmp_path, mode)
    wiki = workspace / "wiki"
    before = _bytes(wiki), _bytes(source), _bytes(input_wiki) if input_wiki else None
    inventory = _json(workspace / run.evidence["generated_ownership"])
    coverage = inventory["coverage"]
    assert coverage["schema_version"] == "llm-wiki-documentation-ownership-coverage/v1"
    assert coverage["complete_native_custody"] is False
    assert coverage["presence_evaluated"] is False
    assert set(coverage["fingerprints"]["root_files"]) == ROOT_FILES
    assert coverage["fingerprints"]["markdown"] == "generated-sections-only"
    assert set(coverage["omitted"]) == {MARKER, *OBJECT_DIRS}
    assert (
        coverage["omitted"][MARKER]["classification"]
        == "immutable-ordinary-authority-marker"
    )
    assert all(
        coverage["omitted"][d]["classification"]
        == "immutable-content-addressed-storage"
        for d in OBJECT_DIRS
    )
    assert all(
        role["fingerprinted"] is False and role["root_rollback"] is False
        for role in coverage["omitted"].values()
    )
    assert MARKER not in inventory["fingerprints"]
    assert not any(key.startswith(OBJECT_DIRS) for key in inventory["fingerprints"])
    assert inventory["fingerprints"] == lifecycle.capture_generated_ownership(wiki)
    assert set(contracts._NATIVE_ARTIFACT_PATHS) == ROOT_FILES
    assert set(contracts._NATIVE_REFRESH_MUTABLE_PATHS) == ROOT_FILES - {
        ".llm-wiki-verification.json"
    }
    if mode == "source":
        native = _json(workspace / run.evidence["native_refresh"])
        assert native["ownership_coverage"] == coverage
        assert set(native["artifact_ownership"]) == ROOT_FILES | {MARKER, *OBJECT_DIRS}
        assert all(
            native["artifact_ownership"][p] == role
            for p, role in coverage["omitted"].items()
        )
    lifecycle.build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    assert (
        _bytes(wiki),
        _bytes(source),
        _bytes(input_wiki) if input_wiki else None,
    ) == before
    guard_maintenance_owner(wiki)
    assert load_knowledge_state(wiki).status is KnowledgeLoadState.VALID


def test_wiki_only_disclosure_does_not_invent_authority(tmp_path: Path):
    _input, _raw, workspace, run = _prepare_legacy_wiki_only_run(tmp_path)
    inventory = _json(workspace / run.evidence["generated_ownership"])
    assert inventory["coverage"]["presence_evaluated"] is False
    assert inventory["coverage"]["complete_native_custody"] is False
    assert set(inventory["coverage"]["omitted"]) == {MARKER, *OBJECT_DIRS}
    assert run.evidence["native_refresh"] == ""
    assert not (workspace / "wiki" / MARKER).exists()
    assert all(not (workspace / "wiki" / name).exists() for name in OBJECT_DIRS)


@pytest.mark.parametrize("mode", ["source", "imported"])
@pytest.mark.parametrize("role", ["marker", *CURRENT_OBJECT_DIRS])
@pytest.mark.parametrize("mutation", ["change", "remove", "symlink"])
def test_worker_cannot_mutate_omitted_custody(
    tmp_path: Path, mode: str, role: str, mutation: str
):
    source, input_wiki, workspace, run = _prepare(tmp_path, mode)
    wiki = workspace / "wiki"
    path = (
        wiki / MARKER
        if role == "marker"
        else next(p for p in (wiki / role).rglob("*") if p.is_file())
    )
    original_source, original_input = (
        _bytes(source),
        _bytes(input_wiki) if input_wiki else None,
    )
    authored = {p: b for p, b in _bytes(wiki).items() if p.endswith(".md")}
    lifecycle.build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    if mutation == "change":
        path.write_bytes(b"invalid native bytes\x00\xff")
    elif mutation == "remove":
        path.unlink()
    else:
        outside = tmp_path / "outside.bin"
        outside.write_bytes(b"outside must stay untouched\x00\xff")
        path.unlink()
        path.symlink_to(outside)
    with pytest.raises(lifecycle.DocumentationIntegrityError):
        lifecycle.record_documentation_agent_result(
            workspace,
            _agent_result(
                run.run_id,
                "wiki-enrichment",
                changed=[path.relative_to(wiki).as_posix()],
            ),
        )
    # An unsafe link also refuses loading the run, before result reconciliation.
    assert _json(workspace / ".llm-wiki-docs/run.json")["state"] in {
        "blocked",
        "wiki_enrichment",
    }
    assert not (workspace / ".llm-wiki-docs/results/wiki-enrichment-01.json").exists()
    assert _bytes(source) == original_source
    assert (_bytes(input_wiki) if input_wiki else None) == original_input
    assert all((wiki / p).read_bytes() == b for p, b in authored.items())
    if mutation == "symlink":
        assert outside.read_bytes() == b"outside must stay untouched\x00\xff"


@pytest.mark.parametrize("mode", ["source", "imported", "legacy"])
@pytest.mark.parametrize("directory", OBJECT_DIRS)
def test_worker_cannot_add_unreferenced_storage(
    tmp_path: Path, mode: str, directory: str
):
    if mode == "legacy":
        _input, _raw, workspace, run = _prepare_legacy_wiki_only_run(tmp_path)
    else:
        _source, _input, workspace, run = _prepare(tmp_path, mode)
    lifecycle.build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    path = workspace / "wiki" / directory / "unreferenced.bin"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"not worker-owned\x00\xff")
    with pytest.raises(lifecycle.DocumentationIntegrityError):
        lifecycle.record_documentation_agent_result(
            workspace,
            _agent_result(
                run.run_id,
                "wiki-enrichment",
                changed=[path.relative_to(workspace / "wiki").as_posix()],
            ),
        )
    assert lifecycle.load_documentation_run(workspace).state == "blocked"


def test_worker_cannot_add_an_authority_marker_to_a_legacy_wiki(tmp_path: Path):
    _input, _raw, workspace, run = _prepare_legacy_wiki_only_run(tmp_path)
    lifecycle.build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    (workspace / "wiki" / MARKER).write_bytes(b"{}\n")
    with pytest.raises(lifecycle.DocumentationIntegrityError):
        lifecycle.record_documentation_agent_result(
            workspace, _agent_result(run.run_id, "wiki-enrichment", changed=[MARKER])
        )
    assert lifecycle.load_documentation_run(workspace).state == "blocked"


def test_legacy_ownership_evidence_remains_readable(tmp_path: Path):
    _source, workspace, run = _prepare_source_run(tmp_path)
    path = workspace / run.evidence["generated_ownership"]
    # This is the exact old wire shape, rebound as a trusted legacy fixture.
    path.write_text(
        json.dumps(
            {"fingerprints": lifecycle.capture_generated_ownership(workspace / "wiki")}
        ),
        encoding="utf-8",
    )
    run.integrity_anchors["generated_ownership"] = hash_bytes(path.read_bytes())
    lifecycle.save_documentation_run(workspace, run)
    lifecycle.build_documentation_agent_packet(workspace, stage="wiki-enrichment")


@pytest.mark.parametrize(
    "malformation", ["incomplete", "integer-boolean", "extra-role"]
)
def test_modified_coverage_is_rejected_even_with_a_rebound_fixture_anchor(
    tmp_path: Path, malformation: str
):
    _source, workspace, run = _prepare_source_run(tmp_path)
    path = workspace / run.evidence["generated_ownership"]
    payload = _json(path)
    if malformation == "incomplete":
        payload["coverage"] = {"complete_native_custody": True}
    elif malformation == "integer-boolean":
        payload["coverage"]["complete_native_custody"] = 0
    else:
        payload["coverage"]["omitted"]["unrecognized"] = {"fingerprinted": True}
    path.write_text(json.dumps(payload), encoding="utf-8")
    run.integrity_anchors["generated_ownership"] = hash_bytes(path.read_bytes())
    lifecycle.save_documentation_run(workspace, run)
    with pytest.raises(lifecycle.DocumentationRunError, match="coverage"):
        lifecycle.build_documentation_agent_packet(workspace, stage="wiki-enrichment")


def test_disclosure_is_bounded_and_never_reads_objects(monkeypatch: pytest.MonkeyPatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("disclosure must not inspect filesystem contents")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "rglob", forbidden)
    disclosure = contracts._native_ownership_coverage()
    assert len(json.dumps(disclosure).encode()) < 4096
    assert disclosure["complete_native_custody"] is False
    # Callers cannot mutate the next disclosure or the old rollback set.
    disclosure["omitted"].clear()
    assert len(contracts._native_ownership_coverage()["omitted"]) == 6
    assert set(contracts._NATIVE_ARTIFACT_PATHS) == ROOT_FILES


def test_omitted_objects_are_not_added_to_root_rollback(tmp_path: Path):
    root = tmp_path / "wiki"
    root.mkdir()
    object_file = root / OBJECT_DIRS[0] / "immutable.json"
    object_file.parent.mkdir(parents=True)
    object_file.write_bytes(b"opaque immutable storage\x00\xff")
    marker = root / MARKER
    marker.write_bytes(b"marker retained")
    baseline = refresh._capture_native_artifact_bytes(root)
    assert set(baseline) == ROOT_FILES
    refresh._rollback_native_artifact_bytes(root, baseline, cause=RuntimeError("fault"))
    assert object_file.read_bytes() == b"opaque immutable storage\x00\xff"
    assert marker.read_bytes() == b"marker retained"
    assert integrity.capture_generated_ownership(root) == {}


def test_import_refresh_preserves_pending_and_acknowledged_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text(
        'def run():\n    """Run the operation."""\n    return "running"\n',
        encoding="utf-8",
    )
    (source / "worker.py").write_text(
        'def stop():\n    """Stop the worker."""\n    return "stopped"\n',
        encoding="utf-8",
    )
    seed_workspace = tmp_path / "seed"
    lifecycle.prepare_documentation_run(
        seed_workspace,
        source_root=source,
        site_name="Review fixture",
        project_purpose="Preserve independent ordinary review records.",
        audiences=["operator"],
        audience_intent={"operator": "inspect review state"},
    )
    monkeypatch.chdir(tmp_path)
    seed = seed_workspace / "wiki"
    status = api.get_maintenance_status(str(source), str(seed), allow_external_src=True)
    assert isinstance(status["state_hash"], str)
    assert len(status["records"]) >= 2
    row = next(r for r in status["records"] if r["expected_basis"] is not None)
    assert row["expected_basis"] is not None
    api.acknowledge_maintenance(
        str(source),
        str(seed),
        record_id=row["record_id"],
        expected_state_hash=status["state_hash"],
        expected_basis=row["expected_basis"],
        actor_kind="agent",
        actor_id="independent-fixture-reviewer",
        allow_external_src=True,
    )
    before_state = SyncManifest.load(seed).maintenance_state
    assert before_state is not None
    assert {r["status"] for r in before_state["records"].values()} == {
        "pending",
        "acknowledged",
    }
    original_source, original_input = _bytes(source), _bytes(seed)
    workspace = tmp_path / "reviewed-import"
    run = lifecycle.prepare_documentation_run(
        workspace,
        baseline_strategy="adopt_existing_wiki",
        source_root=source,
        input_wiki_root=seed,
        freshness_policy="require-current",
        site_name="Review history",
        project_purpose="Preserve review identity.",
        audiences=["operator"],
        audience_intent={"operator": "inspect preserved authority"},
    )
    wiki = workspace / "wiki"
    assert (
        _json(workspace / run.evidence["native_refresh"])["ownership_coverage"][
            "complete_native_custody"
        ]
        is False
    )
    lifecycle.build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    assert SyncManifest.load(wiki).maintenance_state == before_state
    assert (wiki / MARKER).read_bytes() == original_input[MARKER]
    # Existing content-addressed objects and authored pages are never rolled back
    # or rewritten merely to describe them; new writer-owned objects may coexist.
    assert all(
        (wiki / p).read_bytes() == b
        for p, b in original_input.items()
        if p.endswith(".md") or p.startswith(OBJECT_DIRS)
    )
    assert _bytes(source) == original_source
    assert _bytes(seed) == original_input
    guard_maintenance_owner(wiki)
    assert load_knowledge_state(wiki).status is KnowledgeLoadState.VALID


@pytest.mark.parametrize(
    "source_available", [True, False], ids=["source-backed", "wiki-only"]
)
@pytest.mark.parametrize(
    "mutation", ["add-marker", "change-object", "remove-object", "symlink-object"]
)
@pytest.mark.parametrize(
    "storage_format,object_directory",
    [
        ("sharded-v2", OBJECT_DIRS[1]),
        ("packed-v3", OBJECT_DIRS[3]),
    ],
    ids=["sharded-v2", "packed-v3"],
)
def test_legacy_native_custody_remains_guarded(
    tmp_path: Path,
    source_available: bool,
    mutation: str,
    storage_format: str,
    object_directory: str,
):
    source = tmp_path / "source"
    source.mkdir()
    (source / "entry.py").write_text(
        'def run():\n    return "legacy"\n', encoding="utf-8"
    )
    input_wiki = tmp_path / "input-wiki"
    api.bootstrap_wiki(str(source), str(input_wiki), knowledge_format=storage_format)
    assert not (input_wiki / MARKER).exists()
    workspace = tmp_path / "sharded-workspace"
    run = lifecycle.prepare_documentation_run(
        workspace,
        baseline_strategy="adopt_existing_wiki",
        source_root=source if source_available else None,
        input_wiki_root=input_wiki,
        freshness_policy="require-current" if source_available else "allow-unverified",
        site_name="Legacy custody",
        project_purpose="Retain legacy native custody.",
        audiences=["operator"],
        audience_intent={"operator": "inspect legacy storage"},
    )
    before_source, before_input = _bytes(source), _bytes(input_wiki)
    wiki = workspace / "wiki"
    lifecycle.build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    if mutation == "add-marker":
        path = wiki / MARKER
        path.write_bytes(b"{}\n")
    else:
        path = next(p for p in (wiki / object_directory).rglob("*") if p.is_file())
        if mutation == "change-object":
            path.write_bytes(b"corrupt object\x00\xff")
        elif mutation == "remove-object":
            path.unlink()
        else:
            outside = tmp_path / "external-object"
            outside.write_bytes(b"external object untouched")
            path.unlink()
            path.symlink_to(outside)
    with pytest.raises(lifecycle.DocumentationIntegrityError):
        lifecycle.record_documentation_agent_result(
            workspace,
            _agent_result(
                run.run_id,
                "wiki-enrichment",
                changed=[path.relative_to(wiki).as_posix()],
            ),
        )
    assert _bytes(source) == before_source
    assert _bytes(input_wiki) == before_input
    assert not (workspace / ".llm-wiki-docs/results/wiki-enrichment-01.json").exists()
