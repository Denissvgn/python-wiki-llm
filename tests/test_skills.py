"""Tests for bundled agent skill listing, export, and installation."""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import skills_cmd
from llm_wiki_cli.services import skills


_CUSTOM_SKILL_MANIFEST_LF = (
    b"---\nname: demo\ndescription: A demo skill.\n---\n\n# demo\n"
)
_CUSTOM_SKILL_EXTRA_LF = b"# extra\n"


def _ns(**kwargs):
    return types.SimpleNamespace(**kwargs)


def _write_custom_skill(root: Path, skill_id: str = "demo") -> Path:
    skill_dir = root / skill_id
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_bytes(_CUSTOM_SKILL_MANIFEST_LF)
    (skill_dir / "extra.md").write_bytes(_CUSTOM_SKILL_EXTRA_LF)
    return skill_dir


class TestBundledAgentDocsSkill:
    def test_agent_docs_skill_is_bundled(self):
        by_id = {skill.skill_id: skill for skill in skills.list_bundled_skills()}
        assert "agent-docs" in by_id
        agent_docs = by_id["agent-docs"]
        assert agent_docs.name == "agent-docs"
        assert "external workspace" in agent_docs.description.lower()
        assert "existing llm wiki" in agent_docs.description.lower()
        assert agent_docs.files == ("SKILL.md", "reference.md")

    def test_agent_docs_orders_intake_baseline_packets_review_and_handoff(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "agent-docs"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        ordered_markers = [
            "**Record the intake exactly once.**",
            "**Prepare one baseline.**",
            "**Verify the baseline gate.**",
            "**Run wiki enrichment from an explicit packet.**",
            "**Run the user-docs packet in order.**",
            "**Run an auditable review packet.**",
            "**Verify and hand off locally.**",
        ]
        positions = [manifest.index(marker) for marker in ordered_markers]
        assert positions == sorted(positions)

        assert "`bootstrap-source` or `existing-wiki`" in combined
        assert "never re-ask" in combined
        assert "`unspecified`" in combined
        assert "trusted human intent" in combined
        assert "untrusted evidence" in combined
        assert "wiki-semantic-enhance" in combined
        assert "llm-wiki-documentation-semantic-readiness/v1" in combined
        assert "llm-wiki-documentation-agent-result/v1" in combined
        assert "worker and reviewer packets/results" in combined
        assert "provider-neutral" in combined
        assert "do not add a provider SDK" in combined
        assert "`generic-agent`" in combined
        assert "`handoff`" in combined
        assert "`low-cost`" in combined
        assert "Anthropic" in combined
        assert "Google Gemini" in combined
        assert "local/self-hosted" in combined
        assert "none is the protocol default" in combined

    def test_agent_docs_encodes_isolation_resume_and_heavy_gate_contracts(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "agent-docs"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"
        normalized = " ".join(combined.split())

        assert "external_agent_docs" in combined
        assert "`.llm-wiki-docs/run.json`" in combined
        assert "source and input wiki as read-only evidence" in combined
        assert "AGENTS.md" in combined
        assert "CLAUDE.md" in combined
        assert "auto-discovered" in combined
        assert "Never put credentials" in combined
        assert "source_unavailable" in combined
        assert "source_identity_unknown" in combined
        assert "Run one heavy gate at a time" in combined
        assert "Use `--jobs 1`" in combined
        assert "mark unfinished checks inconclusive" in combined
        assert "Three repeated unresolved high-severity failures block" in combined
        assert "do not deploy, stage, or commit the source" in combined
        assert "supervisor-only write control" in normalized
        assert "one bounded result handoff" in normalized
        assert "not a cryptographic boundary" in normalized
        assert "shares the supervisor's principal" in normalized
        assert "same boundary to every provider and runner" in normalized
        assert "llm-wiki docs calibration" in combined
        assert "digest-pinned" in combined
        assert "separately authenticated host broker" in combined
        assert "`candidate_evaluated=true`" in combined
        assert "`INTAKE_FROZEN`" in combined
        assert "use_p0_calibration_host_broker_authenticator" in combined


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
        assert "dependency_evidence.most_depended_on" in manifest
        # Ranking detail and the remainder-backlog artifact format live in
        # the bundled reference file.
        assert "bootstrap-remainder.md" in reference
        assert "WB-<YYYYMMDD>-<4-digit sequence>" in reference
        assert "skipped_no_safe_context" in reference
        assert "## Bootstrap Remainder" in reference

    def test_wiki_bootstrap_is_permanently_first_use_only(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "wiki-bootstrap"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "Use only for first-time wiki creation" in manifest
        assert "llm-wiki migrate --dry-run" in combined
        assert "phrase 're-bootstrap' never authorizes replacement" in combined
        assert "bootstrap deliberately has no public existing-target mode" in manifest
        assert "intentional full re-bootstrap" not in combined
        assert "unless the request explicitly says to re-bootstrap" not in combined

    def test_adjacent_skills_never_route_existing_wikis_to_bootstrap_repair(self):
        for skill_id in ("onboarding-guide", "usage-examples", "publish-docs"):
            manifest = (
                skills.BUNDLED_SKILLS_ROOT / skill_id / "SKILL.md"
            ).read_text(encoding="utf-8")
            normalized = " ".join(manifest.split())

            assert "bootstrap is never an existing-wiki repair path" in normalized
            assert "llm-wiki migrate --dry-run" in normalized
            assert "exact untouched `llm-wiki init` scaffold" in normalized

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

    def test_wiki_bootstrap_uses_live_surface_name_and_external_handoff(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "wiki-bootstrap"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert ".llm-wiki-surface.json" in manifest
        assert ".llm-wiki-surface-index.json" not in combined
        assert "external_agent_docs" in combined
        assert "wiki-semantic-enhance" in combined
        assert "never stage or commit the source or adopted input wiki" in combined

    def test_infrastructure_ownership_is_consistent_across_authoring_skills(self):
        bootstrap = "\n".join(
            (
                (
                    skills.BUNDLED_SKILLS_ROOT / "wiki-bootstrap" / "SKILL.md"
                ).read_text(encoding="utf-8"),
                (
                    skills.BUNDLED_SKILLS_ROOT / "wiki-bootstrap" / "reference.md"
                ).read_text(encoding="utf-8"),
            )
        )
        semantic = (
            skills.BUNDLED_SKILLS_ROOT
            / "wiki-semantic-enhance"
            / "reference.md"
        ).read_text(encoding="utf-8")
        user_docs = (
            skills.BUNDLED_SKILLS_ROOT / "user-docs-author" / "reference.md"
        ).read_text(encoding="utf-8")

        assert "ordinary sync regenerates them incrementally" in bootstrap
        assert "Infrastructure `## Notes`" in bootstrap
        assert "| Infrastructure `## Notes` | Yes |" in semantic
        assert "matches a live freshness evaluation" in user_docs
        assert "bootstrap snapshots, not supported semantic" not in bootstrap
        assert "have no agent-owned `## Notes`" not in bootstrap
        assert "current raw source" in bootstrap


class TestBundledWikiSemanticEnhanceSkill:
    def test_wiki_semantic_enhance_skill_is_bundled(self):
        by_id = {skill.skill_id: skill for skill in skills.list_bundled_skills()}
        assert "wiki-semantic-enhance" in by_id
        semantic = by_id["wiki-semantic-enhance"]
        assert semantic.name == "wiki-semantic-enhance"
        assert "semantic-enrichment" in semantic.description.lower()
        assert semantic.files == ("SKILL.md", "reference.md")

    def test_wiki_semantic_enhance_encodes_readiness_and_ownership(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "wiki-semantic-enhance"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "freshly bootstrapped source baseline" in manifest
        assert "validated snapshot of an existing LLM Wiki" in manifest
        assert "`candidate_reuse`" in combined
        assert "`needs_grounding`" in combined
        assert "`needs_enhancement`" in combined
        assert "`incompatible`" in combined
        assert "do not rewrite merely for style" in combined
        assert "`wiki-bootstrap/reference.md`" in combined
        assert "do not invent a parallel" in combined
        assert "llm-wiki-documentation-semantic-readiness/v1" in combined
        assert "every P0" in combined
        assert "declared P1 budget" in combined
        assert "ready_for_user_docs" in combined
        assert "generator defects" in combined
        assert "Never edit generated tables" in combined
        assert "source or adopted input wiki" in combined

    def test_wiki_semantic_enhance_supports_resume_and_wiki_only_limits(self):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "wiki-semantic-enhance"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = f"{manifest}\n{reference}"

        assert "source is optional" in combined.lower()
        assert "wiki-only run resumes from its recorded snapshot" in combined
        assert "cannot upgrade an imported claim to" in combined
        assert "source-verified" in combined
        assert "Same source/snapshot and packet hashes" in combined
        assert "Resume open ids" in combined
        assert "Run one heavy gate at a time" in combined
        assert "Semantic budget exhausted" in combined
        assert (
            "Never write, stage, or commit the source or adopted input wiki" in combined
        )


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
        assert "`data_flow_details`" in combined
        assert "llm-wiki-extract-data-flow-details/v1" in combined
        assert "`observed`, `emitted`, `omitted`" in combined
        assert "`not_evaluated`" in combined
        assert "`unsupported`" in combined
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
        assert "`dependencies.version_details`" in combined
        assert "llm-wiki-dependency-version-details/v1" in combined
        assert "`selection_confidence`" in combined
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
        assert "navigation guides" in onboarding_guide.description.lower()
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
        assert "docs(wiki): add navigation guides" in combined
        assert "guides/<persona>-navigation.md" in combined
        assert "# <Persona> navigation guide" in combined
        assert "docs(wiki): add onboarding guides" not in combined
        assert "guides/<persona>-onboarding.md" not in combined
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
        assert "--format docusaurus" in combined
        assert ".llm-wiki-site-selection.json" in combined
        assert "ordered normalized" in combined
        # There is no durable authored hub input/navigation/check surface.
        assert "no canonical hub-overview input" in combined.lower()
        assert "do not author a hub overview in derived output" in combined.lower()
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

    def test_impact_analysis_is_native_qualified_with_labeled_legacy_supplement(
        self,
    ):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / "impact-analysis"
        manifest = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
        combined = " ".join(f"{manifest}\n{reference}".split())

        for required in (
            "get_concept",
            "traverse_typed_graph",
            "explain_evidence",
            "freshness_evaluated",
            "lifecycle",
            "successor",
            "include_evidence=false",
            "resolved",
            "ambiguous",
            "external",
            "unresolved",
            "typed_graph.coverage",
            "bounds.edges",
            "legacy live supplement",
            "semantic section",
        ):
            assert required.lower() in combined.lower()
        assert (
            "A non-truncated query is not a complete neighborhood when analyzer "
            "coverage is truncated"
        ) in combined
        assert "must not overwrite a native limitation" in combined
        assert "Do not copy raw detailed evidence into public output" in combined

    def test_impact_analysis_reuses_one_service_for_native_query_sequence(self):
        reference = (
            skills.BUNDLED_SKILLS_ROOT / "impact-analysis" / "reference.md"
        ).read_text(encoding="utf-8")
        example = reference[
            reference.index("```python") + len("```python") :
            reference.index("```", reference.index("```python") + len("```python"))
        ]

        assert example.count("build_documentation_query_service(") == 1
        for wrapper in (
            "get_concept(",
            "traverse_typed_graph(",
            "explain_evidence(",
        ):
            assert wrapper in example
        assert example.count("service=service") == 3

    @pytest.mark.parametrize(
        ("row", "required"),
        [
            ("| `ready` + typed graph `ready` |", "analyzer bounds"),
            (
                "| `ready` + `typed-graph-extension-not-present` |",
                "no typed-neighborhood conclusion",
            ),
            ("| `absent` (`knowledge-projection-not-present`) |", "legacy live"),
            ("| `degraded`, `unsupported`, invalid, or mixed snapshot |", "no rejected"),
            ("| Ambiguous exact identity or persisted alias |", "owner choice"),
            ("| `ready` with `freshness_evaluated: false` |", "snapshot-only"),
        ],
    )
    def test_impact_analysis_fallback_table_preserves_native_limitations(
        self,
        row,
        required,
    ):
        reference = (
            skills.BUNDLED_SKILLS_ROOT / "impact-analysis" / "reference.md"
        ).read_text(encoding="utf-8")
        selected = next(
            line for line in reference.splitlines() if line.startswith(row)
        )

        assert required in selected
        assert (
            "Legacy detail can increase the known blast radius, but it cannot "
            "erase native"
        ) in reference


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
        assert "--format mkdocs" in combined
        assert "--built-site-dir" in combined
        assert "--link-mode http" in combined
        assert "--file-friendly" in combined
        assert "--link-mode file" in combined
        assert ".llm-wiki-site-selection.json" in combined
        assert "llm-wiki-site-selection.json" in combined
        assert (
            "cp site/llm-wiki-site-selection.json "
            "build/llm-wiki-site-selection.json"
        ) in combined
        assert "_site-http" in combined
        assert "_site-file" in combined

    def test_publish_docs_direct_file_sequence_rebuilds_before_file_check(self):
        manifest = (skills.BUNDLED_SKILLS_ROOT / "publish-docs" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        start = manifest.index("Direct-file handoffs use")
        end = manifest.index("5. **Hand off", start)
        direct = manifest[start:end]

        export = direct.index("llm-wiki site export")
        file_friendly = direct.index("--file-friendly", export)
        mirror_check = direct.index("llm-wiki site check", file_friendly)
        rebuild = direct.index("mkdocs build --strict", mirror_check)
        built_check = direct.index("--built-site-dir _site", rebuild)
        file_check = direct.index("--link-mode file", built_check)
        assert (
            export < file_friendly < mirror_check < rebuild < built_check < file_check
        )


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

    def test_user_docs_author_direct_file_handoff_is_complete_and_ordered(self):
        manifest = (
            skills.BUNDLED_SKILLS_ROOT / "user-docs-author" / "SKILL.md"
        ).read_text(encoding="utf-8")
        start = manifest.index("# For direct-file handoff")
        end = manifest.index("6. **Run the adjustment loop", start)
        direct = manifest[start:end]

        export = direct.index("llm-wiki site export")
        file_friendly = direct.index("--file-friendly", export)
        mirror_check = direct.index("llm-wiki site check", file_friendly)
        rebuild = direct.index("mkdocs build --strict", mirror_check)
        built_check = direct.index("--built-site-dir _site", rebuild)
        file_check = direct.index("--link-mode file", built_check)
        assert (
            export < file_friendly < mirror_check < rebuild < built_check < file_check
        )

        reference = (
            skills.BUNDLED_SKILLS_ROOT / "user-docs-author" / "reference.md"
        ).read_text(encoding="utf-8")
        assert "`site-user-http` and `_site-user-http`" in reference
        assert "`site-user-file`" in reference
        assert "mismatched marker" in reference


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
        assert (
            "a row added to canonical wiki Markdown is a semantic edit" in combined
        )
        assert "restart at the step 5 owning sync/re-anchor" in combined
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

    def test_usage_examples_rebuilds_after_media_changes_before_built_checks(self):
        manifest = (
            skills.BUNDLED_SKILLS_ROOT / "usage-examples" / "SKILL.md"
        ).read_text(encoding="utf-8")
        start = manifest.index("5. **Validate and adjust.**")
        end = manifest.index("6. **Defer honestly.**", start)
        validation = manifest[start:end]

        first_export = validation.index("llm-wiki site export")
        first_mirror_check = validation.index("llm-wiki site check", first_export)
        first_rebuild = validation.index("mkdocs build --strict", first_mirror_check)
        http_built_check = validation.index("--built-site-dir _site", first_rebuild)
        assert first_export < first_mirror_check < first_rebuild < http_built_check

        file_export = validation.index("llm-wiki site export", http_built_check)
        file_friendly = validation.index("--file-friendly", file_export)
        file_mirror_check = validation.index("llm-wiki site check", file_friendly)
        second_rebuild = validation.index("mkdocs build --strict", file_mirror_check)
        file_built_check = validation.index("--built-site-dir _site", second_rebuild)
        file_mode = validation.index("--link-mode file", file_built_check)
        assert (
            file_export
            < file_friendly
            < file_mirror_check
            < second_rebuild
            < file_built_check
            < file_mode
        )


class TestExternalDocumentationSkillChain:
    @staticmethod
    def _combined(skill_id: str) -> str:
        skill_dir = skills.BUNDLED_SKILLS_ROOT / skill_id
        return "\n".join(
            [
                (skill_dir / "SKILL.md").read_text(encoding="utf-8"),
                (skill_dir / "reference.md").read_text(encoding="utf-8"),
            ]
        )

    def test_existing_skills_preserve_managed_defaults_and_add_external_gates(self):
        bootstrap = self._combined("wiki-bootstrap")
        sync = self._combined("wiki-sync")
        onboarding = self._combined("onboarding-guide")

        assert "Managed knowledge-base behavior remains the default" in bootstrap
        assert "docs(wiki): bootstrap <project>" in bootstrap
        assert "external_agent_docs" in bootstrap
        assert "wiki-semantic-enhance" in bootstrap

        assert "Commit wiki changes separately" in sync
        assert "external_agent_docs" in sync
        assert "resume from the recorded wiki snapshot" in sync
        assert "never stage or commit the source or" in sync

        assert "docs(wiki): add navigation guides" in onboarding
        assert "recorded audiences and per-audience intent" in onboarding
        assert "Never re-ask intake on resume" in onboarding
        assert "wiki-only runs" in onboarding.lower()
        assert "never stage or commit the source or input wiki" in onboarding

    def test_user_capture_review_and_publish_external_entry_exit_contracts(self):
        author = self._combined("user-docs-author")
        capture = self._combined("usage-examples")
        review = self._combined("doc-review")
        publish = self._combined("publish-docs")

        assert "semantic-readiness ledger has passed" in author
        assert "one-time recorded intake" in author
        assert "Wiki-only runs" in author
        assert "unverified imported claims" in author
        assert "return normalized deferrals" in author

        assert "capture is optional and separately authorized" in capture
        assert "already-running caller-owned staging/demo service" in capture
        assert "untrusted evidence" in capture
        assert "Missing tooling, browser/runtime access, or authorization" in capture

        assert "Keep reviewer and worker packets/results separately auditable" in review
        assert "No finding may disappear" in review
        assert "three repeated unresolved high-severity failures block" in review
        assert "independent supervisor reconciliation" in review

        assert "semantic readiness" in publish
        assert "separate review ledger/result" in publish
        assert "`publish_ready` is not" in publish
        assert "deployment remains separately authorized" in publish


class TestSkillExport:
    def test_export_writes_all_skill_files(self, tmp_path):
        report = skills.export_skills(tmp_path / "out")
        assert report.ok
        assert "agent-docs" in report.skills
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
        assert "wiki-semantic-enhance" in report.skills
        assert (tmp_path / "out" / "agent-docs" / "SKILL.md").is_file()
        assert (tmp_path / "out" / "agent-docs" / "reference.md").is_file()
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
        assert (tmp_path / "out" / "wiki-semantic-enhance" / "SKILL.md").is_file()
        assert (tmp_path / "out" / "wiki-semantic-enhance" / "reference.md").is_file()
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

    def test_export_force_canonicalizes_semantically_equal_crlf(self, tmp_path):
        root = tmp_path / "bundled"
        _write_custom_skill(root)
        destination = tmp_path / "out"
        skills.export_skills(destination, skills_root=root)
        target = destination / "demo" / "SKILL.md"
        canonical_bytes = target.read_bytes()
        crlf_bytes = canonical_bytes.replace(b"\n", b"\r\n")
        target.write_bytes(crlf_bytes)

        preserved = skills.export_skills(destination, skills_root=root)

        assert preserved.ok
        assert target.read_bytes() == crlf_bytes
        assert (
            next(
                operation.action
                for operation in preserved.operations
                if Path(operation.path) == target
            )
            == "keep"
        )

        refreshed = skills.export_skills(destination, skills_root=root, force=True)

        assert refreshed.ok
        assert target.read_bytes() == canonical_bytes
        assert (
            next(
                operation.action
                for operation in refreshed.operations
                if Path(operation.path) == target
            )
            == "overwrite"
        )

    def test_export_normalizes_crlf_bundled_source(self, tmp_path):
        root = tmp_path / "bundled"
        skill_dir = _write_custom_skill(root)
        source = skill_dir / "SKILL.md"
        source.write_bytes(_CUSTOM_SKILL_MANIFEST_LF.replace(b"\n", b"\r\n"))

        report = skills.export_skills(tmp_path / "out", skills_root=root)

        assert report.ok
        exported = (tmp_path / "out" / "demo" / "SKILL.md").read_bytes()
        assert b"\r" not in exported
        assert exported == _CUSTOM_SKILL_MANIFEST_LF

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
        assert (tmp_path / ".claude" / "skills" / "agent-docs" / "SKILL.md").is_file()
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
        assert (
            tmp_path / ".claude" / "skills" / "wiki-semantic-enhance" / "SKILL.md"
        ).is_file()


class TestSkillsCli:
    def test_cli_list_json(self, capsys):
        skills_cmd.run(_ns(skills_action="list", format="json"))
        data = json.loads(capsys.readouterr().out)
        assert any(skill["id"] == "agent-docs" for skill in data["skills"])
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
        assert any(skill["id"] == "wiki-semantic-enhance" for skill in data["skills"])

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
