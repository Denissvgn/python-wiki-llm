"""Incremental infrastructure regeneration and evidence-state contracts."""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, lint_cmd, sync_cmd
from llm_wiki_cli.commands.lint_cmd import (
    LintReport,
    _check_infrastructure_coverage,
)
from llm_wiki_cli.commands.extract_cmd import get_docker_inventory
from llm_wiki_cli.services import skills
from llm_wiki_cli.services.infrastructure_inventory import (
    get_yaml_infrastructure_inventory,
)
from llm_wiki_cli.services.infrastructure_sync import (
    INFRASTRUCTURE_SYNC_SCHEMA_VERSION,
    InfrastructureSyncError,
    build_infrastructure_page_map,
    build_infrastructure_sync_plan,
    validate_infrastructure_generation_input,
    with_infrastructure_generation_input,
)
from llm_wiki_cli.services.knowledge_evidence import is_valid_sha256
from llm_wiki_cli.services.knowledge_loader import (
    KnowledgeStateLoadError,
    load_knowledge_state,
)
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.section_ownership import (
    SectionOwnership,
    observe_page_sections,
)
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from llm_wiki_cli.services.wiki_surface import PageKind


def _bootstrap_args(project: Path, wiki: Path, **overrides):
    values = {
        "src_dir": str(project),
        "wiki_dir": str(wiki),
        "overwrite": False,
        "depth": "full",
        "skip_workflows": True,
        "source_adapter": True,
    }
    values.update(overrides)
    return types.SimpleNamespace(**values)


def _sync_args(project: Path, wiki: Path, **overrides):
    values = {"src_dir": str(project), "wiki_dir": str(wiki)}
    values.update(overrides)
    return types.SimpleNamespace(**values)


def _write_fixture(project: Path) -> None:
    (project / "app.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    (project / "Dockerfile").write_text(
        "FROM python:3.12\nEXPOSE 8000\n",
        encoding="utf-8",
    )
    (project / "compose.yml").write_text(
        "services:\n  api:\n    image: nginx:1\n",
        encoding="utf-8",
    )
    (project / "prometheus.yml").write_text(
        "scrape_configs:\n  - job_name: api-v1\n",
        encoding="utf-8",
    )
    workflow = project / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        "    steps:\n      - uses: actions/checkout@v4\n",
        encoding="utf-8",
    )
    manifest = project / "k8s" / "deployment.yml"
    manifest.parent.mkdir()
    manifest.write_text(
        "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: api\n"
        "spec:\n  replicas: 1\n",
        encoding="utf-8",
    )
    alternate = project / "alternate" / "deployment.yaml"
    alternate.parent.mkdir()
    alternate.write_text(
        "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: unsupported\n",
        encoding="utf-8",
    )


def _manifest(wiki: Path) -> dict:
    return json.loads(
        (wiki / ".llm-wiki-manifest.json").read_text(encoding="utf-8")
    )


def _json_artifact(wiki: Path, filename: str) -> dict:
    return json.loads((wiki / filename).read_text(encoding="utf-8"))


def _wiki_bytes(wiki: Path) -> dict[str, bytes]:
    return {
        path.relative_to(wiki).as_posix(): path.read_bytes()
        for path in sorted(wiki.rglob("*"))
        if path.is_file()
    }


def test_sync_regenerates_all_infrastructure_families_and_preserves_only_notes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    _write_fixture(project)
    wiki = project / "docs" / "llm_wiki"
    monkeypatch.chdir(project)

    bootstrap_cmd.run(_bootstrap_args(project, wiki))
    state = _manifest(wiki)["generation_inputs"]["infrastructure"]
    assert state["schema_version"] == INFRASTRUCTURE_SYNC_SCHEMA_VERSION
    assert state["status"] == "supported-sources"
    assert state["discovery"]["roots"] == [
        ".",
        ".github/workflows",
        "alternate",
        "k8s",
    ]
    assert state["discovery"]["unsupported_yaml"] == [
        {
            "path": "alternate/deployment.yaml",
            "reason": "unrecognized-yaml",
            "source_content_hash": state["discovery"]["unsupported_yaml"][0][
                "source_content_hash"
            ],
        }
    ]
    assert is_valid_sha256(
        state["sources"]["Dockerfile"]["evidence_basis"]["source_content_hash"]
    )
    assert is_valid_sha256(
        state["sources"]["Dockerfile"]["evidence_basis"]["observation_hash"]
    )
    before_knowledge = _json_artifact(wiki, ".llm-wiki-knowledge.json")
    before_concepts = {
        item["document"]["canonical_path"]: item
        for item in before_knowledge["concepts"]
    }
    before_snapshot = before_knowledge["bundle"]["snapshot"]

    docker_page = wiki / "infrastructure" / "Dockerfile.md"
    docker_page.write_text(
        docker_page.read_text(encoding="utf-8").replace(
            "_Add reviewed operational context here; generated sections are "
            "replaced from source observations._",
            "Keep this operator note.",
        )
        + "\n## Unsupported Heading\n\nDo not carry this forward.\n",
        encoding="utf-8",
    )
    (project / "Dockerfile").write_text(
        "FROM python:3.13\nEXPOSE 9000\n",
        encoding="utf-8",
    )
    (project / "compose.yml").write_text(
        "services:\n  api:\n    image: nginx:2\n",
        encoding="utf-8",
    )
    (project / "prometheus.yml").write_text(
        "scrape_configs:\n  - job_name: api-v2\n",
        encoding="utf-8",
    )
    (project / ".github" / "workflows" / "ci.yml").write_text(
        "name: CI\non: pull_request\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        "    steps:\n      - uses: actions/checkout@v5\n",
        encoding="utf-8",
    )
    (project / "k8s" / "deployment.yml").write_text(
        "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: api\n"
        "spec:\n  replicas: 3\n",
        encoding="utf-8",
    )

    sync_cmd.run(_sync_args(project, wiki, source_adapter=True))
    output = capsys.readouterr().out
    assert "Unsupported infrastructure YAML: alternate/deployment.yaml" in output
    assert "python:3.13" in docker_page.read_text(encoding="utf-8")
    assert "Keep this operator note." in docker_page.read_text(encoding="utf-8")
    assert "Unsupported Heading" not in docker_page.read_text(encoding="utf-8")
    assert "nginx:2" in (
        wiki / "infrastructure" / "compose_yml.md"
    ).read_text(encoding="utf-8")
    assert "api-v2" in (
        wiki / "infrastructure" / "prometheus_yml.md"
    ).read_text(encoding="utf-8")
    assert "actions/checkout@v5" in (
        wiki / "infrastructure" / "_github_workflows_ci_yml.md"
    ).read_text(encoding="utf-8")
    assert "| 3 |" in (
        wiki / "infrastructure" / "k8s_deployment_yml.md"
    ).read_text(encoding="utf-8")
    after_state = _manifest(wiki)["generation_inputs"]["infrastructure"]
    after_knowledge = _json_artifact(wiki, ".llm-wiki-knowledge.json")
    after_concepts = {
        item["document"]["canonical_path"]: item
        for item in after_knowledge["concepts"]
    }
    assert (
        after_knowledge["bundle"]["snapshot"]["source_snapshot_hash"]
        != before_snapshot["source_snapshot_hash"]
    )
    assert (
        after_knowledge["bundle"]["snapshot"]["markdown_snapshot_hash"]
        != before_snapshot["markdown_snapshot_hash"]
    )
    for source_path in (
        "Dockerfile",
        "compose.yml",
        "prometheus.yml",
        ".github/workflows/ci.yml",
        "k8s/deployment.yml",
    ):
        page_path = after_state["sources"][source_path]["page_path"]
        before_basis = before_concepts[page_path]["facets"]["structure"]["basis"]
        after_concept = after_concepts[page_path]
        after_basis = after_concept["facets"]["structure"]["basis"]
        assert after_basis["source_content_hash"] == (
            after_state["sources"][source_path]["source_content_hash"]
        )
        assert after_basis["concept_observation_hash"] == (
            after_state["sources"][source_path]["observation_hash"]
        )
        assert (
            after_basis["concept_observation_hash"]
            != before_basis["concept_observation_hash"]
        )
    assert (
        after_concepts["infrastructure/Dockerfile.md"]["facets"]["semantics"][
            "page_hash"
        ]
        != before_concepts["infrastructure/Dockerfile.md"]["facets"]["semantics"][
            "page_hash"
        ]
    )

    stable = _wiki_bytes(wiki)
    sync_cmd.run(_sync_args(project, wiki))
    assert _wiki_bytes(wiki) == stable

    docker_page.write_text(
        docker_page.read_text(encoding="utf-8")
        + "\n## Unsupported Again\n\nThis must not survive a source no-op.\n",
        encoding="utf-8",
    )
    sync_cmd.run(_sync_args(project, wiki))
    assert "Unsupported Again" not in docker_page.read_text(encoding="utf-8")
    assert "Keep this operator note." in docker_page.read_text(encoding="utf-8")

    moved = project / "containers" / "Dockerfile"
    moved.parent.mkdir()
    (project / "Dockerfile").replace(moved)
    sync_cmd.run(_sync_args(project, wiki))
    moved_page = wiki / "infrastructure" / "containers_Dockerfile.md"
    assert moved_page.is_file()
    assert "Keep this operator note." in moved_page.read_text(encoding="utf-8")
    assert not docker_page.exists()
    moved_state = _manifest(wiki)["generation_inputs"]["infrastructure"]
    assert moved_state["tombstones"]["Dockerfile"]["reason"] == "source-moved"
    assert moved_state["tombstones"]["Dockerfile"]["moved_to"] == (
        "containers/Dockerfile"
    )
    moved_surface = _json_artifact(wiki, ".llm-wiki-surface.json")
    moved_surface_paths = {
        page["canonical_path"]: page for page in moved_surface["pages"]
    }
    assert "infrastructure/Dockerfile.md" not in moved_surface_paths
    assert moved_surface_paths[
        "infrastructure/containers_Dockerfile.md"
    ]["source_path"] == "containers/Dockerfile"
    moved_knowledge = _json_artifact(wiki, ".llm-wiki-knowledge.json")
    moved_concept = next(
        item
        for item in moved_knowledge["concepts"]
        if item["document"]["canonical_path"]
        == "infrastructure/containers_Dockerfile.md"
    )
    assert moved_concept["facets"]["structure"]["basis"]["source_path"] == (
        "containers/Dockerfile"
    )
    docker_page.write_text("# falsely resurrected\n", encoding="utf-8")
    sync_cmd.run(_sync_args(project, wiki))
    assert not docker_page.exists()

    kubernetes_source = project / "k8s" / "deployment.yml"
    kubernetes_source.unlink()
    sync_cmd.run(_sync_args(project, wiki))
    removed_page = wiki / "infrastructure" / "k8s_deployment_yml.md"
    assert "Stale observation" in removed_page.read_text(encoding="utf-8")
    assert "source-removed" in removed_page.read_text(encoding="utf-8")
    removed_state = _manifest(wiki)["generation_inputs"]["infrastructure"]
    assert "k8s/deployment.yml" not in removed_state["sources"]
    assert (
        removed_state["tombstones"]["k8s/deployment.yml"]["reason"]
        == "source-removed"
    )
    removed_knowledge = _json_artifact(wiki, ".llm-wiki-knowledge.json")
    removed_concept = next(
        item
        for item in removed_knowledge["concepts"]
        if item["document"]["canonical_path"]
        == "infrastructure/k8s_deployment_yml.md"
    )
    assert removed_concept["facets"]["structure"]["basis"]["source_path"] == (
        "k8s/deployment.yml"
    )
    removed_page.write_text(
        "# Kubernetes\n\n**Observation State:** `current`\n",
        encoding="utf-8",
    )
    sync_cmd.run(_sync_args(project, wiki))
    assert "Stale observation" in removed_page.read_text(encoding="utf-8")
    final_snapshot = build_source_snapshot(project)
    lint_report = LintReport(
        wiki_dir=str(wiki),
        src_dir=str(project),
        strict=True,
    )
    _check_infrastructure_coverage(
        lint_report,
        wiki,
        get_docker_inventory(project, source_snapshot=final_snapshot),
        get_yaml_infrastructure_inventory(
            project,
            source_snapshot=final_snapshot,
        ),
    )
    assert lint_report.issues == []


def test_infrastructure_native_evidence_and_strict_freshness_are_live(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    dockerfile = project / "Dockerfile"
    dockerfile.write_text("FROM python:3.12\nEXPOSE 8000\n", encoding="utf-8")
    unsupported = project / "alternate.yaml"
    unsupported.write_text(
        "apiVersion: v1\nkind: Service\n",
        encoding="utf-8",
    )
    wiki = project / "docs" / "llm_wiki"
    monkeypatch.chdir(project)

    bootstrap_cmd.run(_bootstrap_args(project, wiki))
    manifest = _manifest(wiki)
    infrastructure_state = manifest["generation_inputs"]["infrastructure"]
    record = infrastructure_state["sources"]["Dockerfile"]
    surface = _json_artifact(wiki, ".llm-wiki-surface.json")
    surface_page = next(
        page
        for page in surface["pages"]
        if page["canonical_path"] == "infrastructure/Dockerfile.md"
    )
    assert surface_page["source_path"] == "Dockerfile"
    knowledge = _json_artifact(wiki, ".llm-wiki-knowledge.json")
    concept = next(
        item
        for item in knowledge["concepts"]
        if item["document"]["canonical_path"] == "infrastructure/Dockerfile.md"
    )
    basis = concept["facets"]["structure"]["basis"]
    assert concept["facets"]["structure"]["origin"] == "extracted"
    assert concept["facets"]["structure"]["evidence"] == "present"
    assert basis == {
        "scope": "infrastructure",
        "source_path": "Dockerfile",
        "extractor_ref": "llm-wiki/extractor/infrastructure",
        "source_content_hash": record["source_content_hash"],
        "concept_observation_hash": record["observation_hash"],
    }
    assert any(
        relationship["kind"] == "derived_from"
        and relationship["from"] == concept["locator"]
        and relationship["target"]["source_path"] == "Dockerfile"
        for relationship in knowledge["relationships"]
    )
    assert not any(
        item["document"]["canonical_path"].endswith("alternate_yaml.md")
        for item in knowledge["concepts"]
    )

    current = lint_cmd.build_report(
        str(wiki),
        str(project),
        strict=True,
    )
    assert current.count("knowledge_evidence") == 0
    assert current.count("knowledge_freshness") == 0

    dockerfile.write_text("FROM python:3.13\nEXPOSE 9000\n", encoding="utf-8")
    changed = lint_cmd.build_report(
        str(wiki),
        str(project),
        strict=True,
    )
    changed_messages = [
        issue.message
        for issue in changed.issues
        if issue.category == "knowledge_freshness"
        and issue.path == "infrastructure/Dockerfile.md"
    ]
    assert any("source-changed" in message for message in changed_messages)

    dockerfile.unlink()
    removed = lint_cmd.build_report(
        str(wiki),
        str(project),
        strict=True,
    )
    removed_messages = [
        issue.message
        for issue in removed.issues
        if issue.category == "knowledge_freshness"
        and issue.path == "infrastructure/Dockerfile.md"
    ]
    assert any("source-missing" in message for message in removed_messages)


def test_rebootstrap_skip_never_claims_changed_infrastructure_is_current(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    dockerfile = project / "Dockerfile"
    dockerfile.write_text("FROM python:3.12\n", encoding="utf-8")
    wiki = project / "docs" / "llm_wiki"
    monkeypatch.chdir(project)

    bootstrap_cmd.run(_bootstrap_args(project, wiki))
    before_state = _manifest(wiki)["generation_inputs"]["infrastructure"]
    before_hash = before_state["sources"]["Dockerfile"]["source_content_hash"]
    dockerfile.write_text("FROM python:3.13\n", encoding="utf-8")

    bootstrap_cmd.run(_bootstrap_args(project, wiki))
    after_state = _manifest(wiki)["generation_inputs"]["infrastructure"]
    assert after_state["sources"]["Dockerfile"]["source_content_hash"] == before_hash
    assert after_state["deferred_sources"] == ["Dockerfile"]
    assert "python:3.12" in (
        wiki / "infrastructure" / "Dockerfile.md"
    ).read_text(encoding="utf-8")
    report = lint_cmd.build_report(str(wiki), str(project), strict=True)
    messages = [
        issue.message
        for issue in report.issues
        if issue.category == "knowledge_freshness"
        and issue.path == "infrastructure/Dockerfile.md"
    ]
    assert any("source-changed" in message for message in messages)

    sync_cmd.run(_sync_args(project, wiki))
    refreshed_state = _manifest(wiki)["generation_inputs"]["infrastructure"]
    assert "deferred_sources" not in refreshed_state
    assert "python:3.13" in (
        wiki / "infrastructure" / "Dockerfile.md"
    ).read_text(encoding="utf-8")


def test_infrastructure_dry_run_and_interrupted_finalize_are_recoverable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text(
        "def main():\n    return 1\n",
        encoding="utf-8",
    )
    compose = project / "compose.yml"
    compose.write_text("services:\n  api:\n    image: nginx:1\n", encoding="utf-8")
    wiki = project / "docs" / "llm_wiki"
    monkeypatch.chdir(project)
    bootstrap_cmd.run(_bootstrap_args(project, wiki))

    compose.write_text("services:\n  api:\n    image: nginx:2\n", encoding="utf-8")
    before = _wiki_bytes(wiki)
    sync_cmd.run(_sync_args(project, wiki, dry_run=True))
    assert _wiki_bytes(wiki) == before
    dry_run_output = capsys.readouterr().out
    assert "infrastructure sources: 0 new, 1 changed, 0 moved, 0 removed" in (
        dry_run_output
    )
    assert "DRY-RUN: no files modified." in dry_run_output

    real_finalize = sync_cmd._finalize_prepared_sync

    def interrupt(*_args, **_kwargs):
        raise RuntimeError("simulated interrupted finalization")

    monkeypatch.setattr(sync_cmd, "_finalize_prepared_sync", interrupt)
    with pytest.raises(RuntimeError, match="interrupted"):
        sync_cmd.run(_sync_args(project, wiki))
    page = wiki / "infrastructure" / "compose_yml.md"
    assert "nginx:2" in page.read_text(encoding="utf-8")
    with pytest.raises(KnowledgeStateLoadError) as interrupted:
        load_knowledge_state(wiki)
    assert interrupted.value.status is KnowledgeLoadState.MIXED_SNAPSHOT

    monkeypatch.setattr(sync_cmd, "_finalize_prepared_sync", real_finalize)
    sync_cmd.run(_sync_args(project, wiki))
    state = _manifest(wiki)["generation_inputs"]["infrastructure"]
    assert state["sources"]["compose.yml"]["state"] == "current"
    assert "nginx:2" in page.read_text(encoding="utf-8")
    assert load_knowledge_state(wiki).status is KnowledgeLoadState.VALID

    page.write_text(
        page.read_text(encoding="utf-8").replace(
            "_Add reviewed operational context here; generated sections are "
            "replaced from source observations._",
            "Discard this note when semantic preservation is disabled.",
        ),
        encoding="utf-8",
    )
    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            no_preserve_semantic=True,
        )
    )
    assert "Discard this note" not in page.read_text(encoding="utf-8")


def test_infrastructure_plan_distinguishes_empty_unsupported_and_large_change(
    tmp_path: Path,
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    empty_snapshot = build_source_snapshot(empty)
    empty_plan = build_infrastructure_sync_plan(empty_snapshot, {})
    assert empty_plan.next_state["status"] == "nothing-discovered"
    assert empty_plan.current_sources == {}
    assert empty_plan.unsupported_yaml == ()

    unsupported = tmp_path / "unsupported"
    unsupported.mkdir()
    (unsupported / "deployment.yaml").write_text(
        "apiVersion: v1\nkind: Service\n",
        encoding="utf-8",
    )
    unsupported_snapshot = build_source_snapshot(unsupported)
    unsupported_plan = build_infrastructure_sync_plan(unsupported_snapshot, {})
    assert unsupported_plan.next_state["status"] == "unsupported-only"
    assert unsupported_plan.current_sources == {}
    assert unsupported_plan.unsupported_yaml[0]["path"] == "deployment.yaml"

    broad = tmp_path / "broad"
    broad.mkdir()
    for index in range(51):
        (broad / f"Dockerfile.{index}").write_text(
            "FROM alpine\n",
            encoding="utf-8",
        )
    first_snapshot = build_source_snapshot(broad)
    first_inventory = get_docker_inventory(
        broad,
        source_snapshot=first_snapshot,
    )
    first_plan = build_infrastructure_sync_plan(first_snapshot, first_inventory)
    generation_inputs = with_infrastructure_generation_input({}, first_plan)
    for index in range(51):
        (broad / f"Dockerfile.{index}").write_text(
            "FROM busybox\n",
            encoding="utf-8",
        )
    second_snapshot = build_source_snapshot(broad)
    second_inventory = get_docker_inventory(
        broad,
        source_snapshot=second_snapshot,
    )
    second_plan = build_infrastructure_sync_plan(
        second_snapshot,
        second_inventory,
        generation_inputs=generation_inputs,
    )
    assert second_plan.changed_sources == tuple(
        sorted(f"Dockerfile.{index}" for index in range(51))
    )
    assert "exceeds the safety limit" in (
        sync_cmd._large_infrastructure_message(second_plan) or ""
    )


def test_infrastructure_plan_fails_closed_on_future_persisted_schema(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    snapshot = build_source_snapshot(project)
    generation_inputs = {
        "infrastructure": {
            "schema_version": "llm-wiki-infrastructure-sync/v2",
            "sources": {},
            "tombstones": {},
        }
    }

    with pytest.raises(
        InfrastructureSyncError,
        match=r"infrastructure\.schema_version is unsupported",
    ):
        validate_infrastructure_generation_input(generation_inputs)
    with pytest.raises(
        InfrastructureSyncError,
        match=r"infrastructure\.schema_version is unsupported",
    ):
        build_infrastructure_sync_plan(
            snapshot,
            {},
            generation_inputs=generation_inputs,
        )
    for invalid in (None, [], "llm-wiki-infrastructure-sync/v2"):
        with pytest.raises(
            InfrastructureSyncError,
            match=r"infrastructure must be an object",
        ):
            validate_infrastructure_generation_input(
                {"infrastructure": invalid}
            )


def test_infrastructure_plan_preserves_absent_and_supported_prior_state(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "Dockerfile").write_text("FROM alpine\n", encoding="utf-8")
    snapshot = build_source_snapshot(project)
    inventory = get_docker_inventory(project, source_snapshot=snapshot)

    validate_infrastructure_generation_input(None)
    absent_plan = build_infrastructure_sync_plan(
        snapshot,
        inventory,
        generation_inputs={},
    )
    assert absent_plan.prior_sources == {}
    assert absent_plan.new_sources == ("Dockerfile",)

    generation_inputs = with_infrastructure_generation_input({}, absent_plan)
    validate_infrastructure_generation_input(generation_inputs)
    supported_plan = build_infrastructure_sync_plan(
        snapshot,
        inventory,
        generation_inputs=generation_inputs,
    )
    assert supported_plan.prior_sources == absent_plan.current_sources
    assert supported_plan.unchanged_sources == ("Dockerfile",)
    assert supported_plan.new_sources == ()


def test_infrastructure_notes_are_the_only_semantic_section() -> None:
    page = observe_page_sections(
        "# Compose\n\n## Services\n\ngenerated\n\n"
        "## Notes\n\nreviewed context\n\n## Custom\n\nunsupported\n",
        "llm-wiki://infrastructure/compose_yml",
        PageKind.INFRASTRUCTURE,
    )
    ownership = {
        section.title: section.ownership
        for section in page.sections
        if section.title is not None
    }
    assert ownership["Services"] is SectionOwnership.GENERATED
    assert ownership["Notes"] is SectionOwnership.SEMANTIC
    assert ownership["Custom"] is SectionOwnership.UNKNOWN


def test_infrastructure_page_mapping_disambiguates_flattened_path_collisions() -> None:
    mapping = build_infrastructure_page_map(
        ["deploy/api.yml", "deploy_api.yml", "Dockerfile"]
    )
    assert mapping["Dockerfile"] == "infrastructure/Dockerfile.md"
    assert mapping["deploy/api.yml"] != mapping["deploy_api.yml"]
    assert all(
        page.startswith("infrastructure/deploy_api_yml__")
        for source, page in mapping.items()
        if source != "Dockerfile"
    )


def test_persisted_infrastructure_mapping_rejects_path_escape() -> None:
    with pytest.raises(InfrastructureSyncError, match="unsafe source path"):
        validate_infrastructure_generation_input(
            {
                "infrastructure": {
                    "schema_version": INFRASTRUCTURE_SYNC_SCHEMA_VERSION,
                    "sources": {
                        "../Dockerfile": {
                            "source_path": "../Dockerfile",
                            "page_path": "infrastructure/Dockerfile.md",
                            "source_content_hash": "sha256:" + "0" * 64,
                            "observation_hash": "sha256:" + "1" * 64,
                        }
                    },
                    "tombstones": {},
                }
            }
        )
    with pytest.raises(InfrastructureSyncError, match="must match its source record"):
        validate_infrastructure_generation_input(
            {
                "infrastructure": {
                    "schema_version": INFRASTRUCTURE_SYNC_SCHEMA_VERSION,
                    "sources": {
                        "Dockerfile": {
                            "state": "current",
                            "source_path": "Dockerfile",
                            "page_path": "infrastructure/Dockerfile.md",
                            "adapter": "dockerfile",
                            "source_content_hash": "sha256:" + "0" * 64,
                            "observation_hash": "sha256:" + "1" * 64,
                            "evidence_basis": {
                                "discovery_root": ".",
                                "source_content_hash": "sha256:" + "0" * 64,
                                "observation_hash": "sha256:" + "2" * 64,
                                "adapter": "dockerfile",
                            },
                        }
                    },
                    "tombstones": {},
                }
            }
        )


def test_collision_mapping_rename_carries_notes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    nested = project / "a" / "b.yml"
    nested.parent.mkdir()
    nested.write_text(
        "services:\n  api:\n    image: nginx\n",
        encoding="utf-8",
    )
    wiki = project / "docs" / "llm_wiki"
    monkeypatch.chdir(project)
    bootstrap_cmd.run(_bootstrap_args(project, wiki))

    legacy_page = wiki / "infrastructure" / "a_b_yml.md"
    legacy_page.write_text(
        legacy_page.read_text(encoding="utf-8").replace(
            "_Add reviewed operational context here; generated sections are "
            "replaced from source observations._",
            "Carry this collision-safe note.",
        ),
        encoding="utf-8",
    )
    colliding = project / "a_b.yml"
    colliding.write_text(
        "services:\n  worker:\n    image: busybox\n",
        encoding="utf-8",
    )
    sync_cmd.run(_sync_args(project, wiki))
    state = _manifest(wiki)["generation_inputs"]["infrastructure"]
    nested_page = wiki / state["sources"]["a/b.yml"]["page_path"]
    other_page = wiki / state["sources"]["a_b.yml"]["page_path"]
    assert nested_page != other_page
    assert nested_page.is_file() and other_page.is_file()
    assert "Carry this collision-safe note." in nested_page.read_text(encoding="utf-8")
    assert not legacy_page.exists()

    colliding.unlink()
    sync_cmd.run(_sync_args(project, wiki))
    assert legacy_page.is_file()
    assert "Carry this collision-safe note." in legacy_page.read_text(encoding="utf-8")


def test_external_source_adapter_sync_uses_repository_relative_infra_basis(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    source = tmp_path / "source"
    workspace.mkdir()
    source.mkdir()
    (source / "app.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    dockerfile = source / "Dockerfile"
    dockerfile.write_text("FROM alpine:3.20\n", encoding="utf-8")
    wiki = workspace / "docs" / "llm_wiki"
    monkeypatch.chdir(workspace)

    bootstrap_cmd.run(
        _bootstrap_args(
            source,
            wiki,
            allow_external_src=True,
            source_adapter=True,
        )
    )
    dockerfile.write_text("FROM alpine:3.21\n", encoding="utf-8")
    sync_cmd.run(
        _sync_args(
            source,
            wiki,
            allow_external_src=True,
        )
    )

    state = _manifest(wiki)["generation_inputs"]["infrastructure"]
    record = state["sources"]["Dockerfile"]
    assert record["source_path"] == "Dockerfile"
    assert record["evidence_basis"]["discovery_root"] == "."
    assert str(source) not in json.dumps(state)
    assert "alpine:3.21" in (
        wiki / "infrastructure" / "Dockerfile.md"
    ).read_text(encoding="utf-8")


def test_wiki_sync_skill_exposes_incremental_infrastructure_contract() -> None:
    skill_root = skills.BUNDLED_SKILLS_ROOT / "wiki-sync"
    text = "\n".join(
        (skill_root / name).read_text(encoding="utf-8")
        for name in ("SKILL.md", "reference.md")
    )
    normalized = " ".join(text.split())
    for expected in (
        "Docker, Compose, Kubernetes, GitHub Actions",
        "infrastructure add/change/move/remove counts",
        "discovery roots",
        "unsupported YAML",
        "generation_inputs.infrastructure",
        "source-content hash",
        "observation hash",
        "`## Notes` is the sole semantic section",
        "unsupported custom headings",
        "Page writes are atomic",
    ):
        assert expected in normalized
