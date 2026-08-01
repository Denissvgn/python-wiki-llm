"""Tests for Obsidian mirror export and companion plugin packaging."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import types
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import obsidian_cmd
from llm_wiki_cli.services import obsidian
from llm_wiki_cli.services.knowledge_model import KnowledgeProjectionProfile
from llm_wiki_cli.services.knowledge_projection import KnowledgeProjection


def _ns(**kwargs):
    return types.SimpleNamespace(**kwargs)


def _write_wiki(root: Path) -> Path:
    wiki = root / "docs" / "llm_wiki"
    for subdir in [
        "entities",
        "modules",
        "workflows",
        "guides",
        "flows",
        "infrastructure",
        "legacy",
    ]:
        (wiki / subdir).mkdir(parents=True, exist_ok=True)
    (wiki / "index.md").write_text(
        "# LLM Wiki Index\n\n- [User](entities/User.md)\n- [models](modules/models.md)\n",
        encoding="utf-8",
    )
    (wiki / "log.md").write_text("# Architectural Log\n\n", encoding="utf-8")
    (wiki / "dependencies.md").write_text(
        "# Dependencies\n\nProject dependency graph.\n",
        encoding="utf-8",
    )
    (wiki / "load-order.md").write_text(
        "# Load Order\n\nProject initialization order.\n",
        encoding="utf-8",
    )
    (wiki / "entities" / "User.md").write_text(
        "# User\n\n"
        "**Location:** `models.py:3`\n"
        "**Module:** [models](../modules/models.md)\n\n"
        "## Description\n\nA user entity.\n",
        encoding="utf-8",
    )
    (wiki / "modules" / "models.md").write_text(
        "# models Module\n\n"
        "**Path:** `models.py`\n\n"
        "## Classes\n\n| Class | Description |\n|---|---|\n| [User](../entities/User.md) | A user |\n",
        encoding="utf-8",
    )
    (wiki / "workflows" / "signup.md").write_text(
        "# Signup\n\nTouches [models](../modules/models.md).\n",
        encoding="utf-8",
    )
    (wiki / "guides" / "operator-onboarding.md").write_text(
        "# Operator Onboarding\n\nGuidance for operators.\n",
        encoding="utf-8",
    )
    (wiki / "flows" / "checkout.md").write_text(
        "# Checkout\n\nUses [models](../modules/models.md).\n",
        encoding="utf-8",
    )
    (wiki / "infrastructure" / "Dockerfile.md").write_text(
        "# Dockerfile\n\nCopies [models.py](../modules/models.md).\n",
        encoding="utf-8",
    )
    (wiki / "legacy" / "Old.md").write_text("# Old\n\n", encoding="utf-8")
    return wiki


def _knowledge_projection(
    wiki: Path,
    *,
    bundle_id: str = "bundle-1",
    unknown_uid_path: str | None = None,
) -> KnowledgeProjection:
    pages = obsidian.collect_wiki_pages(wiki)
    uid_by_path = {
        page.canonical_rel: f"lw:doc:{index:032x}"
        for index, page in enumerate(pages, start=1)
    }
    concepts: dict[str, dict[str, object]] = {}
    for page in pages:
        uid = (
            "unknown"
            if page.canonical_rel == unknown_uid_path
            else uid_by_path[page.canonical_rel]
        )
        relationships: list[dict[str, object]] = []
        if page.canonical_rel == "entities/User.md":
            relationships = [
                {
                    "kind": "calls",
                    "direction": "outgoing",
                    "origin": "extracted",
                    "resolution": "resolved",
                    "target": {
                        "kind": "concept",
                        "present": True,
                        "canonical_path": "modules/models.md",
                        "title": "models Module",
                        "concept_kind": "source-module",
                        "namespaced_uid": (
                            f"{bundle_id}#{uid_by_path['modules/models.md']}"
                        ),
                    },
                    "evidence": {
                        "state": "present",
                        "observed": 1,
                        "unique": 1,
                        "emitted": 1,
                        "omitted": 0,
                    },
                    "coverage": {
                        "observed": 1,
                        "emitted": 1,
                        "omitted": 0,
                        "limit": 20,
                        "truncated": False,
                    },
                },
                {
                    "kind": "depends_on",
                    "direction": "incoming",
                    "origin": "inferred",
                    "resolution": "unresolved",
                    "target": {
                        "kind": "unresolved",
                        "present": False,
                        "label": "Unresolved target",
                    },
                    "evidence": {
                        "state": "present",
                        "observed": 1,
                        "unique": 1,
                        "emitted": 0,
                        "omitted": 1,
                    },
                    "coverage": {
                        "observed": 1,
                        "emitted": 0,
                        "omitted": 1,
                        "limit": 20,
                        "truncated": True,
                    },
                },
            ]
        concepts[page.canonical_rel] = {
            "canonical_path": page.canonical_rel,
            "title": page.title,
            "concept_kind": "unknown",
            "identity": {
                "state": "tracked",
                "bundle_id": bundle_id,
                "uid": uid,
                "namespaced_uid": (
                    "unknown" if uid == "unknown" else f"{bundle_id}#{uid}"
                ),
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
                "state": "not-evaluated",
                "reason": "not-evaluated",
                "evaluated": False,
                "live_comparison_performed": False,
            },
            "review": {
                "scope": "section",
                "state": "has-valid-sections",
                "total": 1,
                "returned": 1,
                "valid_returned": 1,
                "expired_returned": 0,
                "truncated": False,
                "reasons": [],
                "items": [
                    {
                        "section_locator": f"{page.canonical_rel}#summary",
                        "state": "valid",
                        "reasons": [],
                    }
                ],
            },
            "semantic_verification": "untracked",
            "machine_check": {
                "state": "not-run",
                "reason": "verification-receipt-not-present",
                "availability": "absent",
            },
            "relationships": {
                "availability": "ready",
                "total": len(relationships),
                "returned": len(relationships),
                "limit": 20,
                "truncated": False,
                "items": relationships,
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
    )


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


class TestObsidianMirror:
    def test_maps_api_contracts_to_root_vault_page(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        (wiki / "api-contracts.md").write_text(
            "# API contracts\n", encoding="utf-8"
        )

        by_rel = {
            page.canonical_rel: page for page in obsidian.collect_wiki_pages(wiki)
        }

        assert by_rel["api-contracts.md"].mirror_rel == "LLM Wiki/API contracts.md"
        assert by_rel["api-contracts.md"].kind == "api-contracts"

    def test_collects_pages_and_maps_to_vault_paths(self, tmp_project):
        wiki = _write_wiki(tmp_project)

        pages = obsidian.collect_wiki_pages(wiki)
        by_rel = {page.canonical_rel: page for page in pages}

        assert by_rel["entities/User.md"].mirror_rel == "LLM Wiki/Entities/User.md"
        assert (
            by_rel["guides/operator-onboarding.md"].mirror_rel
            == "LLM Wiki/Guides/operator-onboarding.md"
        )
        assert by_rel["flows/checkout.md"].mirror_rel == "LLM Wiki/Flows/checkout.md"
        assert by_rel["dependencies.md"].mirror_rel == "LLM Wiki/Dependencies.md"
        assert by_rel["load-order.md"].mirror_rel == "LLM Wiki/Load order.md"
        assert by_rel["modules/models.md"].source_path == "models.py"
        assert by_rel["entities/User.md"].source_line == 3
        assert "legacy/Old.md" not in by_rel

    def test_frontmatter_aliases_tags_and_metadata(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        page = next(
            page
            for page in obsidian.collect_wiki_pages(wiki)
            if page.canonical_rel == "entities/User.md"
        )

        frontmatter = obsidian.build_frontmatter(page)

        assert '  - "llm-wiki/entity"' in frontmatter
        assert '  canonical_path: "entities/User.md"' in frontmatter
        assert '  source_path: "models.py"' in frontmatter
        assert "  source_line: 3" in frontmatter
        assert '  - "entity/User"' in frontmatter

    def test_sidecar_relative_path_is_canonical_posix(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        page = next(
            page
            for page in obsidian.collect_wiki_pages(wiki)
            if page.canonical_rel == "entities/User.md"
        )

        relative = obsidian._sidecar_note_relative_path(page)

        assert relative == "entity/User.md"
        assert "\\" not in relative
        assert obsidian._sidecar_note_path(
            tmp_project / "notes", page
        ) == tmp_project / "notes" / "entity" / "User.md"

    def test_converts_internal_markdown_links_to_wikilinks(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        pages = obsidian.collect_wiki_pages(wiki)
        canonical = {page.canonical_rel: page for page in pages}
        page = canonical["entities/User.md"]

        content = obsidian.convert_markdown_links(
            "See [models](../modules/models.md) and [external](https://example.com).",
            page,
            canonical,
            wiki,
        )

        assert "[[LLM Wiki/Modules/models|models]]" in content
        assert "[external](https://example.com)" in content

    def test_export_creates_mirror_and_preserves_sidecar_note(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        note = vault / ".llm-wiki" / "obsidian-notes" / "entity" / "User.md"
        note.parent.mkdir(parents=True)
        note.write_text("# Existing Notes\n\nKeep this.\n", encoding="utf-8")

        report = obsidian.export_obsidian_vault(
            src_dir=".",
            wiki_dir=wiki,
            vault_dir=vault,
        )

        mirror = vault / "LLM Wiki" / "Entities" / "User.md"
        assert report.page_count == 10
        assert mirror.exists()
        assert (vault / "LLM Wiki" / "Flows" / "checkout.md").exists()
        assert (vault / "LLM Wiki" / "Dependencies.md").exists()
        assert (vault / "LLM Wiki" / "Load order.md").exists()
        content = mirror.read_text(encoding="utf-8")
        assert "aliases:" in content
        assert "[[LLM Wiki/Modules/models|models]]" in content
        assert "![[.llm-wiki/obsidian-notes/entity/User]]" in content
        assert note.read_text(encoding="utf-8") == "# Existing Notes\n\nKeep this.\n"

    def test_export_escapes_source_wikilinks_before_vault_check(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        user_page = wiki / "entities" / "User.md"
        user_page.write_text(
            user_page.read_text(encoding="utf-8")
            + "\nRaw source docs mention [[std::string::String]].\n",
            encoding="utf-8",
        )
        vault = tmp_project / "vault"

        obsidian.export_obsidian_vault(src_dir=".", wiki_dir=wiki, vault_dir=vault)

        mirror = vault / "LLM Wiki" / "Entities" / "User.md"
        content = mirror.read_text(encoding="utf-8")
        assert r"\[\[std::string::String\]\]" in content
        assert "[[LLM Wiki/Modules/models|models]]" in content
        report = obsidian.check_obsidian_vault(wiki_dir=wiki, vault_dir=vault)
        assert report.ok is True

    def test_export_reads_each_wiki_page_once(self, tmp_project, monkeypatch):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        canonical_paths = {
            page.canonical_path.resolve() for page in obsidian.collect_wiki_pages(wiki)
        }
        reads: dict[Path, int] = {}
        original_read_md = obsidian.read_md

        def counting_read_md(path: Path) -> str:
            resolved = path.resolve()
            if resolved in canonical_paths:
                reads[resolved] = reads.get(resolved, 0) + 1
            return original_read_md(path)

        monkeypatch.setattr(obsidian, "read_md", counting_read_md)

        report = obsidian.export_obsidian_vault(
            src_dir=".",
            wiki_dir=wiki,
            vault_dir=vault,
        )

        assert report.page_count == len(canonical_paths)
        assert set(reads) == canonical_paths
        assert sum(reads.values()) == len(canonical_paths)

    def test_export_dry_run_does_not_write(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"

        report = obsidian.export_obsidian_vault(
            src_dir=".",
            wiki_dir=wiki,
            vault_dir=vault,
            dry_run=True,
        )

        assert report.dry_run is True
        assert any(op.action == "would_write" for op in report.operations)
        assert not (vault / "LLM Wiki").exists()

    def test_knowledge_sidecars_do_not_change_obsidian_output(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        before_vault = tmp_project / "vault-before"
        after_vault = tmp_project / "vault-after"

        before_report = obsidian.export_obsidian_vault(
            src_dir=str(tmp_project),
            wiki_dir=wiki,
            vault_dir=before_vault,
        )
        before = {
            path.relative_to(before_vault).as_posix(): path.read_bytes()
            for path in sorted(before_vault.rglob("*"))
            if path.is_file()
        }

        (wiki / ".llm-wiki-knowledge.json").write_text(
            '{"schema_version": "future"}\n',
            encoding="utf-8",
        )
        (wiki / ".llm-wiki-manifest.json").write_text(
            '{"artifact_hashes": {}}\n',
            encoding="utf-8",
        )
        after_report = obsidian.export_obsidian_vault(
            src_dir=str(tmp_project),
            wiki_dir=wiki,
            vault_dir=after_vault,
        )
        after = {
            path.relative_to(after_vault).as_posix(): path.read_bytes()
            for path in sorted(after_vault.rglob("*"))
            if path.is_file()
        }

        assert after_report.page_count == before_report.page_count
        assert after == before
        assert not any("llm-wiki-knowledge" in path for path in after)

    def test_default_export_preserves_legacy_source_inventory_relationships(
        self, tmp_project, monkeypatch
    ):
        wiki = _write_wiki(tmp_project)
        (wiki / "entities" / "User.md").write_text(
            "# User\n\n**Location:** `models.py:3`\n",
            encoding="utf-8",
        )
        (wiki / "modules" / "models.md").write_text(
            "# models Module\n\n**Path:** `models.py`\n",
            encoding="utf-8",
        )
        vault = tmp_project / "vault"
        calls: list[tuple[str, bool]] = []

        def fixed_inventory(src_dir, *, deep=False):
            calls.append((src_dir, deep))
            return {
                "models.py": {
                    "classes": [{"name": "User", "line": 3}],
                }
            }

        monkeypatch.setattr(obsidian, "get_inventory", fixed_inventory)

        report = obsidian.export_obsidian_vault(
            src_dir=str(tmp_project),
            wiki_dir=wiki,
            vault_dir=vault,
        )

        assert report.ok is True
        assert calls == [(str(tmp_project), True)]
        user = (vault / "LLM Wiki" / "Entities" / "User.md").read_text(
            encoding="utf-8"
        )
        module = (vault / "LLM Wiki" / "Modules" / "models.md").read_text(
            encoding="utf-8"
        )
        assert "- [[LLM Wiki/Modules/models|models Module]]" in user
        assert "- [[LLM Wiki/Entities/User|User]]" in module

    def test_enriched_source_relationships_need_no_inventory_scan(
        self, tmp_project, monkeypatch
    ):
        wiki = _write_wiki(tmp_project)
        (tmp_project / "models.py").write_text("class User:\n    pass\n")
        (wiki / "entities" / "User.md").write_text(
            "# User\n\n**Location:** `models.py:3`\n",
            encoding="utf-8",
        )
        (wiki / "modules" / "models.md").write_text(
            "# models Module\n\n**Path:** `models.py`\n",
            encoding="utf-8",
        )

        monkeypatch.setattr(
            obsidian,
            "get_inventory",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("enriched export must not scan source inventory")
            ),
        )
        vault = tmp_project / "vault"
        obsidian.export_obsidian_vault(
            src_dir=str(tmp_project),
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=_knowledge_projection(wiki),
        )

        user = (vault / "LLM Wiki" / "Entities" / "User.md").read_text(
            encoding="utf-8"
        )
        module = (vault / "LLM Wiki" / "Modules" / "models.md").read_text(
            encoding="utf-8"
        )
        assert "- [[LLM Wiki/Modules/models|models Module]]" in user
        assert "- [[LLM Wiki/Entities/User|User]]" in module

    def test_disabled_export_keeps_prefeature_bytes_when_inventory_fails(
        self, tmp_project, monkeypatch
    ):
        wiki = _write_wiki(tmp_project)
        module_page = wiki / "modules" / "models.md"
        module_page.write_text(
            module_page.read_text(encoding="utf-8").replace(
                "# models Module",
                "# models]] [[/etc/passwd",
            ),
            encoding="utf-8",
        )
        missing_source = tmp_project / "source-does-not-exist"
        calls: list[tuple[str, bool]] = []

        def failed_inventory(src_dir, *, deep=False):
            calls.append((src_dir, deep))
            raise FileNotFoundError(src_dir)

        monkeypatch.setattr(obsidian, "get_inventory", failed_inventory)
        vault = tmp_project / "legacy-vault"
        obsidian.export_obsidian_vault(
            src_dir=str(missing_source),
            wiki_dir=wiki,
            vault_dir=vault,
        )

        expected = (
            "---\n"
            "aliases:\n"
            '  - "User"\n'
            '  - "entity/User"\n'
            '  - "entities/User.md"\n'
            '  - "entities/User"\n'
            '  - "models.py"\n'
            "tags:\n"
            '  - "llm-wiki/entity"\n'
            "llm_wiki:\n"
            '  kind: "entity"\n'
            '  id: "User"\n'
            '  canonical_path: "entities/User.md"\n'
            '  source_path: "models.py"\n'
            "  source_line: 3\n"
            "---\n"
            "\n"
            "# User\n"
            "\n"
            "**Location:** `models.py:3`\n"
            "**Module:** [[LLM Wiki/Modules/models|models]]\n"
            "\n"
            "## Description\n"
            "\n"
            "A user entity.\n"
            "\n"
            "## Related\n"
            "\n"
            "- [[LLM Wiki/Index|LLM Wiki Index]]\n"
            "- [[LLM Wiki/Modules/models|models]] [[/etc/passwd]]\n"
            "\n"
            "## Human Notes\n"
            "\n"
            "![[.llm-wiki/obsidian-notes/entity/User]]\n"
        ).encode()
        actual = (
            vault / "LLM Wiki" / "Entities" / "User.md"
        ).read_bytes()

        assert calls == [(str(missing_source), True)]
        assert actual == expected

        enriched_vault = tmp_project / "enriched-vault"
        projection = _knowledge_projection(wiki)
        obsidian.export_obsidian_vault(
            src_dir=str(missing_source),
            wiki_dir=wiki,
            vault_dir=enriched_vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        enriched = (
            enriched_vault / "LLM Wiki" / "Entities" / "User.md"
        ).read_text(encoding="utf-8")
        assert calls == [(str(missing_source), True)]
        assert "|models\\]\\] \\[\\[/etc/passwd]]" in enriched

    def test_opt_in_projection_is_private_by_construction_and_typed(
        self, tmp_project
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        projection = _knowledge_projection(wiki)

        report = obsidian.export_obsidian_vault(
            src_dir=str(tmp_project),
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )

        content = (
            vault / "LLM Wiki" / "Entities" / "User.md"
        ).read_text(encoding="utf-8")
        assert report.ok is True
        assert report.freshness == "unevaluated (snapshot-only read)"
        assert report.to_dict()["freshness"] == (
            "unevaluated (snapshot-only read)"
        )
        assert (
            "Freshness: unevaluated (snapshot-only read)"
            in obsidian.render_report_text(report, action="export")
        )
        assert (
            '"freshness": "unevaluated (snapshot-only read)"'
            in obsidian.render_report_json(report)
        )
        assert 'knowledge_bundle_id: "bundle-1"' in content
        assert 'knowledge_uid: "bundle-1#lw:doc:' in content
        assert 'knowledge_profile: "public-portable"' in content
        assert '  freshness: "unevaluated (snapshot-only read)"' in content
        assert "## Typed Relationships" in content
        assert "### Incoming: `depends_on`" in content
        assert "### Outgoing: `calls`" in content
        assert "[[LLM Wiki/Modules/models|models Module]]" in content
        assert "Unresolved target — resolution `unresolved`" in content
        assert "evidence state `present`, observed 1, unique 1" in content
        assert (
            "coverage observed 1, emitted 1, omitted 0, limit 20, "
            "truncated false"
        ) in content
        assert "sk_seeded_private_value" not in content
        assert "sk_seeded_bundle_value" not in content
        checked = obsidian.check_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        assert checked.freshness == "unevaluated (snapshot-only read)"

    def test_reports_omit_freshness_when_projection_is_disabled(
        self,
        tmp_project,
    ):
        wiki = _write_wiki(tmp_project)
        report = obsidian.export_obsidian_vault(
            src_dir=str(tmp_project),
            wiki_dir=wiki,
            vault_dir=tmp_project / "vault",
        )

        assert report.freshness is None
        assert "freshness" not in report.to_dict()
        assert "Freshness:" not in obsidian.render_report_text(
            report,
            action="export",
        )

    def test_check_rejects_enriched_vault_when_knowledge_mode_is_omitted(
        self,
        tmp_project,
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=_knowledge_projection(wiki),
        )

        report = obsidian.check_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
        )

        assert report.ok is False
        assert report.freshness is None
        assert any(
            issue["category"] == "unexpected_knowledge_metadata"
            and issue["path"]
            == str(vault / "LLM Wiki" / "Entities" / "User.md")
            for issue in report.issues
        )

    def test_disabled_check_reserves_freshness_but_allows_other_metadata(
        self,
        tmp_project,
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        obsidian.export_obsidian_vault(
            src_dir=str(tmp_project),
            wiki_dir=wiki,
            vault_dir=vault,
        )
        page = vault / "LLM Wiki" / "Index.md"
        content = page.read_text(encoding="utf-8").replace(
            "---\n",
            '---\nowner: "docs-team"\n',
            1,
        )
        page.write_text(content, encoding="utf-8")

        unrelated = obsidian.check_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
        )
        assert unrelated.ok is True

        page.write_text(
            content.replace(
                "llm_wiki:\n",
                "llm_wiki:\n"
                '  freshness: "unevaluated (snapshot-only read)"\n',
                1,
            ),
            encoding="utf-8",
        )
        retained = obsidian.check_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
        )

        assert retained.ok is False
        assert any(
            issue["category"] == "unexpected_knowledge_metadata"
            and issue["path"] == str(page)
            for issue in retained.issues
        )

    def test_public_projection_omits_legacy_source_frontmatter_and_alias(
        self, tmp_project
    ):
        wiki = _write_wiki(tmp_project)
        user = wiki / "entities" / "User.md"
        user.write_text(
            user.read_text(encoding="utf-8").replace(
                "`models.py:3`",
                "`/Users/alice/private/models.py:3`",
            ),
            encoding="utf-8",
        )
        projection = _knowledge_projection(wiki)
        vault = tmp_project / "vault"

        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )

        content = (
            vault / "LLM Wiki" / "Entities" / "User.md"
        ).read_text(encoding="utf-8")
        frontmatter = obsidian._frontmatter_block(content)
        assert frontmatter is not None
        assert "source_path:" not in frontmatter
        assert "source_line:" not in frontmatter
        assert "/Users/alice/private/models.py" not in frontmatter

    def test_enriched_external_notes_are_plain_and_path_private(
        self, tmp_project
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        notes = tmp_project / "private-human-notes"

        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            notes_dir=notes,
            knowledge_metadata="summary",
            knowledge_projection=_knowledge_projection(wiki),
        )

        content = (
            vault / "LLM Wiki" / "Entities" / "User.md"
        ).read_text(encoding="utf-8")
        assert "_Human note is stored outside this vault._" in content
        assert str(notes) not in content
        assert (notes / "entity" / "User.md").is_file()

    def test_opt_in_projection_rejects_unknown_bundle_and_uid(self, tmp_project):
        wiki = _write_wiki(tmp_project)

        with pytest.raises(obsidian.ObsidianError, match="bundle"):
            obsidian.export_obsidian_vault(
                wiki_dir=wiki,
                vault_dir=tmp_project / "unknown-bundle",
                knowledge_metadata="summary",
                knowledge_projection=_knowledge_projection(
                    wiki,
                    bundle_id="unknown",
                ),
            )

    def test_projection_schema_hash_and_page_set_fail_before_writes(
        self, tmp_project
    ):
        wiki = _write_wiki(tmp_project)
        projection = _knowledge_projection(wiki)
        payload = projection.to_payload()
        payload["concepts"]["guides/stale.md"] = dict(
            payload["concepts"]["guides/operator-onboarding.md"]
        )
        payload["concepts"]["guides/stale.md"]["canonical_path"] = (
            "guides/stale.md"
        )
        projection = _projection_from_payload(payload)
        vault = tmp_project / "stale-vault"
        with pytest.raises(obsidian.ObsidianError, match="page set"):
            obsidian.export_obsidian_vault(
                wiki_dir=wiki,
                vault_dir=vault,
                knowledge_metadata="summary",
                knowledge_projection=projection,
            )
        assert not vault.exists()

        invalid_hash = replace(
            _knowledge_projection(wiki),
            source_knowledge_hash="not-a-hash",
        )
        with pytest.raises(obsidian.ObsidianError, match="source_knowledge_hash"):
            obsidian.export_obsidian_vault(
                wiki_dir=wiki,
                vault_dir=tmp_project / "hash-vault",
                knowledge_metadata="summary",
                knowledge_projection=invalid_hash,
            )
        assert not (tmp_project / "hash-vault").exists()

        with pytest.raises(obsidian.ObsidianError, match="identity.uid"):
            obsidian.export_obsidian_vault(
                wiki_dir=wiki,
                vault_dir=tmp_project / "unknown-uid",
                knowledge_metadata="summary",
                knowledge_projection=_knowledge_projection(
                    wiki,
                    unknown_uid_path="entities/User.md",
                ),
            )

    def test_projection_check_detects_metadata_and_relationship_tampering(
        self, tmp_project
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        projection = _knowledge_projection(wiki)
        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        user_page = vault / "LLM Wiki" / "Entities" / "User.md"
        content = user_page.read_text(encoding="utf-8")
        content = content.replace(
            'knowledge_bundle_id: "bundle-1"',
            'knowledge_bundle_id: "tampered"',
            1,
        ).replace(
            "resolution `resolved`",
            "resolution `tampered`",
            1,
        )
        user_page.write_text(content, encoding="utf-8")

        checked = obsidian.check_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )

        categories = {issue["category"] for issue in checked.issues}
        assert checked.ok is False
        assert "knowledge_metadata_mismatch" in categories
        assert "knowledge_relationship_mismatch" in categories

    def test_enriched_reexport_rejects_stale_projected_page_before_writes(
        self, tmp_project
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        notes_dir = Path("LLM Wiki") / "Human Notes"
        internal_payload = _knowledge_projection(wiki).to_payload()
        internal_payload["profile"] = "internal"
        internal_payload["bundle"]["snapshot"] = {
            "source_snapshot_hash": "sha256:" + "1" * 64,
            "markdown_snapshot_hash": "sha256:" + "2" * 64,
            "surface_index_hash": "sha256:" + "3" * 64,
            "generation_options_hash": "sha256:" + "4" * 64,
        }
        internal_payload["bundle"]["producer"] = {
            "tool": {
                "id": "llm-wiki",
                "version": "test",
                "limitations": [],
            },
            "extractors": [],
            "plugins": [],
        }
        surface_by_path = {
            page.relative_path: page
            for page in obsidian.wiki_surface.collect_wiki_pages(wiki)
        }
        for canonical_path, concept in internal_payload["concepts"].items():
            surface = surface_by_path[canonical_path]
            concept["locator"] = canonical_path
            concept["document"] = {
                "page_kind": surface.kind.value,
                "page_id": surface.page_id,
                "role": surface.role.value,
            }
            concept["authorship"] = {"kind": "unknown"}
        internal_projection = _projection_from_payload(internal_payload)
        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            notes_dir=notes_dir,
            knowledge_metadata="summary",
            knowledge_projection=internal_projection,
        )

        stale_mirror = (
            vault / "LLM Wiki" / "Guides" / "operator-onboarding.md"
        )
        stale_note = (
            vault
            / "LLM Wiki"
            / "Human Notes"
            / "guide"
            / "operator-onboarding.md"
        )
        stale_note.write_text("# Human-owned stale note\n", encoding="utf-8")
        unrelated = vault / "LLM Wiki" / "Personal.md"
        unrelated.write_text("# Unrelated user page\n", encoding="utf-8")
        expected_page = vault / "LLM Wiki" / "Index.md"
        expected_page.write_text("KEEP-BEFORE-WRITES\n", encoding="utf-8")
        (wiki / "guides" / "operator-onboarding.md").unlink()
        public_projection = _knowledge_projection(wiki)

        with pytest.raises(
            obsidian.ObsidianError,
            match="Unexpected projected Obsidian mirror page",
        ):
            obsidian.export_obsidian_vault(
                wiki_dir=wiki,
                vault_dir=vault,
                notes_dir=notes_dir,
                knowledge_metadata="summary",
                knowledge_projection=public_projection,
            )

        assert expected_page.read_text(encoding="utf-8") == (
            "KEEP-BEFORE-WRITES\n"
        )
        assert 'knowledge_profile: "internal"' in stale_mirror.read_text(
            encoding="utf-8"
        )
        assert unrelated.read_text(encoding="utf-8") == "# Unrelated user page\n"
        assert stale_note.read_text(encoding="utf-8") == (
            "# Human-owned stale note\n"
        )

        checked = obsidian.check_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=public_projection,
        )
        unexpected = [
            issue
            for issue in checked.issues
            if issue["category"] == "unexpected_projected_mirror_page"
        ]
        assert [issue["path"] for issue in unexpected] == [str(stale_mirror)]
        assert all(
            "Personal.md" not in issue["path"]
            and "Human Notes" not in issue["path"]
            for issue in unexpected
        )

    def test_enriched_scan_fails_closed_on_unexpected_symlink(
        self, tmp_project
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        projection = _knowledge_projection(wiki)
        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        outside = tmp_project / "outside.md"
        outside.write_text(
            "---\n"
            "llm_wiki:\n"
            '  knowledge_profile: "internal"\n'
            "---\n",
            encoding="utf-8",
        )
        stale = vault / "LLM Wiki" / "stale.md"
        stale.symlink_to(outside)
        expected_page = vault / "LLM Wiki" / "Index.md"
        expected_before = expected_page.read_bytes()
        outside_before = outside.read_bytes()

        with pytest.raises(obsidian.ObsidianError, match="symlink entry"):
            obsidian.export_obsidian_vault(
                wiki_dir=wiki,
                vault_dir=vault,
                knowledge_metadata="summary",
                knowledge_projection=projection,
            )
        checked = obsidian.check_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )

        assert expected_page.read_bytes() == expected_before
        assert outside.read_bytes() == outside_before
        assert any(
            issue["category"] == "unsafe_projected_mirror_scan"
            and "symlink entry" in issue["message"]
            for issue in checked.issues
        )

    def test_enriched_scan_uses_fresh_no_follow_direntry_metadata(
        self,
        tmp_project,
        monkeypatch: pytest.MonkeyPatch,
    ):
        vault = tmp_project / "vault"
        mirror = vault / obsidian.MIRROR_ROOT
        page = mirror / "Index.md"
        page.parent.mkdir(parents=True)
        page.write_text("# Existing index\n", encoding="utf-8")
        cached_stat_calls = 0
        fresh_stat_paths: list[Path] = []
        real_fresh_stat = obsidian.fresh_no_follow_stat

        class EmulatedWindowsDirEntry:
            name = page.name
            path = os.fspath(page)

            def stat(self, *, follow_symlinks: bool = True):
                nonlocal cached_stat_calls
                cached_stat_calls += 1
                raise AssertionError(
                    "Windows DirEntry.stat() metadata must not be trusted"
                )

        @contextmanager
        def scandir(directory: str | Path):
            assert Path(directory) == mirror
            yield [EmulatedWindowsDirEntry()]

        def fresh_stat(path: str | Path) -> os.stat_result:
            fresh_stat_paths.append(Path(path))
            return real_fresh_stat(path)

        monkeypatch.setattr(obsidian.os, "scandir", scandir)
        monkeypatch.setattr(obsidian, "fresh_no_follow_stat", fresh_stat)

        assert obsidian._unexpected_projected_mirror_pages(
            vault,
            expected_relative_paths=["Index.md"],
        ) == []
        assert cached_stat_calls == 0
        assert fresh_stat_paths == [page]

    def test_enriched_scan_rejects_hardlinked_markdown(self, tmp_project):
        vault = tmp_project / "vault"
        mirror = vault / obsidian.MIRROR_ROOT
        mirror.mkdir(parents=True)
        shared = vault / "shared.md"
        shared.write_text("# Shared\n", encoding="utf-8")
        linked = mirror / "stale.md"
        try:
            os.link(shared, linked)
        except OSError as exc:
            pytest.skip(f"hard links are unavailable: {exc}")

        with pytest.raises(obsidian.ObsidianError, match="hard-linked file"):
            obsidian._unexpected_projected_mirror_pages(
                vault,
                expected_relative_paths=[],
            )

    @pytest.mark.parametrize(
        ("path_kind", "error"),
        [
            ("symlink", "unsafe existing path component"),
            ("hardlink", "hard-linked file"),
            ("directory", "not a regular file"),
        ],
    )
    def test_enriched_export_preflights_late_expected_destination(
        self, tmp_project, path_kind, error
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        projection = _knowledge_projection(wiki)
        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        pages = obsidian.collect_wiki_pages(wiki)
        early = vault / pages[0].mirror_rel
        late = vault / pages[-1].mirror_rel
        early.write_text("EARLY-PAGE-MUST-STAY\n", encoding="utf-8")
        late.unlink()
        preserved = vault / "preserved-target.md"
        preserved.write_text("PRESERVED-TARGET\n", encoding="utf-8")
        if path_kind == "symlink":
            late.symlink_to(preserved)
        elif path_kind == "hardlink":
            obsidian.os.link(preserved, late)
        else:
            late.mkdir()
        preserved_before = preserved.read_bytes()

        with pytest.raises(obsidian.ObsidianError, match=error):
            obsidian.export_obsidian_vault(
                wiki_dir=wiki,
                vault_dir=vault,
                knowledge_metadata="summary",
                knowledge_projection=projection,
            )

        assert early.read_text(encoding="utf-8") == "EARLY-PAGE-MUST-STAY\n"
        assert preserved.read_bytes() == preserved_before

    def test_enriched_export_preflights_late_sidecar_parent(
        self, tmp_project
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        notes = tmp_project / "notes"
        projection = _knowledge_projection(wiki)
        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            notes_dir=notes,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        pages = obsidian.collect_wiki_pages(wiki)
        early = vault / pages[0].mirror_rel
        early.write_text("EARLY-PAGE-MUST-STAY\n", encoding="utf-8")
        late_note_parent = notes / pages[-1].kind
        shutil.rmtree(late_note_parent)
        late_note_parent.write_text("NOT-A-DIRECTORY\n", encoding="utf-8")

        with pytest.raises(
            obsidian.ObsidianError,
            match="unsafe existing path component",
        ):
            obsidian.export_obsidian_vault(
                wiki_dir=wiki,
                vault_dir=vault,
                notes_dir=notes,
                knowledge_metadata="summary",
                knowledge_projection=projection,
            )

        assert early.read_text(encoding="utf-8") == "EARLY-PAGE-MUST-STAY\n"
        assert late_note_parent.read_text(encoding="utf-8") == (
            "NOT-A-DIRECTORY\n"
        )

    def test_enriched_scan_bounds_projected_frontmatter(
        self, tmp_project
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        projection = _knowledge_projection(wiki)
        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        oversized = vault / "LLM Wiki" / "oversized.md"
        oversized.write_bytes(
            b"---\nllm_wiki:\n  knowledge_profile: \"internal\"\n"
            + b"x" * obsidian.MAX_OBSIDIAN_PROJECTED_FRONTMATTER_BYTES
        )
        expected_page = vault / "LLM Wiki" / "Index.md"
        expected_before = expected_page.read_bytes()

        with pytest.raises(obsidian.ObsidianError, match="exceeds the size limit"):
            obsidian.export_obsidian_vault(
                wiki_dir=wiki,
                vault_dir=vault,
                knowledge_metadata="summary",
                knowledge_projection=projection,
            )
        checked = obsidian.check_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )

        assert expected_page.read_bytes() == expected_before
        assert any(
            issue["category"] == "unsafe_projected_mirror_scan"
            and "exceeds the size limit" in issue["message"]
            for issue in checked.issues
        )

    @pytest.mark.parametrize(
        ("limit_name", "message"),
        [
            ("MAX_OBSIDIAN_MIRROR_SCAN_ENTRIES", "entry limit exceeded"),
            ("MAX_OBSIDIAN_MIRROR_SCAN_DEPTH", "depth limit exceeded"),
        ],
    )
    def test_enriched_scan_bounds_tree_before_writes(
        self, tmp_project, monkeypatch, limit_name, message
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        projection = _knowledge_projection(wiki)
        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        expected_page = vault / "LLM Wiki" / "Index.md"
        expected_page.write_text("KEEP-BEFORE-WRITES\n", encoding="utf-8")
        monkeypatch.setattr(obsidian, limit_name, 0)

        with pytest.raises(obsidian.ObsidianError, match=message):
            obsidian.export_obsidian_vault(
                wiki_dir=wiki,
                vault_dir=vault,
                knowledge_metadata="summary",
                knowledge_projection=projection,
            )

        assert expected_page.read_text(encoding="utf-8") == (
            "KEEP-BEFORE-WRITES\n"
        )

    def test_enriched_scan_ignores_large_unrelated_user_markdown(
        self, tmp_project
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        projection = _knowledge_projection(wiki)
        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        unrelated = vault / "LLM Wiki" / "Personal.md"
        unrelated.write_bytes(
            b"# Human note\n"
            + b"x" * (obsidian.MAX_OBSIDIAN_PROJECTED_FRONTMATTER_BYTES + 1)
        )
        before = unrelated.read_bytes()

        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        checked = obsidian.check_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )

        assert checked.ok is True
        assert unrelated.read_bytes() == before

    @pytest.mark.parametrize(
        "metadata",
        [
            'knowledge_profile: "internal"',
            'source_knowledge_hash: "sha256:private"',
            'source_path: "/private/repository/source.py"',
        ],
    )
    def test_enriched_scan_rejects_top_level_projected_metadata(
        self, tmp_project, metadata
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        projection = _knowledge_projection(wiki)
        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        stale = vault / "LLM Wiki" / "stale.md"
        stale.write_text(f"---\n{metadata}\n---\n", encoding="utf-8")

        with pytest.raises(
            obsidian.ObsidianError,
            match="Unexpected projected Obsidian mirror page",
        ):
            obsidian.export_obsidian_vault(
                wiki_dir=wiki,
                vault_dir=vault,
                knowledge_metadata="summary",
                knowledge_projection=projection,
            )

    def test_enriched_scan_reserves_nested_freshness_disclosure(
        self,
        tmp_project,
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        projection = _knowledge_projection(wiki)
        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        stale = vault / "LLM Wiki" / "freshness-only.md"
        stale.write_text(
            "---\n"
            "llm_wiki:\n"
            '  freshness: "unevaluated (snapshot-only read)"\n'
            "---\n",
            encoding="utf-8",
        )

        with pytest.raises(
            obsidian.ObsidianError,
            match="Unexpected projected Obsidian mirror page",
        ):
            obsidian.export_obsidian_vault(
                wiki_dir=wiki,
                vault_dir=vault,
                knowledge_metadata="summary",
                knowledge_projection=projection,
            )
        checked = obsidian.check_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        assert any(
            issue["category"] == "unexpected_projected_mirror_page"
            and issue["path"] == str(stale)
            for issue in checked.issues
        )

    @pytest.mark.parametrize(
        "duplicate",
        [
            '  source_knowledge_hash: "PRIVATE-SENTINEL"\n',
            "llm_wiki:\n"
            '  knowledge_profile: "internal"\n',
        ],
    )
    def test_enriched_check_rejects_duplicate_frontmatter_keys(
        self, tmp_project, duplicate
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        projection = _knowledge_projection(wiki)
        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        user_page = vault / "LLM Wiki" / "Entities" / "User.md"
        content = user_page.read_text(encoding="utf-8")
        user_page.write_text(
            content.replace(
                '  source_knowledge_hash: "sha256:',
                duplicate + '  source_knowledge_hash: "sha256:',
                1,
            ),
            encoding="utf-8",
        )

        checked = obsidian.check_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )

        assert checked.ok is False
        assert any(
            issue["category"] == "knowledge_metadata_mismatch"
            and issue["path"] == str(user_page)
            for issue in checked.issues
        )

    def test_sidecar_creation_is_exclusive(self, tmp_project):
        note = tmp_project / "notes" / "entity" / "User.md"
        note.parent.mkdir(parents=True)
        note.write_text("# Human note\n", encoding="utf-8")

        created = obsidian._create_note_exclusive(note, "# Generated note\n")

        assert created is False
        assert note.read_text(encoding="utf-8") == "# Human note\n"

    def test_interrupted_sidecar_creation_leaves_no_partial_note(
        self, tmp_project, monkeypatch
    ):
        note = tmp_project / "notes" / "entity" / "User.md"

        def interrupt(*_args, **_kwargs):
            raise RuntimeError("interrupted before atomic publication")

        monkeypatch.setattr(obsidian.os, "link", interrupt)
        with pytest.raises(RuntimeError, match="interrupted"):
            obsidian._create_note_exclusive(note, "# Generated note\n")

        assert not note.exists()
        assert not list(note.parent.glob(".*.tmp"))

    def test_check_detects_missing_mirror_and_broken_wikilinks(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        report = obsidian.check_obsidian_vault(wiki_dir=wiki, vault_dir=vault)

        assert report.ok is False
        assert any(
            issue["category"] == "missing_mirror_page" for issue in report.issues
        )

        obsidian.export_obsidian_vault(src_dir=".", wiki_dir=wiki, vault_dir=vault)
        user_page = vault / "LLM Wiki" / "Entities" / "User.md"
        user_page.write_text(
            user_page.read_text(encoding="utf-8") + "\n[[LLM Wiki/Missing/Page]]\n",
            encoding="utf-8",
        )
        broken = obsidian.check_obsidian_vault(wiki_dir=wiki, vault_dir=vault)

        assert any(issue["category"] == "broken_wikilink" for issue in broken.issues)

    def test_check_reports_unsafe_wikilinks_without_escaping_vault(
        self, tmp_project
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        obsidian.export_obsidian_vault(wiki_dir=wiki, vault_dir=vault)
        user_page = vault / "LLM Wiki" / "Entities" / "User.md"
        user_page.write_text(
            user_page.read_text(encoding="utf-8") + "\n[[../outside]]\n",
            encoding="utf-8",
        )

        report = obsidian.check_obsidian_vault(wiki_dir=wiki, vault_dir=vault)

        assert report.ok is False
        assert any(
            issue["category"] == "unsafe_wikilink"
            and issue["target"] == "../outside"
            for issue in report.issues
        )

    def test_enriched_check_rejects_absolute_wikilinks(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        projection = _knowledge_projection(wiki)
        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        user_page = vault / "LLM Wiki" / "Entities" / "User.md"
        user_page.write_text(
            user_page.read_text(encoding="utf-8") + "\n[[/etc/passwd]]\n",
            encoding="utf-8",
        )

        report = obsidian.check_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )

        assert report.ok is False
        assert any(
            issue["category"] == "unsafe_wikilink"
            and issue["target"] == "/etc/passwd"
            for issue in report.issues
        )

    def test_generated_wikilink_aliases_escape_bracket_injection(
        self, tmp_project
    ):
        wiki = _write_wiki(tmp_project)
        module = wiki / "modules" / "models.md"
        module.write_text(
            module.read_text(encoding="utf-8").replace(
                "# models Module",
                "# models]] [[LLM Wiki/Missing",
            ),
            encoding="utf-8",
        )
        vault = tmp_project / "vault"
        projection = _knowledge_projection(wiki)

        obsidian.export_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )

        report = obsidian.check_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        user = (vault / "LLM Wiki" / "Entities" / "User.md").read_text(
            encoding="utf-8"
        )
        assert report.ok is True
        assert "|models\\]\\] \\[\\[LLM Wiki/Missing]]" in user

    def test_path_escape_is_rejected(self, tmp_project):
        vault = tmp_project / "vault"

        with pytest.raises(obsidian.ObsidianError):
            obsidian._safe_join(vault, "../outside.md")

    @pytest.mark.parametrize("target", ["vault", "notes"])
    def test_export_rejects_derived_paths_overlapping_authority(
        self, tmp_project, target
    ):
        wiki = _write_wiki(tmp_project)
        kwargs = {
            "wiki_dir": wiki,
            "vault_dir": wiki if target == "vault" else tmp_project / "vault",
        }
        if target == "notes":
            kwargs["notes_dir"] = wiki / "human-notes"

        with pytest.raises(obsidian.ObsidianError, match="canonical wiki"):
            obsidian.export_obsidian_vault(**kwargs)


class TestObsidianCli:
    def test_cli_loads_knowledge_only_when_metadata_is_enabled(
        self, tmp_project, monkeypatch, capsys
    ):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"

        def unexpected_load(*_args, **_kwargs):
            raise AssertionError("knowledge must stay disabled by default")

        monkeypatch.setattr(
            obsidian_cmd,
            "load_knowledge_read_view",
            unexpected_load,
        )
        obsidian_cmd.run(
            _ns(
                obsidian_action="export",
                src_dir=".",
                wiki_dir=str(wiki),
                vault_dir=str(vault),
                notes_dir=".llm-wiki/obsidian-notes",
                dry_run=False,
                format="json",
            )
        )
        assert json.loads(capsys.readouterr().out)["ok"] is True

        load_calls: list[dict[str, object]] = []
        expected_projection = _knowledge_projection(wiki)

        def load_view(path, **kwargs):
            load_calls.append({"path": path, **kwargs})
            return object()

        monkeypatch.setattr(obsidian_cmd, "load_knowledge_read_view", load_view)
        monkeypatch.setattr(
            obsidian_cmd,
            "project_knowledge",
            lambda view, **kwargs: expected_projection,
        )
        obsidian_cmd.run(
            _ns(
                obsidian_action="export",
                src_dir=".",
                wiki_dir=str(wiki),
                vault_dir=str(tmp_project / "enriched-vault"),
                notes_dir=".llm-wiki/obsidian-notes",
                dry_run=False,
                knowledge_metadata="summary",
                knowledge_profile="public-portable",
                knowledge_public_repository_identity=None,
                format="json",
            )
        )

        assert json.loads(capsys.readouterr().out)["ok"] is True
        assert load_calls == [
            {
                "path": str(wiki),
                "snapshot_only": True,
                "include_machine_verification": True,
            }
        ]

    def test_cli_export_and_check_json(self, tmp_project, capsys):
        _write_wiki(tmp_project)
        vault = tmp_project / "vault"

        obsidian_cmd.run(
            _ns(
                obsidian_action="export",
                src_dir=".",
                wiki_dir="docs/llm_wiki",
                vault_dir=str(vault),
                notes_dir=".llm-wiki/obsidian-notes",
                dry_run=False,
                format="json",
            )
        )
        data = json.loads(capsys.readouterr().out)
        assert data["page_count"] == 10

        obsidian_cmd.run(
            _ns(
                obsidian_action="check",
                wiki_dir="docs/llm_wiki",
                vault_dir=str(vault),
                format="json",
            )
        )
        check = json.loads(capsys.readouterr().out)
        assert check["ok"] is True

    def test_cli_install_plugin(self, tmp_project):
        vault = tmp_project / "vault"

        obsidian_cmd.run(
            _ns(
                obsidian_action="install-plugin",
                vault_dir=str(vault),
                plugin_dir="integrations/obsidian/llm-wiki",
                format="text",
            )
        )

        assert (vault / ".obsidian" / "plugins" / "llm-wiki" / "manifest.json").exists()
        assert (vault / ".obsidian" / "plugins" / "llm-wiki" / "main.js").exists()

    def test_cli_help_includes_obsidian(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["llm-wiki", "obsidian", "--help"])

        with pytest.raises(SystemExit) as exc:
            cli.main()

        assert exc.value.code == 0
        assert "export" in capsys.readouterr().out


class TestObsidianPluginPackage:
    def test_manifest_and_package_metadata(self):
        root = Path("integrations/obsidian/llm-wiki")
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        package = json.loads((root / "package.json").read_text(encoding="utf-8"))

        assert manifest["id"] == "llm-wiki"
        assert manifest["isDesktopOnly"] is True
        assert package["scripts"]["build"]

    def test_main_js_syntax(self):
        node = shutil.which("node")
        if not node:
            pytest.skip("node is not installed")

        subprocess.run(
            [node, "--check", "integrations/obsidian/llm-wiki/main.js"],
            check=True,
            capture_output=True,
            text=True,
        )


def test_text_report_discloses_operations_issues_and_no_issue_state():
    report = obsidian.ObsidianReport(
        dry_run=True,
        wiki_dir="docs/llm_wiki",
        vault_dir="vault",
        page_count=1,
        freshness="current",
        operations=[
            obsidian.ObsidianOperation("write", "LLM Wiki/index.md", "page")
        ],
        issues=[
            {
                "category": "broken_link",
                "path": "index.md",
                "target": "missing.md",
                "message": "missing",
            }
        ],
    )

    rendered = obsidian.render_report_text(report, action="export")

    for expected in (
        "Wiki: docs/llm_wiki",
        "Freshness: current",
        "Pages: 1",
        "Dry run: no files were changed.",
        "Operations:",
        "- write: LLM Wiki/index.md - page",
        "Issues:",
        "index.md -> missing.md - missing",
    ):
        assert expected in rendered

    assert (
        "No Obsidian mirror issues found."
        in obsidian.render_report_text(
            obsidian.ObsidianReport(vault_dir="vault"),
            action="check",
        )
    )
