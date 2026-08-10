"""Contract checks for the bounded managed-reference topic tree."""

from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ROOT = PROJECT_ROOT / "src" / "llm_wiki_cli" / "skills" / "wiki-reference"
TOPICS_ROOT = REFERENCE_ROOT / "references"

TOPIC_HEADINGS = {
    "maintenance.md": "Maintenance and validation",
    "surfaces-naming.md": "Canonical surfaces and naming",
    "repository-handoff.md": "Repository handoff",
    "knowledge-consumption.md": "Qualified knowledge consumption",
    "context-query.md": "Context and query selection",
    "governance.md": "Durable knowledge governance",
    "extractors-dependencies.md": "Extractors and dependencies",
    "publishing.md": "Publishing projections",
    "resources-context.md": "Resource-aware execution",
}

LEGACY_HEADINGS = (
    ("#", "wiki-reference reference"),
    ("##", "Repository-aware Git handoff"),
    ("##", "Extractor helpers and toolchains"),
    ("##", "Haskell extraction contract"),
    ("##", "Python and FastAPI contract extraction"),
    ("##", "Dependency reconciliation"),
    ("##", "Knowledge observations, freshness, and availability"),
    ("###", "Normative native preflight"),
    ("##", "Strict knowledge lint and context ranking"),
    ("##", "Knowledge query, API, and MCP boundaries"),
    ("###", "Typed graph traversal and independent bounds"),
    ("##", "Durable governance, lifecycle, review, and verification"),
    ("##", "JavaScript and TypeScript flows"),
    ("##", "Static-site export"),
    ("###", "Opt-in native metadata for Site and Obsidian"),
    ("##", "Resource-aware execution"),
    ("##", "`llm-wiki context` for large codebases"),
)


def _topic_texts() -> dict[str, str]:
    return {
        name: (TOPICS_ROOT / name).read_text(encoding="utf-8")
        for name in TOPIC_HEADINGS
    }


def _normalized(content: str) -> str:
    return " ".join(content.split())


def test_topic_tree_has_explicit_triggers_and_bounded_scopes() -> None:
    assert {path.name for path in TOPICS_ROOT.glob("*.md")} == set(TOPIC_HEADINGS)

    for name, heading in TOPIC_HEADINGS.items():
        content = (TOPICS_ROOT / name).read_text(encoding="utf-8")
        intro = _normalized(content[:700])
        assert content.startswith(f"# {heading}\n")
        assert "Read this topic" in intro
        assert re.search(
            r"\b(?:does not authorize|never authorizes?)\b",
            intro,
            re.IGNORECASE,
        )


def test_router_links_every_topic_directly_and_documents_install_roots() -> None:
    router = (REFERENCE_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert re.match(
        r"\A---\nname: wiki-reference\ndescription: [^\n]+\n---\n",
        router,
    )

    for name in TOPIC_HEADINGS:
        assert router.count(f"](references/{name})") == 1

    assert "[reference.md](reference.md)" not in router
    assert ".claude/skills/wiki-reference/SKILL.md" in router
    assert ".llm-wiki/skills/wiki-reference/SKILL.md" in router
    assert "compatibility index" in router
    assert "stop only the affected mutation workflow" in _normalized(router)
    assert "read-only" in router


def test_every_local_markdown_link_resolves_inside_the_reference_tree() -> None:
    link_pattern = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")

    for source in REFERENCE_ROOT.rglob("*.md"):
        content = source.read_text(encoding="utf-8")
        for raw_target in link_pattern.findall(content):
            target = raw_target.split("#", 1)[0]
            if not target or "://" in target:
                continue
            resolved = (source.parent / target).resolve()
            assert resolved.is_relative_to(REFERENCE_ROOT.resolve()), (
                source,
                raw_target,
            )
            assert resolved.is_file(), (source, raw_target)


def test_compatibility_index_preserves_legacy_anchors_as_redirects() -> None:
    compatibility = (REFERENCE_ROOT / "reference.md").read_text(encoding="utf-8")
    headings = tuple(
        (marks, heading)
        for marks, heading in re.findall(r"^(#{1,3}) (.+)$", compatibility, re.M)
    )
    assert headings == LEGACY_HEADINGS

    matches = list(re.finditer(r"^(#{2,3}) .+$", compatibility, re.M))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else None
        redirect = compatibility[match.end() : end]
        assert re.search(r"\[[^]]+\]\(references/[^)]+\.md\)", redirect)
        assert len(redirect.split()) <= 60


def test_compatibility_index_stays_bounded_and_policy_free() -> None:
    compatibility = (REFERENCE_ROOT / "reference.md").read_text(encoding="utf-8")
    assert len(compatibility.splitlines()) <= 100
    assert len(compatibility.split()) <= 500
    assert "```" not in compatibility
    assert "| ---" not in compatibility
    assert "preserves legacy headings and does not restate their contracts" in (
        _normalized(compatibility)
    )


def test_full_rule_sentinels_have_one_topic_owner() -> None:
    texts = _topic_texts()
    owners = {
        "repository-handoff.md": "git check-ignore --no-index",
        "extractors-dependencies.md": "llm-wiki prepare-extractors",
        "knowledge-consumption.md": "knowledge-result-exceeds-size-limit",
        "context-query.md": "full_inventory_performed",
        "governance.md": "llm-wiki knowledge move",
        "publishing.md": "llm-wiki site export",
        "resources-context.md": "requested_jobs",
        "surfaces-naming.md": "Entity pages must have:",
        "maintenance.md": "final owning sync",
    }

    for expected_owner, sentinel in owners.items():
        found_in = {name for name, content in texts.items() if sentinel in content}
        assert found_in == {expected_owner}, sentinel


def test_knowledge_contract_covers_qualification_and_uncertainty() -> None:
    knowledge = _topic_texts()["knowledge-consumption.md"]
    context = _topic_texts()["context-query.md"]

    for term in (
        "`ready`",
        "`absent`",
        "`degraded`",
        "`unsupported`",
        "policy-selected-surface-only-fallback-after-invalid",
        "policy-selected-surface-only-fallback-after-mixed-snapshot",
        "manifest-version-unsupported",
        "surface-schema-version-unsupported",
        "knowledge-basis-incompatible",
        "knowledge-snapshot-only",
        "knowledge-source-changed",
        "knowledge-results-truncated",
        "ambiguous",
        "unresolved",
        "analyzer coverage",
        "independently-validated-surface",
        "found: false",
        "dedicated-query reason `all-projection-commitments-match`",
    ):
        assert term in knowledge

    assert "resolved, ambiguous, external, and unresolved" in knowledge.lower()
    assert "live comparison" in knowledge
    assert "raw projection JSON" not in knowledge
    assert "not the normal consumer interface" in _normalized(knowledge)
    assert "inert data" in knowledge
    for mode in ("`off`", "`auto`", "`required`"):
        assert mode in context
    assert "`prefer_fresh` is independent" in context
    assert "`cost.full_inventory_performed`" in context
    normalized_context = _normalized(context)
    assert "Each current dedicated MCP knowledge-tool call" in normalized_context
    assert "performs a full inventory" in normalized_context
    assert "`knowledge_selection.unfiltered_total`" in context
    assert "`bounds.files`" in context
    assert "top-level context `truncated`" in context
    assert "Reviewer/event detail" in context
    assert "`bounds.results`" in context


def test_surface_catalog_and_optional_initialization_routes_are_complete() -> None:
    texts = _topic_texts()
    surfaces = texts["surfaces-naming.md"]
    extractors = texts["extractors-dependencies.md"]

    assert "`assets/<surface>/<page-stem>/<name>.<ext>`" in surfaces
    assert "separately installed `usage-examples` workflow" in surfaces
    assert "llm-wiki bootstrap --api-contracts" in extractors
    assert "llm-wiki sync --initialize-surfaces api-contracts --dry-run" in (
        extractors
    )
    assert "repeat the same command without `--dry-run`" in extractors
    assert "repeatable `--flow-category`" in extractors
    assert "`--exclude-tests`" in extractors
    assert "ordinary entity/module changes are deferred" in extractors


def test_maintenance_contract_orders_owning_sync_before_validation() -> None:
    maintenance = _topic_texts()["maintenance.md"]
    normalized = _normalized(maintenance)
    ordered_markers = (
        "1. Run the deterministic owning pass",
        "3. Classify each affected page",
        "5. After the last canonical Markdown edit",
        "6. Strict validation follows",
        "7. Report expired human-section reviews",
    )
    positions = [maintenance.index(marker) for marker in ordered_markers]
    assert positions == sorted(positions)

    for required in (
        "**Never skip the update** — a stale wiki defeats the purpose of the system.",
        "**seed a baseline manifest** from the current source state without modifying pages",
        "Skip the second sync only when no canonical Markdown changed.",
        "If sync repairs only the manifest (its stored hashes were invalid, and no pages were modified), run the same sync command again before linting.",
        "pass the same external `--src-dir` with `--allow-external-src` to `sync`, `lint`, and `ci-check`",
        "Do not fabricate replacement human reviews or receipts.",
        "Never leave the wiki in a state where lint reports errors.",
        "does not depend on that optional workflow",
    ):
        assert required in normalized

    assert "llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki" in normalized
    assert "llm-wiki lint --strict --jobs 1" in normalized
    assert "llm-wiki ci-check --jobs 1" in normalized


def test_reference_contract_does_not_invent_cli_query_or_automatic_adoption() -> None:
    texts = _topic_texts()
    combined = "\n".join(texts.values())
    context = texts["context-query.md"]
    governance = texts["governance.md"]
    maintenance = texts["maintenance.md"]

    assert "There is no CLI `query_documentation` subcommand." in context
    assert not re.search(r"\bllm-wiki\s+query_documentation\b", combined)

    init_owners = {
        name for name, content in texts.items() if "llm-wiki knowledge init" in content
    }
    assert init_owners == {"governance.md"}
    assert "explicitly asks to adopt" in governance
    assert "never initialize governance" in governance
    assert "Never run `knowledge init` as recovery." in maintenance

    planning_marker = re.compile(
        r"\b(?:epic|milestone|phase)\b|\b(?:FND|REF|KNW|PRV)-\d+\b",
        re.IGNORECASE,
    )
    assert not planning_marker.search(combined)
