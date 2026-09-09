"""Sync reuse is input-bound and agrees with the explicit full builder."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services.bootstrap_service import BootstrapRequest
from llm_wiki_cli.services import (
    knowledge_artifacts,
    knowledge_generation,
    knowledge_orchestration,
    knowledge_reuse,
)
from llm_wiki_cli.services.knowledge_loader import (
    load_knowledge_state,
    KnowledgeStateLoadError,
)
from llm_wiki_cli.services.sync_manifest import SyncManifest

ARTIFACTS = (
    ".llm-wiki-surface.json",
    ".llm-wiki-knowledge.json",
    ".llm-wiki-manifest.json",
)


def sync(wiki="wiki", **kwargs):
    args = dict(src_dir="src", wiki_dir=wiki, cache_dir="cache", force=True)
    args.update(kwargs)
    if args.get("no_cache"):
        args.pop("cache_dir", None)
    sync_cmd.run(SimpleNamespace(**args))


def artifact_bytes(wiki="wiki"):
    return {name: (Path(wiki) / name).read_bytes() for name in ARTIFACTS}


@pytest.fixture(params=("cli", "api"))
def synced(tmp_path, monkeypatch, capsys, request):
    monkeypatch.chdir(tmp_path)
    subprocess.run(
        ["git", "init", "-q", str(tmp_path)], check=True, capture_output=True
    )
    Path("src").mkdir()
    Path("src/a.py").write_text(
        "from pathlib import Path\nclass Item:\n    pass\ndef save(value):\n    Path('out').write_text(value)\n",
        encoding="utf-8",
    )
    Path("src/b.py").write_text(
        "from a import save\ndef main():\n    return save('value')\n", encoding="utf-8"
    )
    Path("src/pyproject.toml").write_text(
        '[project]\nname="sample"\nversion="0.1.0"\n[project.scripts]\nrun="b:main"\n',
        encoding="utf-8",
    )
    Path("src/Dockerfile").write_text("FROM python:3.10\n", encoding="utf-8")
    if request.param == "cli":
        bootstrap_cmd.run(
            SimpleNamespace(
                src_dir="src",
                wiki_dir="wiki",
                depth="full",
                overwrite=False,
                source_adapter=True,
                skip_workflows=False,
            )
        )
    else:
        bootstrap_cmd.execute_bootstrap(
            BootstrapRequest(
                source_root=tmp_path / "src",
                wiki_root=tmp_path / "wiki",
                source_adapter=True,
            )
        )
    knowledge = load_knowledge_state("wiki").knowledge
    assert knowledge is not None
    capsys.readouterr()
    return tmp_path


@pytest.mark.parametrize("mode", ("default", "no_cache", "rebuild_knowledge"))
def test_first_sync_preserves_bootstrap_artifacts(synced, mode):
    before = artifact_bytes()
    sync(no_cache=mode == "no_cache", rebuild_knowledge=mode == "rebuild_knowledge")
    assert artifact_bytes() == before
    loaded = load_knowledge_state("wiki")
    assert loaded.knowledge is not None
    assert loaded.manifest_basis is not None
    commitment = loaded.knowledge.extensions[knowledge_reuse.REUSE_EXTENSION_KEY]
    assert (
        commitment
        == loaded.manifest_basis.generation_inputs[knowledge_reuse.REUSE_INPUT_KEY]
    )


@pytest.mark.parametrize(
    "profile",
    (
        "default",
        "no_flows",
        "no_dependencies",
        "no_data_flow",
        "api_contracts",
        "api_without_flows",
        "source_selection",
        "include_tests",
    ),
)
def test_first_sync_respects_bootstrap_surface_and_source_policies(
    tmp_path, monkeypatch, profile
):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n"
        "@app.get('/ping')\ndef ping() -> str:\n    return 'pong'\n",
        encoding="utf-8",
    )
    (source / "test_app.py").write_text(
        "from app import ping\ndef test_ping():\n    assert ping() == 'pong'\n",
        encoding="utf-8",
    )
    request = BootstrapRequest(source_root=source, wiki_root=tmp_path / "wiki")
    if profile == "no_flows":
        request = replace(request, skip_flows=True)
    elif profile == "no_dependencies":
        request = replace(request, skip_dependencies=True)
    elif profile == "no_data_flow":
        request = replace(request, skip_data_flow=True)
    elif profile in {"api_contracts", "api_without_flows"}:
        request = replace(
            request, api_contracts=True, skip_flows=profile == "api_without_flows"
        )
    elif profile == "source_selection":
        (source / "selection.json").write_text(
            json.dumps(
                {
                    "schema_version": "llm-wiki-source-selection/v1",
                    "include": ["app.py"],
                    "exclude": [],
                }
            ),
            encoding="utf-8",
        )
        request = replace(request, source_selection="selection.json")
    elif profile == "include_tests":
        request = replace(request, include_tests=("go",))
    bootstrap_cmd.execute_bootstrap(request)
    before = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in Path("wiki").rglob("*")
        if path.is_file()
    }
    for no_cache, rebuild_knowledge in ((False, False), (True, False), (True, True)):
        sync(
            no_cache=no_cache,
            rebuild_knowledge=rebuild_knowledge,
            no_plugins=True,
            source_selection=request.source_selection,
            include_tests=request.include_tests,
        )
        after = {
            path: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in Path("wiki").rglob("*")
            if path.is_file()
        }
        assert after == before
        assert load_knowledge_state("wiki").knowledge is not None


def test_shallow_bootstrap_does_not_authorize_knowledge_reuse(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text("class Item:\n    pass\n", encoding="utf-8")
    bootstrap_cmd.execute_bootstrap(
        BootstrapRequest(
            source_root=source, wiki_root=tmp_path / "wiki", depth="shallow"
        )
    )
    loaded = load_knowledge_state("wiki")
    assert loaded.knowledge is not None
    assert loaded.manifest_basis is not None
    assert knowledge_reuse.REUSE_EXTENSION_KEY not in loaded.knowledge.extensions
    assert (
        knowledge_reuse.REUSE_INPUT_KEY not in loaded.manifest_basis.generation_inputs
    )


@pytest.mark.parametrize(
    "no_cache,dry_run", [(False, False), (True, False), (False, True)]
)
def test_proven_noop_skips_graph_plan_serialization_and_writes(
    synced, monkeypatch, no_cache, dry_run
):
    before = artifact_bytes()
    mtimes = {
        path: path.stat().st_mtime_ns
        for path in Path("wiki").rglob("*")
        if path.is_file()
    }

    def unexpected(*args, **kwargs):
        pytest.fail("no-op invoked generation or artifact write")

    monkeypatch.setattr(sync_cmd, "_build_sync_graph_observations", unexpected)
    monkeypatch.setattr(
        knowledge_orchestration, "build_knowledge_generation_plan", unexpected
    )
    monkeypatch.setattr(knowledge_generation, "materialize_typed_graph", unexpected)
    monkeypatch.setattr(knowledge_generation, "serialize_knowledge_index", unexpected)
    monkeypatch.setattr(knowledge_artifacts, "write_bytes_atomic", unexpected)
    with patch.object(
        knowledge_orchestration,
        "validate_knowledge_artifacts",
        wraps=knowledge_orchestration.validate_knowledge_artifacts,
    ) as validate:
        sync(no_cache=no_cache, dry_run=dry_run)
    assert validate.call_count == 1
    assert artifact_bytes() == before
    assert {path: path.stat().st_mtime_ns for path in mtimes} == mtimes


def test_rebuild_knowledge_is_an_independent_full_oracle(synced):
    before = artifact_bytes()
    with patch.object(
        knowledge_orchestration,
        "build_knowledge_generation_plan",
        wraps=knowledge_orchestration.build_knowledge_generation_plan,
    ) as build:
        sync(rebuild_knowledge=True)
    assert build.call_count >= 1
    assert artifact_bytes() == before


@pytest.mark.parametrize(
    "change",
    ["source", "delete", "rename", "markdown", "asset", "options", "implementation"],
)
def test_changed_inputs_match_full_oracle_from_same_history(
    synced, monkeypatch, change
):
    shutil.copytree("wiki", "oracle")
    kwargs = {}
    if change == "source":
        with Path("src/a.py").open("a", encoding="utf-8") as stream:
            stream.write("\ndef changed():\n    return 7\n")
    elif change == "delete":
        Path("src/b.py").unlink()
    elif change == "rename":
        Path("src/b.py").rename("src/renamed.py")
    elif change == "markdown":
        for wiki in ("wiki", "oracle"):
            with (Path(wiki) / "modules/a.md").open("a", encoding="utf-8") as stream:
                stream.write("\n## Operator notes\nAuthored content.\n")
    elif change == "asset":
        for wiki in ("wiki", "oracle"):
            (Path(wiki) / "assets").mkdir(exist_ok=True)
            (Path(wiki) / "assets/example.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8"
            )
    elif change == "options":
        kwargs["no_preserve_semantic"] = True
    else:
        monkeypatch.setattr(
            knowledge_reuse, "implementation_hash", lambda: "sha256:" + "f" * 64
        )
    with patch.object(
        knowledge_orchestration,
        "build_knowledge_generation_plan",
        wraps=knowledge_orchestration.build_knowledge_generation_plan,
    ) as build:
        sync(**kwargs)
    assert build.call_count >= 1
    sync("oracle", rebuild_knowledge=True, **kwargs)
    assert artifact_bytes("wiki") == artifact_bytes("oracle")
    load_knowledge_state("wiki")


def test_forged_manifest_hint_cannot_authorize_old_projection(synced):
    path = Path("wiki/.llm-wiki-manifest.json")
    payload = json.loads(path.read_text())
    payload["generation_inputs"]["knowledge_reuse"]["source_snapshot_hash"] = (
        "sha256:" + "1" * 64
    )
    path.write_text(json.dumps(payload))
    with pytest.raises(KnowledgeStateLoadError):
        load_knowledge_state("wiki")
    state = knowledge_orchestration.capture_committed_knowledge(
        "wiki", SyncManifest.load(Path("wiki"))
    )
    assert state.artifacts is None


@pytest.mark.parametrize("changed", ["source", "wiki", "artifact"])
def test_change_during_reuse_check_aborts_without_rebuilding(
    synced, monkeypatch, changed
):
    real = sync_cmd.source_snapshot_matches_current_files

    def raced(snapshot):
        if changed == "source":
            Path("src/new.py").write_text("class New: pass\n", encoding="utf-8")
        elif changed == "wiki":
            with Path("wiki/index.md").open("a", encoding="utf-8") as stream:
                stream.write("\nConcurrent edit\n")
        else:
            with Path("wiki/.llm-wiki-knowledge.json").open("ab") as stream:
                stream.write(b" ")
        return real(snapshot)

    monkeypatch.setattr(sync_cmd, "source_snapshot_matches_current_files", raced)
    monkeypatch.setattr(
        knowledge_orchestration,
        "build_knowledge_generation_plan",
        lambda *_: pytest.fail("rebuilt after a race"),
    )
    with pytest.raises((SystemExit, knowledge_artifacts.KnowledgeArtifactError)):
        sync()


def test_reuse_manifest_state_must_validate_its_schema(synced):
    manifest = SyncManifest.load(Path("wiki"))
    assert isinstance(manifest.generation_inputs["knowledge_reuse"], dict)
    manifest.generation_inputs["knowledge_reuse"]["schema_version"] = "future"
    with pytest.raises(ValueError, match="reuse"):
        manifest.to_payload()


def test_governed_generation_keeps_using_full_builder(synced):
    from llm_wiki_cli.services.knowledge_governance import (
        GovernanceLedger,
        save_governance,
    )

    save_governance(
        "wiki", GovernanceLedger.empty("kb_reuse-regression"), expected_hash=None
    )
    sync()
    with patch.object(
        knowledge_orchestration,
        "build_knowledge_generation_plan",
        wraps=knowledge_orchestration.build_knowledge_generation_plan,
    ) as build:
        sync()
    assert build.call_count >= 1
    knowledge = load_knowledge_state("wiki").knowledge
    assert knowledge is not None
    assert knowledge_reuse.REUSE_EXTENSION_KEY not in knowledge.extensions
