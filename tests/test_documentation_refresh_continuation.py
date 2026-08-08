"""Focused source-revision continuation tests for documentation workspaces."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import llm_wiki_cli.services.documentation_run as documentation_run_service
from llm_wiki_cli.services import plugins
from llm_wiki_cli.services.bootstrap_service import BootstrapResult
from llm_wiki_cli.services.contracts import DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION
from llm_wiki_cli.services.documentation_run import (
    DocumentationIntegrityError,
    DocumentationRunError,
    build_documentation_agent_packet,
    prepare_documentation_run,
    record_documentation_agent_result,
)
from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION


def _install_fake_bootstrap(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_execute(request):
        source = Path(request.source_root)
        wiki = Path(request.wiki_root)
        revision_text = (source / "app.py").read_text(encoding="utf-8").strip()
        revision = "v2" if "second revision" in revision_text else "v1"
        (wiki / "modules").mkdir(parents=True, exist_ok=True)
        (wiki / "index.md").write_text(
            "# LLM Wiki Index\n\nUse this landing page to choose the right wiki surface.\n\n"
            "## Modules\n\n- [app](modules/app.md)\n",
            encoding="utf-8",
        )
        generated_description = "_Auto-generated from `app.py`._"
        (wiki / "modules" / "app.md").write_text(
            "# app Module\n\n**Path:** `app.py`\n\n## Description\n\n"
            f"{generated_description}\n\n## Local dependency map\n\n"
            "<!-- Auto-generated local dependency summary. Do not edit by hand. -->\n\n"
            f"Generated dependency evidence for {revision}.\n",
            encoding="utf-8",
        )
        (wiki / ".llm-wiki-manifest.json").write_text(
            json.dumps(
                {
                    "version": 4,
                    "sources": {
                        "app.py": {
                            "hash": (
                                "sha256:" + ("1" if revision == "v1" else "2") * 64
                            ),
                            "module_page": "app",
                            "entity_pages": {},
                            "entity_page_occurrences": [],
                            "generated_semantics": {
                                "module": {
                                    "description": generated_description,
                                    "classes": {},
                                    "functions": {},
                                },
                                "entities": {},
                            },
                        }
                    },
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (wiki / ".llm-wiki-surface.json").write_text(
            json.dumps(
                {
                    "schema_version": "llm-wiki-surface/v1",
                    "pages": [
                        {
                            "canonical_path": "modules/app.md",
                            "source_path": "app.py",
                        }
                    ],
                    "flows": [],
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return BootstrapResult(
            summary={
                "schema_version": "llm-wiki-bootstrap/v1",
                "src_dir": str(source),
                "generated_wiki_path": str(wiki),
                "created_files": [],
                "updated_files": [],
                "skipped_files": [],
                "unsupported_sources": {},
                "dependencies": {},
            }
        )

    monkeypatch.setattr(
        "llm_wiki_cli.commands.bootstrap_cmd.execute_bootstrap", fake_execute
    )
    monkeypatch.setattr(
        "llm_wiki_cli.services.documentation_run._run_wiki_validation_pair",
        lambda *args, **kwargs: True,
    )


def _prepare_source_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _install_fake_bootstrap(monkeypatch)
    source = tmp_path / "source Ω"
    source.mkdir()
    (source / "app.py").write_text("first revision\n", encoding="utf-8")
    workspace = tmp_path / "documentation workspace Ω"
    run = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="Continuation Docs",
    )
    return source, workspace, run


def _write_selection_profile(
    path: Path,
    *,
    include: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": include,
                "exclude": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_documentation_run_persists_default_selection_and_selected_baseline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_bootstrap(monkeypatch)
    source = tmp_path / "source"
    (source / "selected").mkdir(parents=True)
    (source / "excluded").mkdir()
    (source / "app.py").write_text("first revision\n", encoding="utf-8")
    (source / "selected" / "feature.py").write_text(
        "FEATURE = 1\n",
        encoding="utf-8",
    )
    excluded = source / "excluded" / "secret.py"
    excluded.write_text("SECRET = 1\n", encoding="utf-8")
    profile = source / ".llm-wiki" / "source-selection.json"
    _write_selection_profile(profile, include=["app.py", "selected"])
    workspace = tmp_path / "workspace"

    run = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="Selected Documentation",
    )

    selection = run.policy["source_selection"]
    assert selection["path"] == ".llm-wiki/source-selection.json"
    assert run.policy["source_selection_origin"] == "default"
    source_baseline = json.loads(
        (workspace / run.evidence["source_baseline"]).read_text(encoding="utf-8")
    )
    assert set(source_baseline["file_hashes"]) == {
        ".llm-wiki/source-selection.json",
        "app.py",
        "selected/feature.py",
    }
    assert "excluded/secret.py" not in source_baseline["file_hashes"]

    excluded.write_text("SECRET = 2\n", encoding="utf-8")
    resumed = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="Selected Documentation",
    )
    assert resumed.run_id == run.run_id

    (source / "selected" / "feature.py").write_text(
        "FEATURE = 2\n",
        encoding="utf-8",
    )
    with pytest.raises(DocumentationRunError, match="Source content changed"):
        prepare_documentation_run(
            workspace,
            source_root=source,
            site_name="Selected Documentation",
        )


def test_documentation_run_without_selection_keeps_legacy_whole_tree_baseline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_bootstrap(monkeypatch)
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("first revision\n", encoding="utf-8")
    arbitrary = source / "notes.proprietary"
    arbitrary.write_text("first arbitrary revision\n", encoding="utf-8")
    workspace = tmp_path / "workspace"

    run = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="Legacy Documentation",
    )
    source_baseline = json.loads(
        (workspace / run.evidence["source_baseline"]).read_text(encoding="utf-8")
    )
    assert "notes.proprietary" in source_baseline["file_hashes"]

    arbitrary.write_text("second arbitrary revision\n", encoding="utf-8")
    with pytest.raises(DocumentationRunError, match="Source content changed"):
        prepare_documentation_run(
            workspace,
            source_root=source,
            site_name="Legacy Documentation",
        )


def test_trusted_source_plugins_have_separate_frozen_integrity_baseline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_bootstrap(monkeypatch)
    monkeypatch.setattr(
        documentation_run_service,
        "_refresh_prepared_native_projection",
        lambda *_args, **_kwargs: None,
    )
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("first revision\n", encoding="utf-8")
    profile = source / ".llm-wiki" / "source-selection.json"
    _write_selection_profile(profile, include=["app.py"])
    plugin_store = source / ".llm-wiki" / "plugins" / "trusted"
    plugin_store.mkdir(parents=True)
    plugin_code = plugin_store / "plugin.py"
    plugin_code.write_text("PLUGIN_VALUE = 1\n", encoding="utf-8")
    (source / ".llm-wiki" / "plugins.lock.json").write_text(
        '{"plugins": {}, "version": 1}\n',
        encoding="utf-8",
    )
    workspace = tmp_path / "workspace"

    run = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="Trusted Plugin Documentation",
        trust_source_plugins=True,
    )

    selected_baseline = json.loads(
        (workspace / run.evidence["source_baseline"]).read_text(encoding="utf-8")
    )
    assert "plugins/trusted/plugin.py" not in selected_baseline["file_hashes"]
    plugin_baseline = json.loads(
        (workspace / run.evidence["source_plugins_baseline"]).read_text(
            encoding="utf-8"
        )
    )
    assert set(plugin_baseline["file_hashes"]) == {
        "plugins.lock.json",
        "plugins/trusted/plugin.py",
    }

    runtime_cache = plugin_store / "__pycache__"
    runtime_cache.mkdir()
    (runtime_cache / "plugin.cpython-314.pyc").write_bytes(b"runtime bytecode")
    resumed = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="Trusted Plugin Documentation",
        trust_source_plugins=True,
    )
    assert resumed.run_id == run.run_id

    plugin_code.write_text("PLUGIN_VALUE = 2\n", encoding="utf-8")
    with pytest.raises(DocumentationRunError, match="Trusted source plugins changed"):
        prepare_documentation_run(
            workspace,
            source_root=source,
            site_name="Trusted Plugin Documentation",
            trust_source_plugins=True,
        )


@pytest.mark.parametrize("configured", [False, True])
def test_external_documentation_trust_never_executes_ambient_plugins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    configured: bool,
) -> None:
    host = tmp_path / "host"
    host.mkdir()
    source = tmp_path / "external-source"
    source.mkdir()
    (source / "app.py").write_text(
        '"""External source."""\n\ndef run() -> str:\n    return "ok"\n',
        encoding="utf-8",
    )
    if configured:
        _write_selection_profile(
            source / ".llm-wiki" / "source-selection.json",
            include=["app.py"],
        )
    plugin_dir = host / "vendor" / "ambient-extractor"
    plugin_dir.mkdir(parents=True)
    module_name = "ambient_docs_extractor"
    (plugin_dir / plugins.MANIFEST_FILENAME).write_text(
        json.dumps(
            {
                "id": "ambient-docs-extractor",
                "version": "1.0.0",
                "llm_wiki_version": "*",
                "components": [
                    {
                        "type": "extractor",
                        "id": "ambient",
                        "language": "ambient",
                        "entry_point": f"{module_name}:AmbientExtractor",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (plugin_dir / f"{module_name}.py").write_text(
        "from pathlib import Path\n"
        "Path(__file__).with_name('AMBIENT_EXECUTED').write_text('unsafe')\n"
        "class AmbientExtractor:\n"
        "    last_error = None\n"
        "    def extract(self, **kwargs):\n"
        "        return {}\n",
        encoding="utf-8",
    )
    plugins.install_plugin(str(plugin_dir), root=host, yes=True)
    installed_module = (
        host
        / ".llm-wiki"
        / "plugins"
        / "ambient-docs-extractor"
        / f"{module_name}.py"
    )
    marker = installed_module.with_name("AMBIENT_EXECUTED")
    workspace = tmp_path / "workspace"
    monkeypatch.chdir(host)

    run = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="External Plugin Boundary",
        trust_source_plugins=True,
    )

    assert not marker.exists()
    installed_module.write_text(
        installed_module.read_text(encoding="utf-8") + "\nMUTATED = True\n",
        encoding="utf-8",
    )
    resumed = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="External Plugin Boundary",
        trust_source_plugins=True,
    )
    assert resumed.run_id == run.run_id
    assert not marker.exists()


def test_trusted_source_plugin_refresh_executes_newly_frozen_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = tmp_path / "host"
    host.mkdir()
    source = tmp_path / "external-source"
    source.mkdir()
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    _write_selection_profile(
        source / ".llm-wiki" / "source-selection.json",
        include=["app.py"],
    )
    plugin_dir = source / "vendor" / "source-extractor"
    plugin_dir.mkdir(parents=True)
    module_name = "source_docs_extractor"
    (plugin_dir / plugins.MANIFEST_FILENAME).write_text(
        json.dumps(
            {
                "id": "source-docs-extractor",
                "version": "1.0.0",
                "llm_wiki_version": "*",
                "components": [
                    {
                        "type": "extractor",
                        "id": "source",
                        "language": "source-custom",
                        "entry_point": f"{module_name}:SourceExtractor",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    marker = tmp_path / "plugin-executed-version"

    def plugin_code(version: str) -> str:
        return (
            "from pathlib import Path\n"
            "class SourceExtractor:\n"
            "    last_error = None\n"
            "    def extract(self, **kwargs):\n"
            f"        Path({str(marker)!r}).write_text('{version}')\n"
            "        return {}\n"
        )

    (plugin_dir / f"{module_name}.py").write_text(
        plugin_code("v1"), encoding="utf-8"
    )
    plugins.install_plugin(str(plugin_dir), root=source, yes=True)
    installed_module = (
        source
        / ".llm-wiki"
        / "plugins"
        / "source-docs-extractor"
        / f"{module_name}.py"
    )
    workspace = tmp_path / "workspace"
    monkeypatch.chdir(host)

    first = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="Source Plugin Refresh",
        trust_source_plugins=True,
    )
    assert marker.read_text(encoding="utf-8") == "v1"

    installed_module.write_text(plugin_code("v2"), encoding="utf-8")
    refreshed = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="Source Plugin Refresh",
        trust_source_plugins=True,
        refresh=True,
    )

    assert refreshed.run_id != first.run_id
    assert marker.read_text(encoding="utf-8") == "v2"


def test_trusted_source_plugin_refresh_reloads_changed_committed_resource(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = tmp_path / "host"
    host.mkdir()
    source = tmp_path / "external-source"
    source.mkdir()
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    plugin_dir = source / "vendor" / "resource-extractor"
    plugin_dir.mkdir(parents=True)
    module_name = "resource_docs_extractor"
    (plugin_dir / plugins.MANIFEST_FILENAME).write_text(
        json.dumps(
            {
                "id": "resource-docs-extractor",
                "version": "1.0.0",
                "llm_wiki_version": "*",
                "components": [
                    {
                        "type": "extractor",
                        "id": "resource",
                        "language": "resource-custom",
                        "entry_point": f"{module_name}:ResourceExtractor",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    marker = tmp_path / "resource-plugin-executed-version"
    (plugin_dir / "value.txt").write_text("v1", encoding="utf-8")
    (plugin_dir / f"{module_name}.py").write_text(
        "from pathlib import Path\n"
        "VALUE = Path(__file__).with_name('value.txt').read_text()\n"
        "class ResourceExtractor:\n"
        "    last_error = None\n"
        "    def extract(self, **kwargs):\n"
        f"        Path({str(marker)!r}).write_text(VALUE)\n"
        "        return {}\n",
        encoding="utf-8",
    )
    plugins.install_plugin(str(plugin_dir), root=source, yes=True)
    installed_resource = (
        source
        / ".llm-wiki"
        / "plugins"
        / "resource-docs-extractor"
        / "value.txt"
    )
    workspace = tmp_path / "workspace"
    monkeypatch.chdir(host)

    first = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="Source Plugin Resource Refresh",
        trust_source_plugins=True,
    )
    assert marker.read_text(encoding="utf-8") == "v1"

    installed_resource.write_text("v2", encoding="utf-8")
    refreshed = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="Source Plugin Resource Refresh",
        trust_source_plugins=True,
        refresh=True,
    )

    assert refreshed.run_id != first.run_id
    assert marker.read_text(encoding="utf-8") == "v2"


def test_documentation_run_pins_explicit_selection_and_refreshes_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_bootstrap(monkeypatch)
    source = tmp_path / "source"
    (source / "selected").mkdir(parents=True)
    (source / "alternate").mkdir()
    (source / "app.py").write_text("first revision\n", encoding="utf-8")
    (source / "selected" / "feature.py").write_text(
        "FEATURE = 1\n",
        encoding="utf-8",
    )
    (source / "alternate" / "feature.py").write_text(
        "FEATURE = 2\n",
        encoding="utf-8",
    )
    profile = source / "profiles" / "documentation.json"
    _write_selection_profile(profile, include=["app.py", "selected"])
    workspace = tmp_path / "workspace"
    options = {
        "source_root": source,
        "source_selection": "profiles/documentation.json",
        "site_name": "Explicit Selection Documentation",
    }

    run = prepare_documentation_run(workspace, **options)
    initial_selection = dict(run.policy["source_selection"])
    assert initial_selection["path"] == "profiles/documentation.json"
    assert run.policy["source_selection_origin"] == "explicit"
    assert prepare_documentation_run(workspace, **options).run_id == run.run_id

    _write_selection_profile(profile, include=["alternate", "app.py"])
    with pytest.raises(
        DocumentationIntegrityError,
        match="source selection changed since prepare",
    ):
        prepare_documentation_run(workspace, **options)

    refreshed = prepare_documentation_run(
        workspace,
        **options,
        refresh=True,
    )
    assert refreshed.run_id != run.run_id
    assert refreshed.policy["source_selection"] != initial_selection
    assert refreshed.policy["source_selection_origin"] == "explicit"
    refreshed_baseline = json.loads(
        (workspace / refreshed.evidence["source_baseline"]).read_text(
            encoding="utf-8"
        )
    )
    assert "alternate/feature.py" in refreshed_baseline["file_hashes"]
    assert "selected/feature.py" not in refreshed_baseline["file_hashes"]


def test_explicit_refresh_preserves_semantics_and_requires_regrounding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, workspace, prior = _prepare_source_run(tmp_path, monkeypatch)
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    module = workspace / "wiki" / "modules" / "app.md"
    module.write_text(
        module.read_text(encoding="utf-8").replace(
            "_Auto-generated from `app.py`._",
            "The prior agent explains how the application coordinates operator requests.",
        ),
        encoding="utf-8",
    )
    worklist = json.loads(
        (workspace / prior.evidence["semantic_worklist"]).read_text(encoding="utf-8")
    )
    items = [item for item in worklist["items"] if item.get("canonical_path")]
    record_documentation_agent_result(
        workspace,
        {
            "schema_version": DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION,
            "run_id": prior.run_id,
            "stage": "wiki-enrichment",
            "status": "complete",
            "changed_wiki_paths": ["modules/app.md"],
            "reused_work_ids": [],
            "completed_work_ids": [item["id"] for item in items],
            "deferred_work_ids": [],
            "claims_evidence_pages": sorted(
                {str(item["canonical_path"]) for item in items}
            ),
            "unresolved_unknowns": [],
            "unsupported_source_notices": [],
            "requested_follow_up_checks": [],
            "reported_source_writes": [],
            "reported_input_wiki_writes": [],
            "reported_generated_block_edits": [],
            "deferral_rationales": {},
            "findings": [],
        },
    )

    (source / "app.py").write_text("second revision\n", encoding="utf-8")
    refreshed = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="Continuation Docs",
        refresh=True,
    )

    assert refreshed.run_id != prior.run_id
    refreshed_text = module.read_text(encoding="utf-8")
    assert "prior agent explains" in refreshed_text
    assert "Generated dependency evidence for v2" in refreshed_text
    assert "Generated dependency evidence for v1" not in refreshed_text

    continuation = json.loads(
        (workspace / refreshed.evidence["continuation"]).read_text(encoding="utf-8")
    )
    assert continuation["prior_run_id"] == prior.run_id
    assert continuation["prior_source_revision"] == prior.source["revision"]
    assert continuation["source_revision"] == refreshed.source["revision"]
    assert continuation["preserved_semantic_paths"] == ["modules/app.md"]
    assert continuation["preserved_semantic_hash"].startswith("sha256:")
    archive = workspace / continuation["archive_path"]
    assert (archive / "run.json").is_file()
    assert (archive / "wiki" / "modules" / "app.md").is_file()

    refreshed_worklist = json.loads(
        (workspace / refreshed.evidence["semantic_worklist"]).read_text(
            encoding="utf-8"
        )
    )
    continued = next(
        item
        for item in refreshed_worklist["items"]
        if item.get("canonical_path") == "modules/app.md"
    )
    assert continued["imported_classification"] == "needs_grounding"
    assert continued["grounding_status"] == "unknown"
    assert continued["status"] == "open"
    assert "continuation:source_revision_changed" in continued["signals"]
    assert "evidence:continuation.json" in continued["suggested_context"]


def test_refresh_refuses_changed_generated_ownership_before_archive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, workspace, prior = _prepare_source_run(tmp_path, monkeypatch)
    module = workspace / "wiki" / "modules" / "app.md"
    module.write_text(
        module.read_text(encoding="utf-8").replace(
            "Generated dependency evidence for v1",
            "Agent changed a protected generated block",
        ),
        encoding="utf-8",
    )
    (source / "app.py").write_text("second revision\n", encoding="utf-8")

    with pytest.raises(DocumentationIntegrityError, match="generated ownership"):
        prepare_documentation_run(
            workspace,
            source_root=source,
            site_name="Continuation Docs",
            refresh=True,
        )

    assert (
        json.loads(
            (workspace / ".llm-wiki-docs" / "run.json").read_text(encoding="utf-8")
        )["run_id"]
        == prior.run_id
    )
    history = workspace / ".llm-wiki-docs" / "history"
    assert not history.exists() or not any(history.iterdir())


def test_refresh_failure_after_archive_restores_prior_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, workspace, prior = _prepare_source_run(tmp_path, monkeypatch)
    prior_module = (workspace / "wiki" / "modules" / "app.md").read_bytes()
    (source / "app.py").write_text("second revision\n", encoding="utf-8")

    def fail_after_archive(_workspace_root):
        raise RuntimeError("injected post-archive failure")

    monkeypatch.setattr(
        documentation_run_service,
        "_export_documentation_skills",
        fail_after_archive,
    )
    with pytest.raises(RuntimeError, match="post-archive"):
        prepare_documentation_run(
            workspace,
            source_root=source,
            site_name="Continuation Docs",
            refresh=True,
        )

    restored = json.loads(
        (workspace / ".llm-wiki-docs" / "run.json").read_text(encoding="utf-8")
    )
    assert restored["run_id"] == prior.run_id
    assert (workspace / "wiki" / "modules" / "app.md").read_bytes() == prior_module
    assert not (workspace / ".llm-wiki-docs" / "refresh-transaction.json").exists()


def test_prepare_recovers_interrupted_refresh_archive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, workspace, prior = _prepare_source_run(tmp_path, monkeypatch)
    transaction = documentation_run_service._RefreshArchiveTransaction()
    documentation_run_service._archive_owned_run(
        workspace,
        prior,
        transaction=transaction,
    )
    assert not (workspace / ".llm-wiki-docs" / "run.json").exists()
    assert (workspace / ".llm-wiki-docs" / "refresh-transaction.json").is_file()

    resumed = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="Continuation Docs",
    )

    assert resumed.run_id == prior.run_id
    assert not (workspace / ".llm-wiki-docs" / "refresh-transaction.json").exists()
