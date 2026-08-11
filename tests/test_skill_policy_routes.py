"""Portable routing and metadata contracts for bundled workflow skills."""

from __future__ import annotations

import pytest

from llm_wiki_cli.services import skills


CLAUDE_TOPIC_ROOT = ".claude/skills/wiki-reference/references"
GENERIC_TOPIC_ROOT = ".llm-wiki/skills/wiki-reference/references"
DESCRIPTION_WORD_BASELINE = 545
DESCRIPTION_WORD_RANGE = range(25, 41)

EXPECTED_COMMON_ROUTES: dict[str, frozenset[str]] = {
    "agent-docs": frozenset(
        {"knowledge-consumption.md", "repository-handoff.md", "resources-context.md"}
    ),
    "dep-audit": frozenset(
        {"knowledge-consumption.md", "repository-handoff.md"}
    ),
    "doc-hub": frozenset(
        {"knowledge-consumption.md", "publishing.md", "resources-context.md"}
    ),
    "doc-review": frozenset(
        {"knowledge-consumption.md", "repository-handoff.md"}
    ),
    "impact-analysis": frozenset(
        {"context-query.md", "knowledge-consumption.md"}
    ),
    "infra-review": frozenset(
        {"knowledge-consumption.md", "repository-handoff.md"}
    ),
    "onboarding-guide": frozenset(
        {"knowledge-consumption.md", "repository-handoff.md", "resources-context.md"}
    ),
    "publish-docs": frozenset(
        {"knowledge-consumption.md", "publishing.md", "resources-context.md"}
    ),
    "usage-examples": frozenset(
        {"knowledge-consumption.md", "publishing.md", "repository-handoff.md"}
    ),
    "user-docs-author": frozenset(
        {
            "knowledge-consumption.md",
            "publishing.md",
            "repository-handoff.md",
            "resources-context.md",
        }
    ),
    "wiki-bootstrap": frozenset(
        {"governance.md", "knowledge-consumption.md", "repository-handoff.md"}
    ),
    "wiki-semantic-enhance": frozenset(
        {"knowledge-consumption.md", "repository-handoff.md", "resources-context.md"}
    ),
    "wiki-sync": frozenset(
        {
            "context-query.md",
            "extractors-dependencies.md",
            "governance.md",
            "knowledge-consumption.md",
            "maintenance.md",
            "repository-handoff.md",
            "resources-context.md",
            "surfaces-naming.md",
        }
    ),
}


def _manifest(skill_id: str) -> str:
    return (
        skills.BUNDLED_SKILLS_ROOT / skill_id / skills.SKILL_MANIFEST_NAME
    ).read_text(encoding="utf-8")


def _description_diagnostics() -> tuple[int, str]:
    rows = [
        (skill.skill_id, len(skill.description.split()))
        for skill in skills.list_bundled_skills()
    ]
    diagnostics = "\n".join(
        f"{skill_id}: {word_count} words" for skill_id, word_count in rows
    )
    return sum(word_count for _, word_count in rows), diagnostics


def test_bundled_description_word_baseline_is_bounded_and_diagnostic() -> None:
    bundled = skills.list_bundled_skills()
    total, diagnostics = _description_diagnostics()
    outside_target = {
        skill.skill_id: len(skill.description.split())
        for skill in bundled
        if len(skill.description.split()) not in DESCRIPTION_WORD_RANGE
    }

    assert not outside_target, f"description target violations:\n{diagnostics}"
    assert total == DESCRIPTION_WORD_BASELINE, (
        f"description word baseline changed: {total} != "
        f"{DESCRIPTION_WORD_BASELINE}\n{diagnostics}"
    )


@pytest.mark.parametrize(
    ("skill_id", "topics"),
    sorted(EXPECTED_COMMON_ROUTES.items()),
)
def test_common_policy_routes_are_direct_portable_dependencies(
    skill_id: str,
    topics: frozenset[str],
) -> None:
    manifest = _manifest(skill_id)

    assert skills.SKILL_DEPENDENCIES[skill_id] == (skills.REFERENCE_SKILL_ID,)
    for topic in sorted(topics):
        assert f"{CLAUDE_TOPIC_ROOT}/{topic}" in manifest, (
            f"{skill_id} lacks the Claude route for {topic}"
        )
        assert f"{GENERIC_TOPIC_ROOT}/{topic}" in manifest, (
            f"{skill_id} lacks the generic route for {topic}"
        )
        assert (
            skills.BUNDLED_SKILLS_ROOT
            / skills.REFERENCE_SKILL_ID
            / "references"
            / topic
        ).is_file(), f"{skill_id} routes to missing topic {topic}"


def test_every_direct_managed_topic_route_is_paired_and_dependency_closed() -> None:
    topic_root = (
        skills.BUNDLED_SKILLS_ROOT / skills.REFERENCE_SKILL_ID / "references"
    )
    known_topics = {path.name for path in topic_root.glob("*.md")}

    for skill in skills.list_bundled_skills():
        if skill.skill_id == skills.REFERENCE_SKILL_ID:
            continue
        manifest = _manifest(skill.skill_id)
        routed_topics = {
            topic
            for topic in known_topics
            if f"{CLAUDE_TOPIC_ROOT}/{topic}" in manifest
            or f"{GENERIC_TOPIC_ROOT}/{topic}" in manifest
        }
        if not routed_topics:
            continue

        assert skills.SKILL_DEPENDENCIES[skill.skill_id] == (
            skills.REFERENCE_SKILL_ID,
        )
        for topic in routed_topics:
            assert f"{CLAUDE_TOPIC_ROOT}/{topic}" in manifest, (
                f"{skill.skill_id} has only the generic route for {topic}"
            )
            assert f"{GENERIC_TOPIC_ROOT}/{topic}" in manifest, (
                f"{skill.skill_id} has only the Claude route for {topic}"
            )


@pytest.mark.parametrize(
    "skill_id",
    (
        "dep-audit",
        "doc-review",
        "infra-review",
        "onboarding-guide",
        "usage-examples",
        "user-docs-author",
        "wiki-bootstrap",
        "wiki-sync",
    ),
)
def test_managed_wiki_mutation_keeps_a_local_fail_closed_kernel(
    skill_id: str,
) -> None:
    normalized = " ".join(_manifest(skill_id).split()).lower()

    assert "git check-ignore --no-index -- <wiki-dir>/ <wiki-dir>/index.md" in normalized
    assert "local-only" in normalized
    assert "force-add" in normalized
    assert "ignore/exclude" in normalized


def test_impact_analysis_routes_generic_native_policy_and_keeps_graph_kernel() -> None:
    reference = (
        skills.BUNDLED_SKILLS_ROOT / "impact-analysis" / "reference.md"
    ).read_text(encoding="utf-8")

    assert "## Native decision and fallback table" not in reference
    assert "| `absent`" not in reference
    assert "| `degraded`" not in reference
    assert "freshness_evaluated: false" not in reference
    assert "../wiki-reference/references/knowledge-consumption.md" in reference
    assert "## Typed-graph decision supplement" in reference
    assert "typed-graph extension unavailable" in reference
    assert "Exact identity or persisted alias is ambiguous" in reference
