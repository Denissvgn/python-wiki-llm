"""Project upgrade accepts oversized legacy inputs without oversized new commits."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
from dataclasses import replace

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import bootstrap_cmd, knowledge_cmd, sync_cmd
from llm_wiki_cli.services.knowledge_artifacts import (
    CommitStage,
    build_knowledge_commit_plan,
    commit_knowledge_artifacts,
    current_knowledge_format,
)
from llm_wiki_cli.services.knowledge_governance import load_governance
from llm_wiki_cli.services.knowledge_index import serialize_knowledge_index
from llm_wiki_cli.services.knowledge_storage import GIT_FAILURE_BYTES, digest
from llm_wiki_cli.services import knowledge_storage_lifecycle
from llm_wiki_cli.services.knowledge_storage_lifecycle import _committed_inputs
from llm_wiki_cli.services.maintenance_protocol import (
    ADOPTION_FILENAME,
    guard_maintenance_owner,
)
from llm_wiki_cli.services.manifest_storage import current_manifest_format
from llm_wiki_cli.services.section_ownership import observe_page_sections
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.knowledge_storage_scale import large_logical_payload


def _hashes(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file() and not path.name.endswith(".lock")
    }


def _legacy_project(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)
    recovery_temp = tmp_path / "recovery-temp"
    recovery_temp.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(recovery_temp))
    Path("src").mkdir()
    Path("src/app.py").write_text("class Item:\n    value: int\n", encoding="utf-8")
    Path(".git").mkdir()
    selection = Path("selection.json")
    selection.write_text(json.dumps({
        "schema_version": "llm-wiki-source-selection/v1", "include": ["src"], "exclude": [],
    }), encoding="utf-8")
    bootstrap_cmd.run(cli._build_parser().parse_args([
        "bootstrap", "--src-dir", ".", "--wiki-dir", "wiki", "--knowledge-format", "v1",
        "--source-selection", str(selection), "--helper-cache-dir", ".git",
    ]))
    page = Path("wiki/entities/Item.md")
    page.write_text(page.read_text(encoding="utf-8").replace(
        "## Description", "## Description\n\nConsumer-authored explanation."), encoding="utf-8")
    sync_cmd.run(cli._build_parser().parse_args([
        "sync", "--src-dir", ".", "--wiki-dir", "wiki", "--force", "--no-plugins",
        "--source-selection", str(selection), "--helper-cache-dir", ".git",
    ]))
    knowledge_cmd.run(cli._build_parser().parse_args([
        "knowledge", "init", "--wiki-dir", "wiki", "--bundle-id", "kb_large_upgrade",
    ]))
    state, _, _ = _committed_inputs("wiki")
    assert state.knowledge is not None
    concept = next(item for item in state.knowledge.concepts
                   if item.document.canonical_path == "entities/Item.md")
    section = next(item for item in observe_page_sections(
        page.read_text(encoding="utf-8"), concept.locator, "entities",
    ).sections if item.semantic_hash is not None)
    ledger = load_governance("wiki").ledger
    uid = next(uid for uid, item in ledger.concepts.items() if item.locator == concept.locator)
    knowledge_cmd.run(cli._build_parser().parse_args([
        "knowledge", "review", "--wiki-dir", "wiki", "--uid", uid,
        "--section", section.locator, "--reviewer-kind", "human",
        "--reviewer-id", "fixture-reviewer", "--method", "fixture-review",
        "--method-version", "1", "--authored-at", "2026-11-03T08:00:00Z",
    ]))
    assert load_governance("wiki").ledger.review_events
    assert not Path("wiki", ADOPTION_FILENAME).exists()
    # Legacy producers predate reuse commitments. Remove both sides through
    # the owning writer before constructing a pre-policy legacy snapshot.
    from llm_wiki_cli.services.knowledge_reuse import REUSE_INPUT_KEY, REUSE_EXTENSION_KEY

    state, _, previous = _committed_inputs("wiki")
    assert state.knowledge is not None and state.manifest_basis is not None
    generation = dict(state.manifest_basis.generation_inputs)
    generation.pop(REUSE_INPUT_KEY, None)
    extensions = dict(state.knowledge.extensions)
    extensions.pop(REUSE_EXTENSION_KEY, None)
    commit_knowledge_artifacts(build_knowledge_commit_plan("wiki",
        surface_index_bytes=previous[".llm-wiki-surface.json"],
        knowledge_index=replace(state.knowledge, extensions=extensions),
        manifest=state.manifest_basis.with_generation_state(
            surfaces=state.manifest_basis.surfaces, generation_inputs=generation)))
    return project


def test_cli_upgrade_packs_a_real_oversized_legacy_root_before_adoption(tmp_path, monkeypatch, capsys):
    project = _legacy_project(tmp_path, monkeypatch)
    wiki = project / "wiki"
    root = wiki / ".llm-wiki-knowledge.json"
    # This represents a previously committed, pre-policy v1 snapshot, as in the
    # storage scale fixture. New oversized flat writes must still be refused.
    payload = large_logical_payload(root.read_bytes(), blocks=GIT_FAILURE_BYTES // 131_072 + 1)
    extensions = {
        name: hashlib.sha256(value.encode()).hexdigest()
        for name, value in payload["extensions"].items() if name.startswith("storage-scale/")
    }
    legacy = serialize_knowledge_index(payload).encode("utf-8")
    assert GIT_FAILURE_BYTES == 95 * 1024 * 1024
    assert len(legacy) > GIT_FAILURE_BYTES
    manifest = SyncManifest.load(wiki)
    marker = manifest.artifact_hashes
    assert marker is not None
    manifest = manifest.with_artifact_hashes(
        surface_index_hash=marker.surface_index_hash, knowledge_index_hash=digest(legacy),
        evaluated_envelope_hash=marker.evaluated_envelope_hash, governance_hash=marker.governance_hash,
    )
    policy_key = "consumer/legacy-storage-policy"
    manifest.generation_inputs[policy_key] = "x" * GIT_FAILURE_BYTES
    policy_hash = hashlib.sha256(str(manifest.generation_inputs[policy_key]).encode()).hexdigest()
    root.write_bytes(legacy)
    legacy_manifest = (json.dumps(manifest.to_payload(), sort_keys=True, indent=2) + "\n").encode()
    assert len(legacy_manifest) > GIT_FAILURE_BYTES
    (wiki / ".llm-wiki-manifest.json").write_bytes(legacy_manifest)
    del legacy, legacy_manifest, payload, manifest
    state, _, _ = _committed_inputs(wiki)
    assert state.knowledge is not None and state.manifest_basis is not None
    with pytest.raises(ValueError, match="95 MiB"):
        build_knowledge_commit_plan(
            wiki, surface_index_bytes=(wiki / ".llm-wiki-surface.json").read_bytes(),
            knowledge_index=state.knowledge, manifest=state.manifest_basis.without_artifact_hashes(),
            prior=state.validated_artifacts, knowledge_format="v1",
        )
    del state
    before = _hashes(wiki)
    source = _hashes(project / "src")
    profile = (project / "selection.json").read_bytes()
    capsys.readouterr()
    arguments = [
        "upgrade", "--src-dir", ".", "--wiki-dir", "wiki", "--agent", "generic", "--no-skills",
        "--source-selection", "selection.json", "--helper-cache-dir", ".git",
    ]
    monkeypatch.setattr(sys, "argv", ["llm-wiki", *arguments])
    for interrupted_stage in (CommitStage.KNOWLEDGE_INDEX_WRITTEN, CommitStage.MANIFEST_WRITTEN):
        def interrupt(stage):
            if stage is interrupted_stage:
                raise OSError("interrupted oversized legacy migration")

        def publish(plan):
            return commit_knowledge_artifacts(plan, fault_injector=interrupt)

        with monkeypatch.context() as fault:
            fault.setattr(knowledge_storage_lifecycle, "commit_knowledge_artifacts", publish)
            with pytest.raises(SystemExit) as stopped:
                cli.main()
        assert stopped.value.code == 2
        stderr = capsys.readouterr().err
        assert "interrupted oversized legacy migration" in stderr
        interrupted_recovery = Path(next(line.removeprefix("Native upgrade recovery: ")
                                        for line in stderr.splitlines()
                                        if line.startswith("Native upgrade recovery: ")))
        assert current_knowledge_format(wiki) == "packed-v4-deflate"
        assert not (wiki / ADOPTION_FILENAME).exists()
        if interrupted_stage is CommitStage.KNOWLEDGE_INDEX_WRITTEN:
            with pytest.raises(ValueError):
                _committed_inputs(wiki)
        else:
            _committed_inputs(wiki)
        recovery_arguments = ["llm-wiki", "knowledge", "recover-storage", "--wiki-dir", "wiki",
                              "--recovery-dir", str(interrupted_recovery / "knowledge")]
        packed = _hashes(wiki)
        with monkeypatch.context() as invocation:
            invocation.setattr(sys, "argv", [*recovery_arguments, "--dry-run"])
            cli.main()
            assert _hashes(wiki) == packed
            invocation.setattr(sys, "argv", recovery_arguments)
            cli.main()
        restored = _hashes(wiki)
        assert all(restored[name] == content_hash for name, content_hash in before.items())
        assert root.stat().st_size > GIT_FAILURE_BYTES
        assert (wiki / ".llm-wiki-manifest.json").stat().st_size > GIT_FAILURE_BYTES
        _committed_inputs(wiki)
        capsys.readouterr()
    cli.main()
    output = capsys.readouterr().out
    recovery = Path(next(line.removeprefix("Native upgrade recovery: ")
                         for line in output.splitlines() if line.startswith("Native upgrade recovery: ")))
    assert current_knowledge_format(wiki) == "packed-v4-deflate"
    assert current_manifest_format(wiki) == "indexed-v8"
    assert all(path.stat().st_size < GIT_FAILURE_BYTES for path in wiki.rglob("*") if path.is_file())
    assert _hashes(project / "src") == source
    assert (project / "selection.json").read_bytes() == profile
    after = _hashes(wiki)
    for name, content_hash in before.items():
        if name.endswith(".md") or name == ".llm-wiki-governance.json":
            assert after[name] == content_hash
            assert hashlib.sha256((recovery / "adoption/before" / name).read_bytes()).hexdigest() == content_hash
    for name in (".llm-wiki-knowledge.json", ".llm-wiki-manifest.json", ".llm-wiki-surface.json"):
        assert hashlib.sha256((recovery / "knowledge" / name).read_bytes()).hexdigest() == before[name]
    state, _, _ = _committed_inputs(wiki)
    assert state.knowledge is not None and state.manifest_basis is not None
    assert state.manifest_basis.maintenance_state is not None
    assert hashlib.sha256(str(state.manifest_basis.generation_inputs[policy_key]).encode()).hexdigest() == policy_hash
    assert guard_maintenance_owner(wiki) is not None
    assert {
        name: hashlib.sha256(value.encode()).hexdigest()
        for name, value in state.knowledge.extensions.items() if name.startswith("storage-scale/")
    } == extensions
    records = state.manifest_basis.maintenance_state["records"]
    assert records and all(row["status"] == "pending" for row in records.values())
    del state
    cli.main()
    assert _hashes(wiki) == after
    assert "Native upgrade recovery:" not in capsys.readouterr().out
