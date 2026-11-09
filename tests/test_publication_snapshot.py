"""Publication commitments cover native pages without bounded query loss."""

from dataclasses import replace
from datetime import date
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import publication_snapshot as snapshot
from llm_wiki_cli.services.knowledge_artifacts import (
    build_knowledge_commit_plan,
    commit_knowledge_artifacts,
)
from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.knowledge_generation import build_knowledge_generation_plan
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from tests.test_knowledge_generation import _planner_inputs
from tests.test_knowledge_loader import _write_fixture_pages
from tests.test_snapshot_query_validation import STORAGE_FORMATS, _committed_snapshot
from tests.knowledge_fixtures import one_module_two_entities_fixture


@pytest.mark.parametrize("storage_format", STORAGE_FORMATS)
def test_complete_deterministic_native_snapshot_is_read_only(tmp_path, storage_format):
    _committed_snapshot(tmp_path, storage_format, governed=True)
    before = {
        p.relative_to(tmp_path): p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file()
    }
    result = snapshot.build_publication_snapshot(tmp_path)
    assert result == snapshot.build_publication_snapshot(tmp_path)
    assert result["complete"] is True
    assert result["freshness"] == {"scope": "snapshot-only", "state": "not-evaluated"}
    expected = load_knowledge_state(tmp_path).knowledge
    assert expected is not None
    assert {p["canonical_path"] for p in result["pages"]} == {
        c.document.canonical_path for c in expected.concepts
    }
    assert result["coverage"]["page_count"] == len(expected.concepts)
    assert all(p["uid"] for p in result["pages"])
    module = next(p for p in result["pages"] if p["kind"] == "modules")
    assert module["source_basis"]["source_path"] == "src/accounts.py"
    assert module["sections"] and module["sections"][0]["exact_hash"]
    assert str(tmp_path) not in json.dumps(result)
    assert before == {
        p.relative_to(tmp_path): p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file()
    }


def test_current_packed_indexed_snapshot_retains_full_native_page_set(
    tmp_path, monkeypatch
):
    from llm_wiki_cli.services import bootstrap_runtime

    monkeypatch.chdir(tmp_path)
    clock = Mock()
    clock.today.return_value = date(2020, 1, 2)
    monkeypatch.setattr(bootstrap_runtime, "date", clock)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("class Application:\n    pass\n")
    api.bootstrap_wiki("src", "wiki")
    history = (tmp_path / "wiki/log.md").read_text(encoding="utf-8")
    assert "## 2020-01-02" in history and "- Source: `src`" in history
    result = snapshot.build_publication_snapshot("wiki")
    assert result["commitments"]["manifest_storage_version"] == 8
    assert result["complete"] is True
    assert any(
        p["canonical_path"] == "entities/Application.md" for p in result["pages"]
    )
    assert any(
        section.get("semantic_hash")
        for page in result["pages"]
        for section in page["sections"]
    )
    assert any(
        section.get("structural_hash")
        for page in result["pages"]
        for section in page["sections"]
    )


@pytest.mark.parametrize("storage_format", ["v1", "packed-v4-deflate"])
def test_global_native_ownership_and_preamble_are_available_for_facet_dependencies(
    tmp_path, storage_format
):
    fixture = one_module_two_entities_fixture()
    preamble = "Préface with native evidence.\n\n"
    fixture = replace(
        fixture,
        pages=tuple(
            replace(
                page,
                content=preamble
                + page.content
                + (
                    "\n## Description\nMaintained context.\n\n## Imports\nGenerated imports.\n"
                    if page.page_kind == "modules"
                    else ""
                ),
            )
            if page.page_kind in {"modules", "log"}
            else page
            for page in fixture.pages
        ),
    )
    _write_fixture_pages(tmp_path, fixture)
    plan = build_knowledge_generation_plan(_planner_inputs(tmp_path, fixture))
    commit_knowledge_artifacts(plan)
    if storage_format != "v1":
        commit_knowledge_artifacts(
            build_knowledge_commit_plan(
                tmp_path,
                surface_index_bytes=plan.surface_index.content,
                knowledge_index_bytes=plan.knowledge_index.content,
                manifest=plan.committed_manifest.without_artifact_hashes(),
                knowledge_format=storage_format,
            )
        )
    result = snapshot.build_publication_snapshot(tmp_path)
    module = next(page for page in result["pages"] if page["kind"] == "modules")
    sections = {section["title"]: section for section in module["sections"]}
    assert sections["Description"]["ownership"] == "semantic"
    assert (
        sections["Description"]["semantic_hash"]
        == sections["Description"]["exact_hash"]
    )
    assert "structural_hash" not in sections["Description"]
    assert sections["Imports"]["ownership"] == "generated"
    assert sections["Imports"]["structural_hash"] == sections["Imports"]["exact_hash"]
    assert "semantic_hash" not in sections["Imports"]
    assert module["preamble"] == {
        "locator": module["locator"] + "#section/@preamble",
        "page_locator": module["locator"],
        "exact_hash": sha256_bytes(preamble.encode("utf-8")),
        "ownership": "unknown",
    }
    log = next(page for page in result["pages"] if page["kind"] == "log")
    assert log["preamble"]["ownership"] == "generated"
    assert log["preamble"]["structural_hash"] == log["preamble"]["exact_hash"]
    assert "semantic_hash" not in log["preamble"]
    assert all(
        "preamble" not in page for page in result["pages"] if page not in (module, log)
    )


def test_raw_hash_distinguishes_newlines_without_changing_native_hash(tmp_path):
    _committed_snapshot(tmp_path, "packed-v4-deflate")
    before = snapshot.build_publication_snapshot(tmp_path)
    page = tmp_path / "entities" / "User.md"
    page.write_bytes(page.read_bytes().replace(b"\n", b"\r\n"))
    after = snapshot.build_publication_snapshot(tmp_path)
    left = next(p for p in before["pages"] if p["canonical_path"] == "entities/User.md")
    right = next(
        p for p in after["pages"] if p["canonical_path"] == left["canonical_path"]
    )
    assert left["normalized_hash"] == right["normalized_hash"]
    assert left["raw_hash"] != right["raw_hash"] == sha256_bytes(page.read_bytes())
    assert before["snapshot_id"] != after["snapshot_id"]


def test_producer_identity_changes_even_when_page_and_option_hashes_are_unchanged(
    tmp_path,
):
    plan = _committed_snapshot(tmp_path, "packed-v4-deflate")
    before = snapshot.build_publication_snapshot(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    knowledge = loaded.knowledge
    assert knowledge is not None and loaded.manifest_basis is not None
    changed = replace(
        knowledge,
        bundle=replace(
            knowledge.bundle,
            producer=replace(
                knowledge.bundle.producer,
                tool=replace(knowledge.bundle.producer.tool, version="999.0.0"),
            ),
        ),
    )
    commit_knowledge_artifacts(
        build_knowledge_commit_plan(
            tmp_path,
            surface_index_bytes=plan.surface_index.content,
            knowledge_index=changed,
            manifest=loaded.manifest_basis.without_artifact_hashes(),
            knowledge_format="packed-v4-deflate",
        )
    )
    after = snapshot.build_publication_snapshot(tmp_path)
    assert before["pages"] == after["pages"]
    assert (
        before["commitments"]["generation_options_hash"]
        == after["commitments"]["generation_options_hash"]
    )
    assert (
        before["commitments"]["producer_hash"] != after["commitments"]["producer_hash"]
    )


def test_sections_are_not_truncated_at_query_limits(tmp_path):
    fixture = one_module_two_entities_fixture()
    pages = tuple(
        replace(
            p,
            content=p.content
            + "\n"
            + "\n".join(f"## Repeated\nBody {i}\n" for i in range(140)),
        )
        if p.canonical_path == "modules/accounts.md"
        else p
        for p in fixture.pages
    )
    fixture = replace(fixture, pages=pages)
    _write_fixture_pages(tmp_path, fixture)
    commit_knowledge_artifacts(
        build_knowledge_generation_plan(_planner_inputs(tmp_path, fixture))
    )
    result = snapshot.build_publication_snapshot(tmp_path)
    guide = next(
        p for p in result["pages"] if p["canonical_path"] == "modules/accounts.md"
    )
    repeated = [s for s in guide["sections"] if s["title"] == "Repeated"]
    assert len(repeated) == 140
    assert repeated[-1]["sibling_occurrence"] == 140
    assert len({s["locator"] for s in repeated}) == 140


@pytest.mark.parametrize("damage", ["missing", "page", "object", "symlink"])
def test_incomplete_mixed_or_unsafe_inputs_fail_closed(tmp_path, damage):
    _committed_snapshot(tmp_path, "packed-v4-deflate")
    if damage == "missing":
        (tmp_path / ".llm-wiki-knowledge.json").unlink()
    elif damage == "object":
        next(tmp_path.rglob("*.zip")).write_bytes(b"corrupt")
    else:
        page = tmp_path / "entities" / "User.md"
        if damage == "page":
            page.write_text("# Uncommitted prose\n")
        else:
            page.unlink()
            page.symlink_to(tmp_path / "entities" / "Invoice.md")
    with pytest.raises(snapshot.PublicationSnapshotError):
        snapshot.build_publication_snapshot(tmp_path)


@pytest.mark.parametrize("change", ["page", "inventory", "governance"])
def test_mutation_during_capture_cannot_be_reported_complete(
    tmp_path, monkeypatch, change
):
    _committed_snapshot(tmp_path, "packed-v4-deflate")
    original = snapshot.parse_markdown_document
    changed = False

    def mutate(*args):
        nonlocal changed
        parsed = original(*args)
        if changed:
            return parsed
        changed = True
        if change == "page":
            (tmp_path / "entities" / "User.md").write_text("# Changed\n")
        elif change == "inventory":
            (tmp_path / "guides" / "new.md").write_text("# New\n")
        else:
            (tmp_path / ".llm-wiki-governance.json").write_text("{}\n")
        return parsed

    monkeypatch.setattr(snapshot, "parse_markdown_document", mutate)
    with pytest.raises(snapshot.PublicationSnapshotError):
        snapshot.build_publication_snapshot(tmp_path)


def test_source_bootstrap_is_isolated_repeatable_and_selection_owned(
    tmp_path, monkeypatch
):
    from llm_wiki_cli.services import extractor_helpers

    source = tmp_path / "source"
    (source / "selected").mkdir(parents=True)
    (source / "selected" / "app.py").write_text("class Application:\n    pass\n")
    (source / "excluded.go").write_text("package excluded\n")
    (source / "AGENTS.md").write_text("Preserve agent instructions.\n")
    policy = source / ".llm-wiki" / "source-selection.json"
    policy.parent.mkdir()
    policy.write_text(
        json.dumps(
            {
                "schema_version": "llm-wiki-source-selection/v1",
                "include": ["selected"],
                "exclude": [],
            }
        )
    )
    before = {
        p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()
    }
    current_directory = Path.cwd()
    temporary_roots = []
    original_temporary = snapshot.TemporaryDirectory

    def temporary(**kwargs):
        directory = original_temporary(**kwargs)
        temporary_roots.append(Path(directory.name))
        return directory

    monkeypatch.setattr(snapshot, "TemporaryDirectory", temporary)
    monkeypatch.setattr(
        extractor_helpers,
        "prepare_helper",
        lambda *a, **k: pytest.fail("must not prepare helpers"),
    )
    first = snapshot.build_bootstrap_publication_snapshot(source)
    second = snapshot.build_bootstrap_publication_snapshot(source)
    assert first == second
    assert all(not root.exists() for root in temporary_roots)
    assert all(str(root) not in json.dumps(first) for root in temporary_roots)
    assert Path.cwd() == current_directory
    assert before == {
        p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()
    }
    assert any(p["canonical_path"] == "entities/Application.md" for p in first["pages"])
    assert {
        p["source_mapping"]["source_path"]
        for p in first["pages"]
        if p["source_mapping"]
    } == {"selected/app.py"}


def test_source_bootstrap_failure_cleans_partial_output_and_keeps_strict_helper_policy(
    tmp_path, monkeypatch
):
    from llm_wiki_cli.services import bootstrap_runtime
    from llm_wiki_cli.services.bootstrap_service import BootstrapExtractionError
    from llm_wiki_cli.services.helper_runtime import current_helper_operation

    source = tmp_path / "source"
    source.mkdir()
    output_roots = []

    def fail(request, *, publication_snapshot):
        assert publication_snapshot
        assert request.source_adapter is True and request.trust_source_plugins is False
        operation = current_helper_operation()
        assert operation is not None and operation.policy == "never"
        request.wiki_root.mkdir()
        (request.wiki_root / "partial.md").write_text("# Partial\n")
        output_roots.append(request.wiki_root.parent)
        raise BootstrapExtractionError("Prepared helper unavailable")

    monkeypatch.setattr(bootstrap_runtime, "execute_bootstrap", fail)
    with pytest.raises(snapshot.PublicationSnapshotError) as error:
        snapshot.build_bootstrap_publication_snapshot(source)
    assert error.value.code == "publication-bootstrap-failed"
    assert isinstance(error.value.__cause__, BootstrapExtractionError)
    assert not any(source.iterdir())
    assert all(not root.exists() for root in output_roots)
