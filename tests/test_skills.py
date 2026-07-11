"""Tests for bundled agent skill listing, export, and installation."""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import skills_cmd
from llm_wiki_cli.services import skills


def _ns(**kwargs):
    return types.SimpleNamespace(**kwargs)


def _write_custom_skill(root: Path, skill_id: str = "demo") -> Path:
    skill_dir = root / skill_id
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo\ndescription: A demo skill.\n---\n\n# demo\n",
        encoding="utf-8",
    )
    (skill_dir / "extra.md").write_text("# extra\n", encoding="utf-8")
    return skill_dir


class TestBundledWikiSyncSkill:
    def test_wiki_sync_skill_is_bundled(self):
        by_id = {skill.skill_id: skill for skill in skills.list_bundled_skills()}
        assert "wiki-sync" in by_id
        wiki_sync = by_id["wiki-sync"]
        assert wiki_sync.name == "wiki-sync"
        assert "sync" in wiki_sync.description.lower()
        assert wiki_sync.files[0] == "SKILL.md"
        assert "reference.md" in wiki_sync.files

    def test_wiki_sync_skill_encodes_core_loop_and_guardrails(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "wiki-sync"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")

        # Deterministic pass, validation loop, and commit convention.
        assert "llm-wiki sync --jobs 1" in manifest
        assert "lint --strict" in manifest
        assert "docs(wiki):" in manifest
        assert "The supervisor owns heavy-gate scheduling" in manifest
        assert "must not launch a heavy gate unless explicitly assigned" in manifest
        assert "report unfinished gates as" in manifest
        assert "inconclusive until capacity is recovered" in manifest
        # Hook-path markers are reserved, not reused.
        assert "LLM_WIKI_AUTO_COMMIT" in manifest
        assert "auto-update [bot]" in manifest
        # Semantic-only guardrail and unattended-path handoff live in the
        # bundled reference file.
        assert "Do not edit by hand" in reference
        assert "trigger-agent" in reference
        assert "--allow-external-src" in reference

    def test_wiki_sync_skill_documents_external_team_check_contract(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "wiki-sync"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "team check --src-dir <repo>" in combined
        assert "team check --src-dir <repo> --allow-external-src" in combined
        assert (
            "`--wiki-dir` itself always stays inside the current project root"
            in combined
        )

    def test_frontmatter_parses_name_and_description(self):
        name, description = skills._parse_skill_frontmatter(
            "---\nname: wiki-sync\ndescription: Sync the wiki.\n---\n\n# body\n"
        )
        assert name == "wiki-sync"
        assert description == "Sync the wiki."

    def test_frontmatter_missing_returns_empty(self):
        assert skills._parse_skill_frontmatter("# no frontmatter\n") == ("", "")


class TestBundledWikiBootstrapSkill:
    def test_wiki_bootstrap_skill_is_bundled(self):
        by_id = {skill.skill_id: skill for skill in skills.list_bundled_skills()}
        assert "wiki-bootstrap" in by_id
        wiki_bootstrap = by_id["wiki-bootstrap"]
        assert wiki_bootstrap.name == "wiki-bootstrap"
        assert "bootstrap" in wiki_bootstrap.description.lower()
        assert wiki_bootstrap.files[0] == "SKILL.md"
        assert "reference.md" in wiki_bootstrap.files

    def test_wiki_bootstrap_skill_encodes_core_loop_and_guardrails(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "wiki-bootstrap"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")

        # Helper preparation, deterministic bootstrap, validation loop, and
        # commit convention.
        assert "llm-wiki prepare-extractors" in manifest
        assert "--depth full --format json" in manifest
        assert "lint --strict" in manifest
        assert "docs(wiki): bootstrap" in manifest
        # Manifest-exists handoff to the incremental workflow.
        assert ".llm-wiki-manifest.json" in manifest
        assert "wiki-sync" in manifest
        # Hook-path markers are reserved, not reused.
        assert "LLM_WIKI_AUTO_COMMIT" in manifest
        assert "auto-update [bot]" in manifest
        # Centrality ranking and the budgeted semantic pass.
        assert "fan_in * 100 + cycle_bonus * 25" in manifest
        assert "dependencies.metrics.most_depended_on" in manifest
        # Ranking detail and the remainder-backlog artifact format live in
        # the bundled reference file.
        assert "bootstrap-remainder.md" in reference
        assert "WB-<YYYYMMDD>-<4-digit sequence>" in reference
        assert "skipped_no_safe_context" in reference
        assert "## Bootstrap Remainder" in reference

    def test_wiki_bootstrap_skill_documents_external_helper_and_team_contracts(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "wiki-bootstrap"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "prepare-extractors --src-dir <repo> --allow-external-src" in combined
        assert "team check --src-dir <repo> --allow-external-src" in combined
        assert "`--wiki-dir` remains project-root guarded" in combined

    def test_wiki_bootstrap_skill_distinguishes_reference_from_user_docs(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "wiki-bootstrap"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")

        assert "reference-oriented" in manifest
        assert "onboarding-guide" in manifest
        assert "site export --profile user" in manifest


class TestBundledAttackSurfaceSkill:
    def test_attack_surface_skill_is_bundled(self):
        by_id = {skill.skill_id: skill for skill in skills.list_bundled_skills()}
        assert "attack-surface" in by_id
        attack_surface = by_id["attack-surface"]
        assert attack_surface.name == "attack-surface"
        assert "attack surface" in attack_surface.description.lower()
        assert attack_surface.files[0] == "SKILL.md"
        assert "reference.md" in attack_surface.files

    def test_attack_surface_skill_encodes_core_loop_and_guardrails(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "attack-surface"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")

        # Helper preparation and the deep read-only extract.
        assert "llm-wiki prepare-extractors" in manifest
        assert "--deep --read-only" in manifest
        # SECURITY.md seeds the coverage worklist.
        assert "SECURITY.md" in manifest
        # Data-flow gaps are unknown surface, never evidence of safety.
        assert "unknown surface" in manifest
        # The source-level sink scan supplements the bounded flow walk.
        assert "sink scan" in manifest
        # Reconnaissance scope: hand off, no SAST claim, no exploitation.
        assert "SAST" in manifest
        assert "deeper security review" in manifest
        # Boundary/gap taxonomies, sink patterns, and the report format live
        # in the bundled reference file.
        assert "truncated_flow" in reference
        assert "environment_read" in reference
        assert "AS-001" in reference
        assert "attack_surface_<YYYY-MM-DD>.md" in reference
        assert "coverage matrix" in reference

    def test_attack_surface_skill_documents_live_extract_schema_contract(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "attack-surface"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "`entrypoints`" in combined
        assert "`data_flows[].boundaries`" in combined
        assert "`data_flows[].gaps`" in combined
        assert "`data_flows[].truncated`" in combined
        assert "entry_points" not in combined
        assert "summary.entry_points" not in combined

    def test_attack_surface_skill_documents_large_run_and_discovery_contracts(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "attack-surface"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "root `SECURITY.md`" in combined
        assert "root `security-policy.json`" in combined
        assert "`docs/security/**`" in combined
        assert "security ADRs" in combined
        assert "security scanner workflows" in combined
        assert "command log" in combined
        assert "extraction JSON" in combined
        assert "review JSON" in combined
        assert "elapsed time" in combined
        assert "dependency/vendor/build-output" in combined
        assert "docs, tests, generated coverage, caches" in combined
        assert "prepare-extractors --src-dir <repo> --allow-external-src" in combined
        assert "team check --src-dir <repo> --allow-external-src" in combined

    def test_attack_surface_skill_documents_source_reconciliation(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "attack-surface"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"
        normalized = " ".join(combined.split())

        assert (
            "Compare extracted entrypoint categories against source and infrastructure evidence"
            in normalized
        )
        assert "Go `net/http`" in normalized
        assert "Haskell Servant/Warp" in normalized
        assert "uncovered surface" in normalized


class TestBundledDepAuditSkill:
    def test_dep_audit_skill_is_bundled(self):
        by_id = {skill.skill_id: skill for skill in skills.list_bundled_skills()}
        assert "dep-audit" in by_id
        dep_audit = by_id["dep-audit"]
        assert dep_audit.name == "dep-audit"
        assert "dependency" in dep_audit.description.lower()
        assert dep_audit.files[0] == "SKILL.md"
        assert "reference.md" in dep_audit.files

    def test_dep_audit_skill_encodes_triage_workflow(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "dep-audit"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "dependency-cycle" in combined
        assert "undeclared-dependency" in combined
        assert "unused-dependency" in combined
        assert "valid dependency issue" in combined
        assert "documentation-only mismatch" in combined
        assert "source verification" in combined
        assert "llm-wiki lint --strict --profile" in combined
        assert "llm-wiki ci-check" in combined
        assert "No manifest edits without source evidence" in combined


class TestBundledDepVulnTriageSkill:
    def test_dep_vuln_triage_skill_is_bundled(self):
        by_id = {skill.skill_id: skill for skill in skills.list_bundled_skills()}
        assert "dep-vuln-triage" in by_id
        dep_vuln_triage = by_id["dep-vuln-triage"]
        assert dep_vuln_triage.name == "dep-vuln-triage"
        assert "vulnerable" in dep_vuln_triage.description.lower()
        assert dep_vuln_triage.files[0] == "SKILL.md"
        assert "reference.md" in dep_vuln_triage.files

    def test_dep_vuln_triage_skill_encodes_triage_workflow(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "dep-vuln-triage"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        # Deep read-only extract feeds the inventory.
        assert "--deep --read-only" in combined
        # Live payload field names, not invented ones.
        assert "`dependencies.external.<language>`" in combined
        assert "resolved_from" in combined
        # Fail-open version capture means missing versions are unknowns.
        assert "unknown-version" in combined
        assert "never evidence of safety" in combined
        # Advisory lookup contract and datable results.
        assert "OSV" in combined
        assert "lookup date" in combined
        # Reachability classes drive the ranking.
        assert "reachable-from-entrypoint" in combined
        assert "imported-not-traced" in combined
        assert "declared-only" in combined
        assert "test-only" in combined
        # Dogfood-confirmed caveats: test-path false positives and
        # package/import-name mismatches (pyjwt -> jwt) must not be silently
        # trusted.
        assert "test-path exclusion is mandatory" in combined.lower()
        assert "pyjwt" in combined
        assert "jwt" in combined
        # Report artifact and row format.
        assert "DVT-001" in combined
        assert "dep_vuln_triage_<YYYY-MM-DD>.md" in combined
        # Guardrails shared with dep-audit and the security skills.
        assert "no manifest edits without source evidence" in combined.lower()
        assert "never hand-edit lockfiles" in combined.lower()
        assert "dep-audit" in combined

    def test_dep_vuln_triage_skill_documents_external_source_and_scope(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "dep-vuln-triage"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "prepare-extractors --src-dir <repo> --allow-external-src" in combined
        assert "team check --src-dir <repo> --allow-external-src" in combined
        # Haskell versions are never captured; the gap must be explicit.
        assert "Hackage" in combined
        assert "always unknown-version" in combined
        # Defensive scope only.
        assert "locate-and-mitigate" in combined
        assert "no exploit" in combined.lower()


class TestBundledOnboardingGuideSkill:
    def test_onboarding_guide_skill_is_bundled(self):
        by_id = {skill.skill_id: skill for skill in skills.list_bundled_skills()}
        assert "onboarding-guide" in by_id
        onboarding_guide = by_id["onboarding-guide"]
        assert onboarding_guide.name == "onboarding-guide"
        assert "onboarding" in onboarding_guide.description.lower()
        assert onboarding_guide.files[0] == "SKILL.md"
        assert "reference.md" in onboarding_guide.files

    def test_onboarding_guide_skill_encodes_guides_surface_contract(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "onboarding-guide"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        # The first-class agent-owned surface, by its live properties.
        assert "guides/{page_id}.md" in combined
        assert "agent_owned" in combined
        assert "## Guides" in combined
        assert "never rewrites guide bodies" in combined
        # Wiki must exist and be current before narrative is written.
        assert ".llm-wiki-manifest.json" in combined
        assert "wiki-bootstrap" in combined
        assert "Wiki is up to date" in combined
        # Persona defaults and the budgeted pass with explicit remainder.
        assert "contributor" in combined
        assert "operator" in combined
        assert "reviewer" in combined
        assert "bootstrap-remainder.md" in combined
        assert "WB-<YYYYMMDD>-<4-digit sequence>" in combined

    def test_onboarding_guide_skill_encodes_validation_and_commit_contract(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "onboarding-guide"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "lint --strict" in combined
        assert "llm-wiki ci-check" in combined
        assert "docs(wiki): add onboarding guides" in combined
        # Hook-path markers are reserved, not reused.
        assert "LLM_WIKI_AUTO_COMMIT" in combined
        assert "auto-update [bot]" in combined
        # Dogfood-confirmed ordering (2026-07-04): within the final re-link
        # + validate step, sync must run before lint. A new guide page
        # touches no source file, so lint would otherwise report it as
        # orphan_pages before sync has linked it into the index.
        assert "Run `sync` first, not after" in combined
        relink_step = manifest[
            manifest.index("**Re-link, then validate.**") : manifest.index(
                "## Context budget"
            )
        ]
        assert relink_step.index("llm-wiki sync") < relink_step.index("llm-wiki lint")
        # Links must stay lint-checkable.
        assert "Relative links only" in combined
        assert "llm-wiki sync --src-dir . --wiki-dir docs/llm_wiki --jobs 1" in combined
        assert "The supervisor schedules context, sync, lint, CI" in combined
        assert "subagents must not launch them unless explicitly" in combined
        assert "inconclusive until capacity is recovered" in combined
        assert "full deep" in combined
        assert "do not make the scan computationally cheap" in combined

    def test_onboarding_guide_skill_documents_user_profile_prerequisite(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "onboarding-guide"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "publish-docs --profile user" in combined
        assert "product/user reader" in combined
        assert "user-facing workflows" in combined


class TestBundledDocReviewSkill:
    def test_doc_review_skill_is_bundled(self):
        by_id = {skill.skill_id: skill for skill in skills.list_bundled_skills()}
        assert "doc-review" in by_id
        doc_review = by_id["doc-review"]
        assert doc_review.name == "doc-review"
        assert "documentation review" in doc_review.description.lower()
        assert doc_review.files[0] == "SKILL.md"
        assert "reference.md" in doc_review.files

    def test_doc_review_skill_encodes_review_workflow(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "doc-review"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "review JSON" in combined
        assert "branch/diff workflow" in combined
        assert "valid documentation defect" in combined
        assert "stale generated content" in combined
        assert "source-code truth mismatch" in combined
        assert "duplicate finding" in combined
        assert "unresolved finding" in combined
        assert "llm-wiki sync" in combined
        assert "llm-wiki ci-check" in combined

    def test_doc_review_skill_documents_user_docs_quality_findings(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "doc-review"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        for required in [
            "broken distribution-mode link",
            "missing human landing page",
            "missing guide surface",
            "bootstrap placeholder in primary docs",
            "raw generated inventory used as root landing page",
            "published_placeholder",
            "generated_reference_placeholder",
        ]:
            assert required in combined


class TestBundledDocHubSkill:
    def test_doc_hub_skill_is_bundled(self):
        by_id = {skill.skill_id: skill for skill in skills.list_bundled_skills()}
        assert "doc-hub" in by_id
        doc_hub = by_id["doc-hub"]
        assert doc_hub.name == "doc-hub"
        assert "hub" in doc_hub.description.lower()
        assert doc_hub.files[0] == "SKILL.md"
        assert "reference.md" in doc_hub.files

    def test_doc_hub_skill_encodes_pilot_evidence_and_guardrail(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "doc-hub"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        # Live CLI contract, not invented flags.
        assert "site export --wiki-root" in combined
        assert "site check --wiki-root" in combined
        # The pilot-confirmed guardrail: never fabricate a cross-repo
        # relationship when repos are only incidentally co-located.
        assert "do not write an overview page" in combined.lower()
        assert "never fabricate" in combined.lower() or "fabricated" in combined.lower()
        assert "genuinely related" in combined.lower()
        assert "doc_hub_pilot_2026-07-04.md" not in combined
        assert "TeamCrush" not in combined
        assert "Traid" not in combined
        assert "/mnt/data/projects" not in combined
        assert "/tmp/llm-wiki" not in combined
        # Sources are namespaced under out-dir, index.md is generated.
        assert "<source_id>" in combined
        assert "never hand-edit it" in combined.lower()


class TestBundledImpactAnalysisSkill:
    def test_impact_analysis_skill_is_bundled(self):
        by_id = {skill.skill_id: skill for skill in skills.list_bundled_skills()}
        assert "impact-analysis" in by_id
        impact_analysis = by_id["impact-analysis"]
        assert impact_analysis.name == "impact-analysis"
        assert "blast radius" in impact_analysis.description.lower()
        assert impact_analysis.files[0] == "SKILL.md"
        assert "reference.md" in impact_analysis.files

    def test_impact_analysis_skill_encodes_graph_query_contract(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "impact-analysis"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "llm-wiki-context/v1" in combined
        assert "callers" in combined
        assert "callees" in combined
        assert "dependency_neighborhood" in combined
        assert "flow_for_entrypoint" in combined
        assert "pages_for_symbol" in combined
        # dependency_neighborhood is MCP-only through this protocol.
        assert "not exposed through" in combined.lower()
        # Shares doc-review's vocabulary rather than inventing a new one.
        assert "valid documentation defect" in combined
        assert "stale generated content" in combined
        assert "needs human confirmation" in combined
        assert "doc-review" in combined
        # Truncation/ambiguity must be reported, never silently dropped.
        assert "ambiguous" in combined.lower()
        assert "truncated" in combined.lower()


class TestBundledInfraReviewSkill:
    def test_infra_review_skill_is_bundled(self):
        by_id = {skill.skill_id: skill for skill in skills.list_bundled_skills()}
        assert "infra-review" in by_id
        infra_review = by_id["infra-review"]
        assert infra_review.name == "infra-review"
        assert "deployment surface" in infra_review.description.lower()
        assert infra_review.files[0] == "SKILL.md"
        assert "reference.md" in infra_review.files

    def test_infra_review_skill_encodes_generated_field_gaps(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "infra-review"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        # Verified-against-source gaps in the generated pages: these are
        # not captured, and require a raw-source read.
        assert "securityContext" in combined
        assert "hostPath" in combined
        assert "hostNetwork" in combined
        assert "permissions" in combined.lower()
        assert "infrastructure_inventory.py" in combined
        # Docker socket mount is the highest-yield, page-visible finding.
        assert "/var/run/docker.sock" in combined
        # Coverage vs. clean must not be conflated.
        assert (
            "reviewed, clean" in combined.lower() or "zero findings" in combined.lower()
        )


class TestBundledPublishDocsSkill:
    def test_publish_docs_skill_is_bundled(self):
        by_id = {skill.skill_id: skill for skill in skills.list_bundled_skills()}
        assert "publish-docs" in by_id
        publish_docs = by_id["publish-docs"]
        assert publish_docs.name == "publish-docs"
        assert "publish" in publish_docs.description.lower()
        assert publish_docs.files[0] == "SKILL.md"
        assert "reference.md" in publish_docs.files

    def test_publish_docs_skill_encodes_builder_detection_and_deploy_guardrail(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "publish-docs"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "mkdocs build" in combined
        assert "site check" in combined
        # Fails closed: does not install a toolchain on the user's behalf.
        assert "fail" in combined.lower()
        assert "without being asked" in combined.lower()
        # Deploy is a separate, confirmed action, never auto-performed.
        assert "hand off" in combined.lower() or "hand-off" in combined.lower()
        assert "confirm with the user before doing it" in combined.lower()
        # Docusaurus needs an existing app; export alone isn't buildable.
        assert "docusaurus.config.js" in combined

    def test_publish_docs_skill_documents_reference_user_and_distribution_modes(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "publish-docs"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "default export is a reference profile" in combined
        assert "site export --profile user" in combined
        assert "--site-name" in combined
        assert "at least one guide page" in combined
        assert "site check --profile user" in combined
        assert "site check --built-site-dir" in combined
        assert "--link-mode http" in combined
        assert "--file-friendly" in combined
        assert "--link-mode file" in combined


class TestBundledUserDocsAuthorSkill:
    def test_user_docs_author_skill_is_bundled(self):
        by_id = {skill.skill_id: skill for skill in skills.list_bundled_skills()}
        assert "user-docs-author" in by_id
        user_docs_author = by_id["user-docs-author"]
        assert user_docs_author.name == "user-docs-author"
        assert "user docs" in user_docs_author.description.lower()
        assert user_docs_author.files[0] == "SKILL.md"
        assert "reference.md" in user_docs_author.files

    def test_user_docs_author_skill_encodes_deterministic_first_contract(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "user-docs-author"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "deterministic evidence first" in combined
        assert "llm-wiki sync" in combined
        assert "lint --strict" in combined
        assert "site export --profile user" in combined
        assert "site check --profile user" in combined
        assert "site check --built-site-dir" in combined
        assert "--link-mode http" in combined
        assert "--link-mode file" in combined
        assert "llm-wiki sync --src-dir . --wiki-dir docs/llm_wiki --jobs 1" in combined
        assert "The supervisor schedules" in combined
        assert "subagents may inspect bounded pages" in combined
        assert "inconclusive until capacity is recovered" in combined

    def test_user_docs_author_skill_encodes_semantic_authoring_guardrails(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "user-docs-author"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "guides/*.md" in combined
        assert "semantic wiki prose only" in combined
        assert "Do not edit generated blocks" in combined
        assert "Do not edit static-site output" in combined
        assert "Do not invent facts" in combined
        assert "deferred-docs" in combined
        assert "validation-backed issues" in combined


class TestBundledUsageExamplesSkill:
    def test_usage_examples_skill_is_bundled(self):
        by_id = {skill.skill_id: skill for skill in skills.list_bundled_skills()}
        assert "usage-examples" in by_id
        usage_examples = by_id["usage-examples"]
        assert usage_examples.name == "usage-examples"
        assert "usage examples" in usage_examples.description.lower()
        assert "capture" in usage_examples.description.lower()
        assert usage_examples.files[0] == "SKILL.md"
        assert "reference.md" in usage_examples.files

    def test_usage_examples_skill_encodes_capture_contract(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "usage-examples"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "assets/<surface>/<page-stem>/" in combined
        assert "examples are evidence, not decoration" in combined
        assert "capture tooling" in combined
        assert "checked, never installed" in combined
        assert "read-only source" in combined
        assert "disposable" in combined
        assert "alt text" in combined
        assert "caption" in combined
        assert "capture blocker" in combined
        assert "media_link_broken" in combined
        assert "media_missing_alt_text" in combined
        assert "media_oversize" in combined
        assert "site check --built-site-dir" in combined
        assert "--link-mode http" in combined
        assert "--link-mode file" in combined

    def test_usage_examples_skill_is_agent_neutral(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "usage-examples"
        combined = "\n".join(
            [
                (skill_dir / "SKILL.md").read_text(encoding="utf-8"),
                (skill_dir / "reference.md").read_text(encoding="utf-8"),
            ]
        ).lower()

        assert "claude-only" not in combined
        assert "claude code" not in combined
        assert "agent platform" in combined
        assert "llm-wiki site export" in combined


class TestSkillExport:
    def test_export_writes_all_skill_files(self, tmp_path):
        report = skills.export_skills(tmp_path / "out")
        assert report.ok
        assert "wiki-sync" in report.skills
        assert "wiki-bootstrap" in report.skills
        assert "attack-surface" in report.skills
        assert "dep-audit" in report.skills
        assert "dep-vuln-triage" in report.skills
        assert "doc-hub" in report.skills
        assert "doc-review" in report.skills
        assert "impact-analysis" in report.skills
        assert "infra-review" in report.skills
        assert "onboarding-guide" in report.skills
        assert "publish-docs" in report.skills
        assert "usage-examples" in report.skills
        assert "user-docs-author" in report.skills
        assert (tmp_path / "out" / "wiki-sync" / "SKILL.md").is_file()
        assert (tmp_path / "out" / "wiki-sync" / "reference.md").is_file()
        assert (tmp_path / "out" / "wiki-bootstrap" / "SKILL.md").is_file()
        assert (tmp_path / "out" / "wiki-bootstrap" / "reference.md").is_file()
        assert (tmp_path / "out" / "attack-surface" / "SKILL.md").is_file()
        assert (tmp_path / "out" / "attack-surface" / "reference.md").is_file()
        assert (tmp_path / "out" / "dep-audit" / "SKILL.md").is_file()
        assert (tmp_path / "out" / "dep-audit" / "reference.md").is_file()
        assert (tmp_path / "out" / "dep-vuln-triage" / "SKILL.md").is_file()
        assert (tmp_path / "out" / "dep-vuln-triage" / "reference.md").is_file()
        assert (tmp_path / "out" / "doc-hub" / "SKILL.md").is_file()
        assert (tmp_path / "out" / "doc-hub" / "reference.md").is_file()
        assert (tmp_path / "out" / "doc-review" / "SKILL.md").is_file()
        assert (tmp_path / "out" / "doc-review" / "reference.md").is_file()
        assert (tmp_path / "out" / "impact-analysis" / "SKILL.md").is_file()
        assert (tmp_path / "out" / "impact-analysis" / "reference.md").is_file()
        assert (tmp_path / "out" / "infra-review" / "SKILL.md").is_file()
        assert (tmp_path / "out" / "infra-review" / "reference.md").is_file()
        assert (tmp_path / "out" / "onboarding-guide" / "SKILL.md").is_file()
        assert (tmp_path / "out" / "onboarding-guide" / "reference.md").is_file()
        assert (tmp_path / "out" / "publish-docs" / "SKILL.md").is_file()
        assert (tmp_path / "out" / "publish-docs" / "reference.md").is_file()
        assert (tmp_path / "out" / "usage-examples" / "SKILL.md").is_file()
        assert (tmp_path / "out" / "usage-examples" / "reference.md").is_file()
        assert (tmp_path / "out" / "user-docs-author" / "SKILL.md").is_file()
        assert (tmp_path / "out" / "user-docs-author" / "reference.md").is_file()
        assert {op.action for op in report.operations} == {"write"}

    def test_export_is_idempotent(self, tmp_path):
        skills.export_skills(tmp_path / "out")
        report = skills.export_skills(tmp_path / "out")
        assert report.ok
        assert {op.action for op in report.operations} == {"keep"}

    def test_export_preserves_local_edits_without_force(self, tmp_path):
        skills.export_skills(tmp_path / "out")
        target = tmp_path / "out" / "wiki-sync" / "SKILL.md"
        target.write_text("local edit\n", encoding="utf-8")

        report = skills.export_skills(tmp_path / "out")
        assert not report.ok
        assert report.issues[0]["category"] == "existing_file_differs"
        assert target.read_text(encoding="utf-8") == "local edit\n"

    def test_export_force_overwrites_local_edits(self, tmp_path):
        skills.export_skills(tmp_path / "out")
        target = tmp_path / "out" / "wiki-sync" / "SKILL.md"
        target.write_text("local edit\n", encoding="utf-8")

        report = skills.export_skills(tmp_path / "out", force=True)
        assert report.ok
        assert "overwrite" in {op.action for op in report.operations}
        assert "local edit" not in target.read_text(encoding="utf-8")

    def test_export_unknown_skill_rejected(self, tmp_path):
        with pytest.raises(skills.SkillsError, match="Unknown skill 'nope'"):
            skills.export_skills(tmp_path / "out", skills=["nope"])

    def test_export_invalid_destination_rejected(self):
        with pytest.raises(skills.SkillsError, match="Invalid destination"):
            skills.export_skills(".")

    def test_export_from_custom_skills_root(self, tmp_path):
        root = tmp_path / "bundled"
        _write_custom_skill(root)
        (root / "not-a-skill").mkdir()

        listed = skills.list_bundled_skills(root)
        assert [skill.skill_id for skill in listed] == ["demo"]

        report = skills.export_skills(tmp_path / "out", skills_root=root)
        assert report.ok
        assert (tmp_path / "out" / "demo" / "extra.md").is_file()

    def test_empty_skills_root_rejected(self, tmp_path):
        empty = tmp_path / "bundled"
        empty.mkdir()
        with pytest.raises(skills.SkillsError, match="No bundled skills"):
            skills.export_skills(tmp_path / "out", skills_root=empty)


class TestSkillInstall:
    def test_install_defaults_to_claude_skills_dir(self, tmp_path):
        report = skills.install_skills(tmp_path)
        assert report.ok
        assert (tmp_path / ".claude" / "skills" / "wiki-sync" / "SKILL.md").is_file()
        assert (
            tmp_path / ".claude" / "skills" / "wiki-bootstrap" / "SKILL.md"
        ).is_file()
        assert (
            tmp_path / ".claude" / "skills" / "attack-surface" / "SKILL.md"
        ).is_file()
        assert (tmp_path / ".claude" / "skills" / "dep-audit" / "SKILL.md").is_file()
        assert (
            tmp_path / ".claude" / "skills" / "dep-vuln-triage" / "SKILL.md"
        ).is_file()
        assert (tmp_path / ".claude" / "skills" / "doc-hub" / "SKILL.md").is_file()
        assert (tmp_path / ".claude" / "skills" / "doc-review" / "SKILL.md").is_file()
        assert (
            tmp_path / ".claude" / "skills" / "impact-analysis" / "SKILL.md"
        ).is_file()
        assert (tmp_path / ".claude" / "skills" / "infra-review" / "SKILL.md").is_file()
        assert (
            tmp_path / ".claude" / "skills" / "onboarding-guide" / "SKILL.md"
        ).is_file()
        assert (tmp_path / ".claude" / "skills" / "publish-docs" / "SKILL.md").is_file()
        assert (
            tmp_path / ".claude" / "skills" / "usage-examples" / "SKILL.md"
        ).is_file()
        assert (
            tmp_path / ".claude" / "skills" / "user-docs-author" / "SKILL.md"
        ).is_file()


class TestSkillsCli:
    def test_cli_list_json(self, capsys):
        skills_cmd.run(_ns(skills_action="list", format="json"))
        data = json.loads(capsys.readouterr().out)
        assert any(skill["id"] == "wiki-sync" for skill in data["skills"])
        assert any(skill["id"] == "dep-audit" for skill in data["skills"])
        assert any(skill["id"] == "dep-vuln-triage" for skill in data["skills"])
        assert any(skill["id"] == "doc-hub" for skill in data["skills"])
        assert any(skill["id"] == "doc-review" for skill in data["skills"])
        assert any(skill["id"] == "impact-analysis" for skill in data["skills"])
        assert any(skill["id"] == "infra-review" for skill in data["skills"])
        assert any(skill["id"] == "onboarding-guide" for skill in data["skills"])
        assert any(skill["id"] == "publish-docs" for skill in data["skills"])
        assert any(skill["id"] == "usage-examples" for skill in data["skills"])
        assert any(skill["id"] == "user-docs-author" for skill in data["skills"])

    def test_cli_install_and_conflict_exit_code(self, tmp_project, capsys):
        skills_cmd.run(_ns(skills_action="install", format="text"))
        installed = tmp_project / ".claude" / "skills" / "wiki-sync" / "SKILL.md"
        assert installed.is_file()
        assert "WRITE" in capsys.readouterr().out

        installed.write_text("local edit\n", encoding="utf-8")
        with pytest.raises(SystemExit) as excinfo:
            skills_cmd.run(_ns(skills_action="install", format="json"))
        assert excinfo.value.code == 1
        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is False
        assert installed.read_text(encoding="utf-8") == "local edit\n"

    def test_cli_install_rejects_dest_outside_project(
        self, tmp_project, monkeypatch, capsys
    ):
        monkeypatch.setattr(
            "sys.argv",
            ["llm-wiki", "skills", "install", "--dest", "../outside"],
        )
        with pytest.raises(SystemExit) as excinfo:
            cli.main()
        assert excinfo.value.code == 1
        assert "outside the project root" in capsys.readouterr().err

    def test_cli_export_selected_skill(self, tmp_project, monkeypatch, capsys):
        monkeypatch.setattr(
            "sys.argv",
            [
                "llm-wiki",
                "skills",
                "export",
                "--dest",
                "exported",
                "--skill",
                "wiki-sync",
                "--format",
                "json",
            ],
        )
        cli.main()
        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is True
        assert data["skills"] == ["wiki-sync"]
        assert (tmp_project / "exported" / "wiki-sync" / "SKILL.md").is_file()

    def test_cli_help_includes_skills(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["llm-wiki", "skills", "--help"])
        with pytest.raises(SystemExit) as excinfo:
            cli.main()
        assert excinfo.value.code == 0
        out = capsys.readouterr().out
        assert "export" in out
        assert "install" in out
