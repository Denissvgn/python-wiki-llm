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
    with_infrastructure_deselection_generation_input,
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
from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION
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
        "database:\n  host: localhost\n",
        encoding="utf-8",
    )


def _manifest(wiki: Path) -> dict:
    from llm_wiki_cli.services.sync_manifest import SyncManifest
    return SyncManifest.load(wiki).to_payload()


def _json_artifact(wiki: Path, filename: str) -> dict:
    if filename == ".llm-wiki-knowledge.json":
        from llm_wiki_cli.services.knowledge_model import knowledge_index_to_payload
        knowledge = load_knowledge_state(wiki).knowledge
        assert knowledge is not None
        return knowledge_index_to_payload(knowledge)
    return json.loads((wiki / filename).read_text(encoding="utf-8"))


def _wiki_bytes(wiki: Path) -> dict[str, bytes]:
    return {
        path.relative_to(wiki).as_posix(): path.read_bytes()
        for path in sorted(wiki.rglob("*"))
        if path.is_file()
    }


def test_extended_yaml_pages_preserve_notes_selection_and_live_basis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("def main():\n    return 1\n")
    cases = {
        "action.yml": "name: Pilot\ninputs: {token: {default: NEVER_COPY}}\nruns: {using: composite, steps: [{name: Build, run: echo NEVER_COPY, shell: bash}]}\n",
        ".gitlab-ci.yml": "stages: [build]\ncompile: {script: echo NEVER_COPY}\n",
        ".circleci/config.yml": "version: 2.1\njobs: {build: {steps: [checkout]}}\nworkflows: {ci: {jobs: [build]}}\n",
        "azure-pipelines.yml": "trigger: [main]\njobs: [{job: Build, steps: [{script: echo NEVER_COPY}]}]\n",
        "kustomization.yaml": "apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\nresources: [deployment.yaml]\n",
        "overlay/Kustomization": "resources: [../deployment.yaml]\n",
        "Chart.yaml": "apiVersion: v2\nname: pilot\nversion: 1.0.0\n",
        "playbook.yml": "- name: Deploy\n  hosts: web\n  tasks: [{name: Copy, copy: {content: NEVER_COPY, dest: /tmp/file}}]\n",
    }
    for path, text in cases.items():
        target = project / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    (project / "excluded.yaml").write_text("kind: Service\napiVersion: v1\n")
    selection = project / "selection.json"
    selection.write_text(json.dumps({
        "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
        "include": ["app.py", *cases], "exclude": [],
    }))
    wiki = project / "wiki"
    monkeypatch.chdir(project)
    bootstrap_cmd.run(_bootstrap_args(project, wiki, source_selection="selection.json"))
    state = _manifest(wiki)["generation_inputs"]["infrastructure"]
    assert set(state["sources"]) == set(cases)
    assert state["discovery"]["unsupported_yaml"] == []
    page = wiki / state["sources"]["action.yml"]["page_path"]
    before = page.read_text()
    assert "github_action" in before and "Build" in before
    assert "NEVER_COPY" not in "\n".join(p.read_text() for p in (wiki / "infrastructure").glob("*.md"))
    page.write_text(before.replace("_Add reviewed operational context here; generated sections are replaced from source observations._", "Retain this operational decision."))
    sync_cmd.run(_sync_args(project, wiki, source_selection="selection.json", no_plugins=True))
    old_hash = state["sources"]["action.yml"]["source_content_hash"]
    (project / "action.yml").write_text(cases["action.yml"].replace("Build", "Publish"))
    stale = lint_cmd.build_report(str(wiki), str(project), strict=True, source_selection="selection.json", knowledge_drift_report=True)
    assert any(item.category == "knowledge_freshness" and "source-changed" in item.message for item in stale.diagnostics)
    sync_cmd.run(_sync_args(project, wiki, source_selection="selection.json", no_plugins=True))
    after = page.read_text()
    assert "Publish" in after and "Retain this operational decision." in after
    current = _manifest(wiki)["generation_inputs"]["infrastructure"]
    assert current["sources"]["action.yml"]["source_content_hash"] != old_hash
    report = lint_cmd.build_report(str(wiki), str(project), strict=True, source_selection="selection.json", knowledge_drift_report=True)
    assert not any(item.category == "knowledge_freshness" and "source-changed" in item.message for item in report.diagnostics)


def test_yaml_qualifications_are_visible_without_renderer_failures(tmp_path: Path) -> None:
    from llm_wiki_cli.services.bootstrap_runtime import _generate_infrastructure_md
    from llm_wiki_cli.services.extraction_service import _parse_compose
    from llm_wiki_cli.services.infrastructure_inventory import parse_github_actions_workflow

    malformed = _parse_compose("services: {web: {image: nginx, build: [broken]}}")
    assert malformed["services"] == {} and malformed["advisories"]
    assert "## Advisories" in _generate_infrastructure_md("compose.yml", malformed)
    workflow = parse_github_actions_workflow(
        "name: |\n  CI\n  <script>bad</script>\non: push\njobs:\n  check:\n    steps:\n      - name: |\n          <b>label</b>\n        run: |\n          echo ok\n          # Injected heading\n"
    )
    rendered = _generate_infrastructure_md(".github/workflows/ci.yml", workflow)
    assert "\n# Injected heading" not in rendered
    assert "\n<script>" not in rendered and "- <b>" not in rendered
    assert "echo ok # Injected heading" in rendered
    (tmp_path / "infra.yaml").write_text("apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\nmetadata: {name: overlay}\nresources: [service.yaml]\n")
    (tmp_path / "generic.yaml").write_text("apiVersion: 1\nkind: Custom\nmetadata: {name: example}\n")
    (tmp_path / "broken.yaml").write_text("key: [\n")
    snapshot = build_source_snapshot(tmp_path)
    inventory = get_yaml_infrastructure_inventory(tmp_path, source_snapshot=snapshot)
    assert inventory == {}
    plan = build_infrastructure_sync_plan(snapshot, inventory)
    invalid = next(item for item in plan.unsupported_yaml if item["path"] == "broken.yaml")
    assert invalid["reason"] == "invalid-yaml" and invalid["advisories"]


@pytest.mark.parametrize(
    "filename,text",
    [
        ("compose.yml", "services:\n  api:\n    image: nginx\n    command: |\n      echo first\n      # Injected\n"),
        ("prometheus.yml", "scrape_configs:\n  - job_name: |\n      api\n      # Injected\n"),
        ("service.yaml", 'apiVersion: v1\nkind: Service\nmetadata: {name: "api\\n# Injected"}\n'),
    ],
)
def test_yaml_multiline_values_remain_inert_in_pages_and_index(tmp_path, filename, text):
    from llm_wiki_cli.services.bootstrap_runtime import _append_index_infrastructure, _generate_infrastructure_md
    from llm_wiki_cli.services.infrastructure_inventory import infrastructure_display_label

    (tmp_path / filename).write_text(text)
    snapshot = build_source_snapshot(tmp_path)
    inventory = {
        **get_docker_inventory(tmp_path, source_snapshot=snapshot),
        **get_yaml_infrastructure_inventory(tmp_path, source_snapshot=snapshot),
    }
    info = inventory[filename]
    page = _generate_infrastructure_md(filename, info)
    assert "\n# Injected" not in page
    lines: list[str] = []
    _append_index_infrastructure(lines, [{"name": "example", "label": infrastructure_display_label(filename, info), "type": info["type"]}])
    assert "\n# Injected" not in "\n".join(lines)


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
        "database:\n  host: localhost\n",
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
    assert not any(
        finding.category == "knowledge_freshness"
        for finding in (*changed.issues, *changed.diagnostics)
    )
    changed_report = lint_cmd.build_report(
        str(wiki),
        str(project),
        strict=True,
        knowledge_drift_report=True,
    )
    changed_messages = [
        diagnostic.message
        for diagnostic in changed_report.diagnostics
        if diagnostic.category == "knowledge_freshness"
        and diagnostic.path == "infrastructure/Dockerfile.md"
    ]
    assert any("source-changed" in message for message in changed_messages)

    dockerfile.unlink()
    removed = lint_cmd.build_report(
        str(wiki),
        str(project),
        strict=True,
    )
    assert not any(
        finding.category == "knowledge_freshness"
        for finding in (*removed.issues, *removed.diagnostics)
    )
    removed_report = lint_cmd.build_report(
        str(wiki),
        str(project),
        strict=True,
        knowledge_drift_report=True,
    )
    removed_messages = [
        diagnostic.message
        for diagnostic in removed_report.diagnostics
        if diagnostic.category == "knowledge_freshness"
        and diagnostic.path == "infrastructure/Dockerfile.md"
    ]
    assert any("source-missing" in message for message in removed_messages)


def test_first_use_bootstrap_rejects_changed_existing_infrastructure_wiki(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
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
    before_tree = _wiki_bytes(wiki)
    capsys.readouterr()

    with pytest.raises(SystemExit) as exc_info:
        bootstrap_cmd.run(_bootstrap_args(project, wiki))

    assert exc_info.value.code == 2
    assert _wiki_bytes(wiki) == before_tree
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "llm-wiki sync --jobs 1" in captured.err
    after_state = _manifest(wiki)["generation_inputs"]["infrastructure"]
    assert after_state == before_state
    assert after_state["sources"]["Dockerfile"]["source_content_hash"] == before_hash
    assert "python:3.12" in (
        wiki / "infrastructure" / "Dockerfile.md"
    ).read_text(encoding="utf-8")
    report = lint_cmd.build_report(
        str(wiki),
        str(project),
        strict=True,
        knowledge_drift_report=True,
    )
    messages = [
        diagnostic.message
        for diagnostic in report.diagnostics
        if diagnostic.category == "knowledge_freshness"
        and diagnostic.path == "infrastructure/Dockerfile.md"
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
        "database:\n  host: localhost\n",
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
    assert supported_plan.deselected_records == {}
    assert not supported_plan.has_deselection_changes
    assert supported_plan.next_state == generation_inputs["infrastructure"]
    assert with_infrastructure_deselection_generation_input(
        generation_inputs,
        supported_plan,
    ) == generation_inputs


def test_infrastructure_plan_prunes_deselected_state_without_tombstones(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    selected = project / "selected"
    excluded = project / "excluded"
    selected.mkdir(parents=True)
    excluded.mkdir()
    (selected / "compose.yml").write_text(
        "services:\n  api:\n    image: nginx\n",
        encoding="utf-8",
    )
    (excluded / "Dockerfile").write_text("FROM alpine\n", encoding="utf-8")
    broad_snapshot = build_source_snapshot(project)
    broad_inventory = get_docker_inventory(
        project,
        source_snapshot=broad_snapshot,
    )
    broad_plan = build_infrastructure_sync_plan(broad_snapshot, broad_inventory)
    generation_inputs = with_infrastructure_generation_input({}, broad_plan)
    profile = project / ".llm-wiki" / "source-selection.json"
    profile.parent.mkdir()
    profile.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["selected"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )

    selected_snapshot = build_source_snapshot(project)
    selected_inventory = get_docker_inventory(
        project,
        source_snapshot=selected_snapshot,
    )
    plan = build_infrastructure_sync_plan(
        selected_snapshot,
        selected_inventory,
        generation_inputs=generation_inputs,
    )

    assert set(plan.current_sources) == {"selected/compose.yml"}
    assert set(plan.deselected_records) == {"excluded/Dockerfile"}
    assert plan.removed_sources == ()
    assert isinstance(plan.next_state["sources"], dict)
    assert set(plan.next_state["sources"]) == {"selected/compose.yml"}
    assert plan.next_state["tombstones"] == {}
    assert plan.has_deselection_changes
    assert isinstance(plan.deselection_only_state["sources"], dict)
    assert set(plan.deselection_only_state["sources"]) == {
        "selected/compose.yml"
    }
    assert plan.deselection_only_state["tombstones"] == {}
    deselection_inputs = with_infrastructure_deselection_generation_input(
        generation_inputs,
        plan,
    )
    assert deselection_inputs["infrastructure"] == plan.deselection_only_state
    assert plan.deselected_page_paths == (
        broad_plan.current_sources["excluded/Dockerfile"]["page_path"],
    )
    assert plan.has_changes


def test_deselection_only_state_does_not_advance_selected_source_changes(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    selected = project / "selected"
    excluded = project / "excluded"
    selected.mkdir(parents=True)
    excluded.mkdir()
    selected_source = selected / "Dockerfile"
    selected_source.write_text("FROM alpine:3.20\n", encoding="utf-8")
    (excluded / "Dockerfile").write_text("FROM busybox\n", encoding="utf-8")
    broad_snapshot = build_source_snapshot(project)
    broad_inventory = get_docker_inventory(
        project,
        source_snapshot=broad_snapshot,
    )
    broad_plan = build_infrastructure_sync_plan(broad_snapshot, broad_inventory)
    generation_inputs = with_infrastructure_generation_input({}, broad_plan)
    selected_source.write_text("FROM alpine:3.21\n", encoding="utf-8")
    profile = project / ".llm-wiki" / "source-selection.json"
    profile.parent.mkdir()
    profile.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["selected"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )
    snapshot = build_source_snapshot(project)
    inventory = get_docker_inventory(project, source_snapshot=snapshot)

    plan = build_infrastructure_sync_plan(
        snapshot,
        inventory,
        generation_inputs=generation_inputs,
    )

    prior_record = broad_plan.current_sources["selected/Dockerfile"]
    assert plan.current_sources["selected/Dockerfile"] != prior_record
    assert isinstance(plan.next_state["sources"], dict)
    assert plan.next_state["sources"]["selected/Dockerfile"] != prior_record
    assert isinstance(plan.deselection_only_state["sources"], dict)
    assert (
        plan.deselection_only_state["sources"]["selected/Dockerfile"]
        == prior_record
    )
    assert set(plan.deselection_only_state["sources"]) == {
        "selected/Dockerfile"
    }
    assert plan.deselection_only_state["tombstones"] == {}


def test_deselected_page_remains_when_a_current_source_owns_it(tmp_path: Path) -> None:
    project = tmp_path / "project"
    selected = project / "selected"
    excluded = project / "excluded"
    selected.mkdir(parents=True)
    excluded.mkdir()
    (selected / "Dockerfile").write_text("FROM alpine\n", encoding="utf-8")
    (excluded / "compose.yml").write_text(
        "services:\n  api:\n    image: nginx\n",
        encoding="utf-8",
    )
    broad_snapshot = build_source_snapshot(project)
    broad_inventory = get_docker_inventory(
        project,
        source_snapshot=broad_snapshot,
    )
    broad_plan = build_infrastructure_sync_plan(broad_snapshot, broad_inventory)
    generation_inputs = with_infrastructure_generation_input({}, broad_plan)
    shared_page = broad_plan.current_sources["selected/Dockerfile"]["page_path"]
    assert isinstance(generation_inputs["infrastructure"], dict)
    generation_inputs["infrastructure"]["sources"]["excluded/compose.yml"][
        "page_path"
    ] = shared_page
    profile = project / ".llm-wiki" / "source-selection.json"
    profile.parent.mkdir()
    profile.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["selected"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )
    snapshot = build_source_snapshot(project)
    inventory = get_docker_inventory(project, source_snapshot=snapshot)

    plan = build_infrastructure_sync_plan(
        snapshot,
        inventory,
        generation_inputs=generation_inputs,
    )

    assert set(plan.deselected_records) == {"excluded/compose.yml"}
    assert plan.deselected_page_paths == ()


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
    manifest = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    topic = (
        skills.BUNDLED_SKILLS_ROOT
        / skills.REFERENCE_SKILL_ID
        / "references/extractors-dependencies.md"
    ).read_text(encoding="utf-8")
    surfaces = (
        skills.BUNDLED_SKILLS_ROOT
        / skills.REFERENCE_SKILL_ID
        / "references/surfaces-naming.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(f"{topic}\n{surfaces}".split())

    assert skills.SKILL_DEPENDENCIES["wiki-sync"] == (
        skills.REFERENCE_SKILL_ID,
    )
    for root in (".claude/skills", ".llm-wiki/skills"):
        assert (
            f"{root}/wiki-reference/references/extractors-dependencies.md"
            in manifest
        )
    for expected in (
        "Docker, Compose, Kubernetes, GitHub Actions",
        "infrastructure add/change/move/remove counts",
        "discovery roots",
        "unsupported YAML",
        "generation_inputs.infrastructure",
        "source-content hash",
        "observation hash",
        "`## Notes` is the only supported semantic section",
        "unsupported custom headings",
        "Page writes are atomic",
    ):
        assert expected in normalized
