"""Regression coverage for the bounded wiki-sync entry workflow."""

from __future__ import annotations

from pathlib import Path

from llm_wiki_cli.services import skills


SYNC_ROOT = skills.BUNDLED_SKILLS_ROOT / "wiki-sync"
REFERENCE_ROOT = skills.BUNDLED_SKILLS_ROOT / "wiki-reference" / "references"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _topic(name: str) -> str:
    return _text(REFERENCE_ROOT / name)


def _squash(value: str) -> str:
    return " ".join(value.split())


def test_wiki_sync_entry_is_bounded_and_keeps_the_complete_routine_loop() -> None:
    manifest_path = SYNC_ROOT / "SKILL.md"
    manifest = _text(manifest_path)

    assert len(manifest.encode("utf-8")) <= 8_000
    assert len(manifest.splitlines()) <= 150
    assert "after a relevant code" in manifest
    assert "before delivery" in manifest

    ordered = [
        "**Run the deterministic owning pass.**",
        "**Build and classify the changed-page worklist.**",
        "**Edit semantic surfaces only.**",
        "**Append the semantic log line.**",
        "**Run the final owning sync/re-anchor, then verify.**",
        "**Review and hand off under the selected contract.**",
    ]
    positions = [manifest.index(marker) for marker in ordered]
    assert positions == sorted(positions)
    assert manifest.count("llm-wiki sync --jobs 1") == 2
    assert "llm-wiki lint --strict" in manifest
    assert "llm-wiki ci-check" in manifest
    assert "no canonical Markdown change" in manifest

    # Specialized mechanics belong to direct managed topics, not this entry.
    for duplicated_detail in (
        "## Governed rename preflight and owner handoff",
        "llm-wiki knowledge move",
        "--initialize-surfaces",
        "--openapi-file",
        "50-file/30-percent",
        "git add <wiki-dir>/",
        "| Result | Delivery state |",
    ):
        assert duplicated_detail not in manifest


def test_wiki_sync_routes_every_specialized_concern_to_exact_managed_topics() -> None:
    manifest = _text(SYNC_ROOT / "SKILL.md")
    routed_topics = {
        "maintenance.md",
        "surfaces-naming.md",
        "governance.md",
        "extractors-dependencies.md",
        "knowledge-consumption.md",
        "repository-handoff.md",
        "resources-context.md",
        "context-query.md",
    }

    assert skills.SKILL_DEPENDENCIES["wiki-sync"] == (
        skills.REFERENCE_SKILL_ID,
    )
    for topic in routed_topics:
        claude_route = f".claude/skills/wiki-reference/references/{topic}"
        generic_route = f".llm-wiki/skills/wiki-reference/references/{topic}"
        assert claude_route in manifest
        assert generic_route in manifest
        assert manifest.count(f"wiki-reference/references/{topic}") == 2
        assert (REFERENCE_ROOT / topic).is_file()

    assert "[reference.md](reference.md)" not in manifest
    assert "do not fall back to a missing local summary" in manifest
    assert "stop the affected mutation" in manifest


def test_surface_and_infrastructure_exceptions_live_in_extractor_topic() -> None:
    topic = _squash(_topic("extractors-dependencies.md"))

    for command in (
        "llm-wiki sync --initialize-surfaces flows,dependencies ",
        "llm-wiki sync --initialize-surfaces api-contracts --openapi-file openapi.yaml ",
        "--clear-openapi-file",
    ):
        assert command in topic
    for contract in (
        "ordinary entity/module source changes",
        "more than 50 pages (creates plus policy-pruned removals) or more than 30 percent",
        "path, SHA-256, and format",
        "Docker, Compose,",
        "Kubernetes, GitHub Actions",
        "separate 50-file/30-percent broad-change guard",
        "source-content hash and normalized observation hash",
        "`source-missing` tombstone",
        "Only infrastructure `## Notes` is semantic",
    ):
        assert contract in topic


def test_semantic_boundary_topic_retains_recognized_placeholder_triggers() -> None:
    topic = _topic("surfaces-naming.md")

    assert "recognized placeholder" in topic
    assert "bare `—`" in topic
    assert "bare `-`" in topic
    assert "`_Auto-generated from ..._`" in topic


def test_extended_validation_and_handoff_live_in_their_direct_topics() -> None:
    maintenance = _squash(_topic("maintenance.md"))
    handoff = _squash(_topic("repository-handoff.md"))

    for contract in (
        "llm-wiki lint --strict --profile --jobs 1",
        "llm-wiki ci-check --format json --jobs 1",
        "llm-wiki team check --src-dir .",
        "llm-wiki team check --src-dir <repo> --allow-external-src",
        "`--strict` additionally requires `index.md`, `log.md`, `entities/`",
        "`modules/`, `workflows/`, `infrastructure/`",
        "a present, valid, fresh sync manifest",
        "`team resolve-conflicts` only auto-resolves generated-page conflicts",
        "more than 50 files or more than 30 percent of tracked sources",
        "repeat the final owning sync first whenever a fix changes canonical Markdown",
        "expired human-section reviews and stale machine-verification",
        "llm-wiki trigger-agent",
        "`--force` does not bypass the lock or breaker",
    ):
        assert contract in maintenance

    for contract in (
        "| Result | Delivery state | Permitted handoff |",
        "| Delivery state | Review evidence before handoff | Result |",
        "git add <wiki-dir>/",
        'git commit -m "docs(wiki): <short description of what changed and why>"',
        "An empty Git diff proves nothing about ignored files",
        "Never stage a partial native snapshot",
        "never require or mutate target Git state",
        "Never reuse the hook's literal",
        "`auto-update [bot]`",
    ):
        assert contract in handoff


def test_legacy_companion_is_small_and_cannot_shadow_managed_contracts() -> None:
    companion_path = SYNC_ROOT / "reference.md"
    companion = _text(companion_path)

    assert len(companion.encode("utf-8")) <= 2_000
    assert "compatibility reference" in companion
    assert "cannot substitute for a missing or modified dependency" in companion
    assert "not an active route" in companion
    for forbidden_heading in (
        "## Governed rename decision table",
        "## Validation loop details",
        "## Semantic-only edit guardrail",
        "## Failure modes and edge cases",
    ):
        assert forbidden_heading not in companion
