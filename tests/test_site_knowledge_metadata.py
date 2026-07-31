"""Focused coverage for opt-in static-site knowledge metadata."""

from __future__ import annotations

import hashlib
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import site_cmd
from llm_wiki_cli.services import site_export
from llm_wiki_cli.services.knowledge_model import KnowledgeProjectionProfile
from llm_wiki_cli.services.knowledge_projection import KnowledgeProjection
from llm_wiki_cli.services.site_export import (
    SiteExportError,
    SiteExportReport,
    check_site_hub,
    check_site_mirror,
    export_site_hub,
    export_site_mirror,
)
from llm_wiki_cli.services.wiki_surface import collect_wiki_pages


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _wiki(root: Path, name: str = "wiki") -> Path:
    wiki = root / name
    _write(wiki / "index.md", "# Index\n\n[Service](modules/service.md)\n")
    _write(wiki / "log.md", "# Log\n\n")
    _write(wiki / "modules" / "service.md", "# Service\n\n")
    return wiki


def _projection(
    wiki: Path,
    *,
    bundle_id: str = "kb_site",
    freshness_evaluated: bool = False,
) -> KnowledgeProjection:
    concepts = {}
    for page in collect_wiki_pages(wiki):
        uid = (
            "lw:doc:"
            + hashlib.sha256(page.relative_path.encode("utf-8")).hexdigest()[:32]
        )
        concepts[page.relative_path] = {
            "canonical_path": page.relative_path,
            "title": page.label,
            "concept_kind": "unknown",
            "identity": {
                "state": "tracked",
                "bundle_id": bundle_id,
                "uid": uid,
                "namespaced_uid": f"{bundle_id}#{uid}",
            },
            "lifecycle": {
                "state": "active",
                "successor_uid": "unknown",
                "successor_namespaced_uid": "unknown",
            },
            "evidence": {
                "state": "present",
                "reason": "structural-evidence-present",
                "origin": "extracted",
            },
            "freshness": {
                "state": "unknown" if freshness_evaluated else "not-evaluated",
                "reason": (
                    "live-evaluation-not-performed"
                    if freshness_evaluated
                    else "not-evaluated"
                ),
                "evaluated": freshness_evaluated,
                "live_comparison_performed": False,
            },
            "review": {
                "scope": "section",
                "state": "untracked",
                "total": 0,
                "returned": 0,
                "valid_returned": 0,
                "expired_returned": 0,
                "reasons": [],
                "items": [],
                "truncated": False,
            },
            "semantic_verification": "untracked",
            "machine_check": {
                "state": "not-run",
                "reason": "verification-receipt-not-present",
                "availability": "absent",
            },
            "relationships": {
                "availability": "absent",
                "total": 0,
                "returned": 0,
                "limit": 20,
                "truncated": False,
                "items": [],
            },
        }
    return KnowledgeProjection(
        schema_version="llm-wiki-knowledge-projection/v1",
        profile=KnowledgeProjectionProfile.PUBLIC_PORTABLE,
        source_knowledge_hash="sha256:" + "a" * 64,
        bundle={
            "bundle_id": bundle_id,
            "repository_identity": "unknown",
            "repository_identity_source": "unknown",
            "evaluated_revision": "unknown",
            "working_tree": "unknown",
        },
        concepts=concepts,
        warnings=(),
        omitted_fields={},
        freshness=(
            f"evaluated ({len(concepts)} concepts)"
            if freshness_evaluated
            else None
        ),
    )


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _projection_from_payload(payload: dict[str, object]) -> KnowledgeProjection:
    return KnowledgeProjection(
        schema_version=payload["schema_version"],
        profile=KnowledgeProjectionProfile(payload["profile"]),
        source_knowledge_hash=payload["source_knowledge_hash"],
        bundle=payload["bundle"],
        concepts=payload["concepts"],
        warnings=tuple(payload["warnings"]),
        omitted_fields=payload["omitted_fields"],
        freshness=payload.get("freshness"),
    )


def _replace_nested_scalar(path: Path, key: str, value: str) -> None:
    content = path.read_text(encoding="utf-8")
    prefix = f"  {key}: "
    lines = [
        f'{prefix}"{value}"' if line.startswith(prefix) else line
        for line in content.splitlines()
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def test_disabled_export_is_byte_identical_and_command_does_not_load_knowledge(
    tmp_path, monkeypatch
):
    wiki = _wiki(tmp_path)
    baseline = tmp_path / "baseline"
    explicit_disabled = tmp_path / "explicit-disabled"

    baseline_report = export_site_mirror(
        wiki_dir=wiki,
        out_dir=baseline,
        format="mkdocs",
    )
    explicit_report = export_site_mirror(
        wiki_dir=wiki,
        out_dir=explicit_disabled,
        format="mkdocs",
        knowledge_metadata=None,
        knowledge_projection=None,
    )
    assert _tree(explicit_disabled) == _tree(baseline)
    for report in (baseline_report, explicit_report):
        assert report.freshness is None
        assert "freshness" not in report.to_dict()
        assert "Freshness:" not in site_export.render_report_text(
            report,
            action="export",
        )

    def unexpected_load(*args, **kwargs):
        raise AssertionError("disabled site export loaded knowledge")

    monkeypatch.setattr(site_cmd, "load_knowledge_read_view", unexpected_load)
    monkeypatch.chdir(tmp_path)
    site_cmd.run(
        types.SimpleNamespace(
            site_action="export",
            wiki_dir="wiki",
            wiki_root=None,
            wiki=None,
            out_dir="command",
            format="plain",
            file_friendly=False,
            profile="reference",
            site_name=None,
            front_matter=False,
            dry_run=False,
            output_format="json",
            knowledge_metadata=None,
        )
    )


def test_command_loads_one_snapshot_projection_with_public_profile(
    tmp_path, monkeypatch
):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    sentinel_view = object()
    observed: dict[str, object] = {}

    def fake_load(wiki_dir, **kwargs):
        observed["load"] = (wiki_dir, kwargs)
        return sentinel_view

    def fake_project(view, **kwargs):
        observed["project"] = (view, kwargs)
        return projection

    def fake_export(**kwargs):
        observed["export"] = kwargs
        return SiteExportReport(out_dir=str(kwargs["out_dir"]))

    monkeypatch.setattr(site_cmd, "load_knowledge_read_view", fake_load)
    monkeypatch.setattr(site_cmd, "project_knowledge", fake_project)
    monkeypatch.setattr(site_cmd, "export_site_mirror", fake_export)
    monkeypatch.chdir(tmp_path)
    site_cmd.run(
        types.SimpleNamespace(
            site_action="export",
            wiki_dir="wiki",
            wiki_root=None,
            wiki=None,
            out_dir="site",
            format="plain",
            file_friendly=False,
            profile="reference",
            site_name=None,
            front_matter=False,
            dry_run=False,
            output_format="json",
            knowledge_metadata="summary",
        )
    )

    assert observed["load"] == (
        "wiki",
        {
            "snapshot_only": True,
            "include_machine_verification": True,
        },
    )
    assert observed["project"] == (
        sentinel_view,
        {
            "profile": "public-portable",
            "public_repository_identity": None,
        },
    )
    assert observed["export"]["knowledge_projection"] is projection
    assert observed["export"]["knowledge_metadata"] == "summary"


def test_summary_export_is_deterministic_private_safe_and_projection_only(
    tmp_path, monkeypatch
):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)

    def forbidden_surface_load(*args, **kwargs):
        raise AssertionError("enriched export loaded raw surface metadata")

    monkeypatch.setattr(
        site_export,
        "_load_surface_index_sources",
        forbidden_surface_load,
    )
    first = tmp_path / "first"
    second = tmp_path / "second"
    for target in (first, second):
        report = export_site_mirror(
            wiki_dir=wiki,
            out_dir=target,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        assert report.ok is True

    assert report.freshness == "unevaluated (snapshot-only read)"
    assert report.to_dict()["freshness"] == (
        "unevaluated (snapshot-only read)"
    )
    assert (
        "Freshness: unevaluated (snapshot-only read)"
        in site_export.render_report_text(report, action="export")
    )
    assert (
        '"freshness": "unevaluated (snapshot-only read)"'
        in site_export.render_report_json(report)
    )
    checked = check_site_mirror(
        wiki_dir=wiki,
        out_dir=first,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    assert checked.freshness == "unevaluated (snapshot-only read)"
    assert _tree(first) == _tree(second)
    service = (first / "modules" / "service.md").read_text(encoding="utf-8")
    assert 'knowledge_bundle_id: "kb_site"' in service
    assert 'source_knowledge_hash: "sha256:' + "a" * 64 + '"' in service
    assert 'knowledge_evidence_reason: "structural-evidence-present"' in service
    assert '  freshness: "unevaluated (snapshot-only read)"' in service
    assert 'knowledge_freshness: "not-evaluated"' in service
    assert 'knowledge_review_items: "[]"' in service
    assert 'knowledge_machine_check_result: "not-evaluated"' in service
    assert "PRIVATE-SENTINEL" not in service
    assert "source_path:" not in service


def test_public_projection_preserves_canonical_prose_and_media_for_review(tmp_path):
    wiki = _wiki(tmp_path)
    canonical = (
        "# Service\n\n"
        "Canonical prose may contain PRIVATE-BODY-SENTINEL.\n\n"
        "![Private capture](../assets/service/private-capture.png)\n"
    )
    media = b"PRIVATE-MEDIA-SENTINEL"
    _write(wiki / "modules" / "service.md", canonical)
    media_path = wiki / "assets" / "service" / "private-capture.png"
    media_path.parent.mkdir(parents=True)
    media_path.write_bytes(media)
    projection = _projection(wiki)
    out = tmp_path / "public-site"

    report = export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    exported = (out / "modules" / "service.md").read_text(encoding="utf-8")
    front_matter = exported.split("---", 2)[1]
    assert report.ok is True
    assert "PRIVATE-BODY-SENTINEL" not in front_matter
    assert exported.endswith(canonical)
    assert (out / "assets" / "service" / "private-capture.png").read_bytes() == media


def test_user_profile_attaches_index_concept_to_generated_reference(tmp_path):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    out = tmp_path / "site"

    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        profile="user",
        site_name="Example Docs",
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    assert "knowledge_uid:" not in (out / "index.md").read_text(encoding="utf-8")
    generated = (out / "generated-reference.md").read_text(encoding="utf-8")
    expected = projection.concepts["index.md"]["identity"]["namespaced_uid"]
    assert f'knowledge_uid: "{expected}"' in generated
    assert 'canonical_path: "index.md"' in generated


def test_user_profile_checker_enforces_projection_free_human_landing(tmp_path):
    wiki = _wiki(tmp_path)
    _write(wiki / "guides" / "start.md", "# Start\n\nUse the service.\n")
    projection = _projection(wiki)
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        profile="user",
        site_name="Example Docs",
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    valid = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        profile="user",
        site_name="Example Docs",
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    assert valid.ok is True

    landing = out / "index.md"
    content = landing.read_text(encoding="utf-8")
    landing.write_text(
        content.replace(
            "---\n\n#",
            'source_path: "/Users/alice/private.py"\n'
            'knowledge_private_extension: "PRIVATE-SENTINEL"\n'
            "llm_wiki:\n"
            '  knowledge_repository_identity: "PRIVATE-SENTINEL"\n'
            "---\n\n#",
            1,
        ),
        encoding="utf-8",
    )

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        profile="user",
        site_name="Example Docs",
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    assert report.ok is False
    assert {
        issue["target"]
        for issue in report.issues
        if issue["category"] == "unexpected_knowledge_metadata"
        and issue["path"] == str(landing)
    } == {
        "knowledge_private_extension",
        "llm_wiki",
        "source_path",
    }


@pytest.mark.parametrize(
    ("bundle_id", "uid"),
    [
        ("unknown", None),
        ("kb_site", "unknown"),
    ],
)
def test_summary_export_rejects_unknown_identity_before_writes(
    tmp_path, bundle_id, uid
):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki, bundle_id=bundle_id)
    if uid is not None:
        payload = projection.to_payload()
        payload["concepts"]["index.md"]["identity"]["namespaced_uid"] = uid
        projection = _projection_from_payload(payload)
    out = tmp_path / "site"

    with pytest.raises(SiteExportError):
        export_site_mirror(
            wiki_dir=wiki,
            out_dir=out,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )

    assert not out.exists()


def test_summary_export_rejects_stale_projected_page_set_before_writes(tmp_path):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    _write(wiki / "guides" / "new.md", "# New\n\n")
    out = tmp_path / "site"

    with pytest.raises(SiteExportError, match="does not match the exported page set"):
        export_site_mirror(
            wiki_dir=wiki,
            out_dir=out,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )

    assert not out.exists()


def test_enriched_export_cannot_allow_canonical_source_overlap(tmp_path):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    before = _tree(wiki)

    with pytest.raises(SiteExportError, match="overlaps the source wiki"):
        export_site_mirror(
            wiki_dir=wiki,
            out_dir=wiki,
            allow_overwrite_source=True,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )

    assert _tree(wiki) == before


def test_checker_detects_tampered_metadata_uid_and_successor_references(tmp_path):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    index_uid = projection.concepts["index.md"]["identity"]["namespaced_uid"]
    log_uid = projection.concepts["log.md"]["identity"]["namespaced_uid"]
    service = out / "modules" / "service.md"
    log = out / "log.md"
    _replace_nested_scalar(service, "knowledge_uid", index_uid)
    _replace_nested_scalar(service, "knowledge_successor_uid", log_uid)
    _replace_nested_scalar(log, "knowledge_successor_uid", log_uid)

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    categories = {issue["category"] for issue in report.issues}
    assert "front_matter_mismatch" in categories
    assert "duplicate_knowledge_uid" in categories
    assert "duplicate_knowledge_successor_uid" in categories
    assert "self_referential_knowledge_successor" in categories


def test_checker_requires_front_matter_when_knowledge_mode_is_selected(tmp_path):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    out = tmp_path / "site"
    export_site_mirror(wiki_dir=wiki, out_dir=out)

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    assert report.ok is False
    assert any(
        issue["category"] == "missing_knowledge_metadata"
        for issue in report.issues
    )


def test_checker_rejects_enriched_export_when_knowledge_mode_is_omitted(
    tmp_path,
):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    report = check_site_mirror(wiki_dir=wiki, out_dir=out)

    assert report.ok is False
    assert any(
        issue["category"] == "unexpected_knowledge_metadata"
        and issue["target"] == "llm_wiki.knowledge_projection_schema"
        for issue in report.issues
    )


def test_checker_rejects_enriched_export_with_mismatched_projection(tmp_path):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    mismatched_projection = _projection(wiki, bundle_id="kb_other")
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=mismatched_projection,
    )

    assert report.ok is False
    assert any(
        issue["category"] == "front_matter_mismatch"
        and issue["target"] == "llm_wiki.knowledge_bundle_id"
        for issue in report.issues
    )


def test_checker_rejects_unexpected_projected_metadata(tmp_path):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    page = out / "modules" / "service.md"
    content = page.read_text(encoding="utf-8")
    page.write_text(
        content.replace(
            '  source_knowledge_hash: "sha256:',
            '  knowledge_private_extension: "PRIVATE-SENTINEL"\n'
            '  private_remote: "https://alice:secret@private.example/repo.git"\n'
            '  source_path: "/Users/alice/private.py"\n'
            '  source_knowledge_hash: "sha256:',
            1,
        ),
        encoding="utf-8",
    )

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    unexpected = [
        issue
        for issue in report.issues
        if issue["category"] == "unexpected_knowledge_metadata"
    ]
    assert {issue["target"] for issue in unexpected} == {
        "llm_wiki.knowledge_private_extension",
        "llm_wiki.private_remote",
        "llm_wiki.source_path",
    }


def test_checker_rejects_top_level_projected_metadata(tmp_path):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    page = out / "modules" / "service.md"
    content = page.read_text(encoding="utf-8")
    page.write_text(
        content.replace(
            "llm_wiki:\n",
            'source_path: "/Users/alice/private.py"\n'
            'knowledge_private_extension: "PRIVATE-SENTINEL"\n'
            'source_knowledge_private: "PRIVATE-SENTINEL"\n'
            "llm_wiki:\n",
            1,
        ),
        encoding="utf-8",
    )

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    unexpected = [
        issue
        for issue in report.issues
        if issue["category"] == "unexpected_knowledge_metadata"
    ]
    assert {issue["target"] for issue in unexpected} == {
        "knowledge_private_extension",
        "source_knowledge_private",
        "source_path",
    }


@pytest.mark.parametrize(
    ("needle", "duplicate"),
    [
        (
            '  source_knowledge_hash: "sha256:',
            '  source_knowledge_hash: "PRIVATE-SENTINEL"\n',
        ),
        (
            'title: "Service"',
            'title: "PRIVATE-SENTINEL"\n',
        ),
    ],
)
def test_checker_rejects_duplicate_front_matter_keys(
    tmp_path, needle, duplicate
):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    page = out / "modules" / "service.md"
    content = page.read_text(encoding="utf-8")
    page.write_text(
        content.replace(needle, duplicate + needle, 1),
        encoding="utf-8",
    )

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    assert report.ok is False
    assert any(
        issue["category"] == "malformed_front_matter"
        and "Duplicate front matter key" in issue["message"]
        for issue in report.issues
    )


def test_public_reexport_rejects_stale_internal_knowledge_before_writes(
    tmp_path,
):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    stale = out / "stale.md"
    _write(
        stale,
        "---\n"
        "llm_wiki:\n"
        '  knowledge_profile: "internal"\n'
        '  knowledge_repository_identity: "PRIVATE-SENTINEL"\n'
        "---\n"
        "# Stale internal projection\n",
    )
    before = _tree(out)

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    assert report.ok is False
    assert any(
        issue["category"] == "unexpected_knowledge_page"
        and issue["path"] == str(stale)
        for issue in report.issues
    )

    with pytest.raises(
        SiteExportError,
        match="unexpected Markdown with projected knowledge metadata",
    ):
        export_site_mirror(
            wiki_dir=wiki,
            out_dir=out,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )

    assert _tree(out) == before
    assert "PRIVATE-SENTINEL" in stale.read_text(encoding="utf-8")


def test_freshness_disclosure_is_reserved_projected_site_metadata(
    tmp_path,
):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    stale = out / "freshness-only.md"
    _write(
        stale,
        "---\n"
        "llm_wiki:\n"
        '  freshness: "unevaluated (snapshot-only read)"\n'
        "---\n"
        "# Stale projection disclosure\n",
    )

    checked = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    assert any(
        issue["category"] == "unexpected_knowledge_page"
        and issue["path"] == str(stale)
        for issue in checked.issues
    )
    with pytest.raises(
        SiteExportError,
        match="unexpected Markdown with projected knowledge metadata",
    ):
        export_site_mirror(
            wiki_dir=wiki,
            out_dir=out,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )


def test_checker_rejects_freshness_metadata_when_knowledge_is_disabled(
    tmp_path,
):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    page = out / "modules" / "service.md"
    page.write_text(
        "\n".join(
            line
            for line in page.read_text(encoding="utf-8").splitlines()
            if not line.startswith("  knowledge_")
            and not line.startswith("  source_knowledge_")
        )
        + "\n",
        encoding="utf-8",
    )

    checked = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata=None,
        knowledge_projection=None,
    )

    assert any(
        issue["category"] == "unexpected_knowledge_metadata"
        and issue["target"] == "llm_wiki.freshness"
        for issue in checked.issues
    )


def test_enriched_output_scan_leaves_unrelated_extra_markdown_untouched(
    tmp_path,
):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    extra = out / "notes.md"
    _write(extra, "# Unrelated handoff note\n")
    before = extra.read_bytes()

    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    assert report.ok is True
    assert extra.read_bytes() == before


def test_enriched_output_scan_fails_closed_on_unexpected_symlink(tmp_path):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    outside = tmp_path / "outside.md"
    _write(outside, "# External\n")
    stale = out / "stale.md"
    stale.symlink_to(outside)
    index_before = (out / "index.md").read_bytes()

    with pytest.raises(SiteExportError, match="symlink entry"):
        export_site_mirror(
            wiki_dir=wiki,
            out_dir=out,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    assert (out / "index.md").read_bytes() == index_before
    assert outside.read_text(encoding="utf-8") == "# External\n"
    assert any(
        issue["category"] == "unsafe_enriched_output_scan"
        for issue in report.issues
    )


def test_enriched_export_preflights_late_expected_symlink_before_writes(
    tmp_path,
):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    out = tmp_path / "site"
    _write(out / "index.md", "# Existing index\n")
    _write(out / "log.md", "# Existing log\n")
    outside = tmp_path / "outside.md"
    _write(outside, "# External target\n")
    (out / "modules").mkdir(parents=True)
    (out / "modules" / "service.md").symlink_to(outside)
    index_before = (out / "index.md").read_bytes()
    log_before = (out / "log.md").read_bytes()
    outside_before = outside.read_bytes()

    with pytest.raises(SiteExportError, match="symlink|escapes"):
        export_site_mirror(
            wiki_dir=wiki,
            out_dir=out,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )

    assert (out / "index.md").read_bytes() == index_before
    assert (out / "log.md").read_bytes() == log_before
    assert outside.read_bytes() == outside_before


def test_enriched_output_scan_bounds_unexpected_markdown_size(tmp_path):
    wiki = _wiki(tmp_path)
    projection = _projection(wiki)
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    oversized = out / "oversized.md"
    oversized.write_bytes(
        b"x" * (site_export.MAX_ENRICHED_MARKDOWN_BYTES + 1)
    )
    index_before = (out / "index.md").read_bytes()

    with pytest.raises(SiteExportError, match="exceeds the size limit"):
        export_site_mirror(
            wiki_dir=wiki,
            out_dir=out,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )

    assert (out / "index.md").read_bytes() == index_before


def test_hub_preflights_every_projection_and_cross_source_uids(tmp_path):
    root = tmp_path / "sources"
    alpha = _wiki(root, "alpha")
    beta = _wiki(root, "beta")
    out = tmp_path / "hub"

    with pytest.raises(SiteExportError, match="Duplicate hub knowledge bundle id"):
        export_site_hub(
            wikis=[alpha, beta],
            out_dir=out,
            knowledge_metadata="summary",
            knowledge_projections={
                "alpha": _projection(alpha, bundle_id="kb_shared"),
                "beta": _projection(beta, bundle_id="kb_shared"),
            },
        )

    assert not out.exists()


def test_hub_preflights_every_child_output_overlap_before_writes(tmp_path):
    first = _wiki(tmp_path, "first")
    out = tmp_path / "hub"
    overlapping = _wiki(out, "second")

    with pytest.raises(SiteExportError, match="overlaps the source wiki"):
        export_site_hub(
            wikis=[first, overlapping],
            out_dir=out,
        )

    assert not (out / "first").exists()


def test_hub_cross_preflights_each_output_against_every_source(tmp_path):
    first = _wiki(tmp_path / "outside", "first")
    _write(first / "modules" / "index.md", "# First module index\n\n")
    out = tmp_path / "hub"
    second = _wiki(out / "first", "modules")
    second_index = second / "index.md"
    before = second_index.read_bytes()

    with pytest.raises(SiteExportError, match="overlaps the source wiki"):
        export_site_hub(
            wikis=[first, second],
            out_dir=out,
        )

    assert second_index.read_bytes() == before
    assert not (out / "index.md").exists()


@pytest.mark.parametrize(
    ("source_id", "format", "file_friendly"),
    [
        ("index.md", "plain", False),
        ("mkdocs.yml", "mkdocs", False),
        ("sidebars.json", "docusaurus", False),
        (".llm-wiki-mkdocs-overrides", "mkdocs", True),
    ],
)
def test_hub_rejects_reserved_root_output_source_ids_before_writes(
    tmp_path, source_id, format, file_friendly
):
    wiki = _wiki(tmp_path / "sources", source_id)
    out = tmp_path / "hub"

    with pytest.raises(SiteExportError, match="collides with reserved output"):
        export_site_hub(
            wikis=[wiki],
            out_dir=out,
            format=format,
            file_friendly=file_friendly,
        )

    assert not out.exists()


def test_hub_reserved_source_id_check_is_format_aware(tmp_path):
    wiki = _wiki(tmp_path / "sources", "sidebars.json")
    out = tmp_path / "hub"

    report = export_site_hub(
        wikis=[wiki],
        out_dir=out,
        format="plain",
    )

    assert report.ok is True
    assert (out / "sidebars.json" / "index.md").is_file()
    assert (out / "index.md").is_file()


def test_enriched_hub_cannot_allow_cross_source_overlap(tmp_path):
    first = _wiki(tmp_path / "outside", "first")
    _write(first / "modules" / "index.md", "# First module index\n\n")
    out = tmp_path / "hub"
    second = _wiki(out / "first", "modules")
    before = _tree(second)

    with pytest.raises(SiteExportError, match="overlaps the source wiki"):
        export_site_hub(
            wikis=[first, second],
            out_dir=out,
            allow_overwrite_source=True,
            knowledge_metadata="summary",
            knowledge_projections={
                "first": _projection(first, bundle_id="kb_first"),
                "modules": _projection(second, bundle_id="kb_second"),
            },
        )

    assert _tree(second) == before
    assert not (out / "index.md").exists()


def test_enriched_hub_namespaces_front_matter_ids_by_bundle(tmp_path):
    root = tmp_path / "sources"
    alpha = _wiki(root, "alpha")
    beta = _wiki(root, "beta")
    out = tmp_path / "hub"
    projections = {
        "alpha": _projection(alpha, bundle_id="kb_alpha"),
        "beta": _projection(beta, bundle_id="kb_beta"),
    }

    report = export_site_hub(
        wikis=[alpha, beta],
        out_dir=out,
        format="docusaurus",
        knowledge_metadata="summary",
        knowledge_projections=projections,
    )
    assert report.freshness == "unevaluated (snapshot-only read)"

    assert 'id: "kb_alpha/index"' in (
        out / "alpha" / "index.md"
    ).read_text(encoding="utf-8")
    sidebar = (out / "sidebars.json").read_text(encoding="utf-8")
    assert '"kb_alpha/index"' in sidebar
    assert '"kb_beta/modules/service"' in sidebar
    checked = check_site_hub(
        wikis=[alpha, beta],
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projections=projections,
    )
    assert checked.ok is True
    assert checked.freshness == "unevaluated (snapshot-only read)"


def test_enriched_hub_sums_evaluated_freshness_across_sources(tmp_path):
    root = tmp_path / "sources"
    alpha = _wiki(root, "alpha")
    beta = _wiki(root, "beta")
    out = tmp_path / "hub"
    projections = {
        "alpha": _projection(
            alpha,
            bundle_id="kb_alpha",
            freshness_evaluated=True,
        ),
        "beta": _projection(
            beta,
            bundle_id="kb_beta",
            freshness_evaluated=True,
        ),
    }
    expected = "evaluated (6 concepts)"

    report = export_site_hub(
        wikis=[alpha, beta],
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projections=projections,
    )

    assert report.freshness == expected
    assert report.freshness_by_source == {}
    assert report.to_dict()["freshness"] == expected
    assert f"Freshness: {expected}" in site_export.render_report_text(
        report,
        action="export",
    )

    checked = check_site_hub(
        wikis=[alpha, beta],
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projections=projections,
    )
    assert checked.ok is True
    assert checked.freshness == expected
    assert checked.freshness_by_source == {}


def test_hub_retains_per_source_disclosures_for_mixed_evaluation_scope(tmp_path):
    root = tmp_path / "sources"
    alpha = _wiki(root, "alpha")
    beta = _wiki(root, "beta")
    expected = {
        "alpha": "evaluated (3 concepts)",
        "beta": "unevaluated (snapshot-only read)",
    }

    freshness, by_source = site_export._hub_report_freshness(
        {
            "alpha": _projection(
                alpha,
                bundle_id="kb_alpha",
                freshness_evaluated=True,
            ),
            "beta": _projection(beta, bundle_id="kb_beta"),
        }
    )

    assert freshness is None
    assert by_source == expected
    report = SiteExportReport(freshness_by_source=by_source)
    assert report.to_dict()["freshness_by_source"] == expected
    rendered = site_export.render_report_text(report, action="export")
    assert "Freshness by source:" in rendered
    assert "- alpha: evaluated (3 concepts)" in rendered
    assert "- beta: unevaluated (snapshot-only read)" in rendered


def test_checker_rejects_enriched_hub_when_knowledge_mode_is_omitted(tmp_path):
    root = tmp_path / "sources"
    alpha = _wiki(root, "alpha")
    beta = _wiki(root, "beta")
    out = tmp_path / "hub"
    projections = {
        "alpha": _projection(alpha, bundle_id="kb_alpha"),
        "beta": _projection(beta, bundle_id="kb_beta"),
    }
    export_site_hub(
        wikis=[alpha, beta],
        out_dir=out,
        knowledge_metadata="summary",
        knowledge_projections=projections,
    )

    report = check_site_hub(wikis=[alpha, beta], out_dir=out)

    assert report.ok is False
    assert any(
        issue["category"] == "unexpected_knowledge_metadata"
        and issue["target"] == "llm_wiki.knowledge_projection_schema"
        for issue in report.issues
    )
