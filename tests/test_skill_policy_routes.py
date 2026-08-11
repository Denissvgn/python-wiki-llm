"""Portable routing and metadata contracts for bundled workflow skills."""

from __future__ import annotations

import re

import pytest
from markdown_it import MarkdownIt

from llm_wiki_cli.services import skills
from llm_wiki_cli.services.instruction_ownership import markdown_anchor


CLAUDE_TOPIC_ROOT = ".claude/skills/wiki-reference/references"
GENERIC_TOPIC_ROOT = ".llm-wiki/skills/wiki-reference/references"
DESCRIPTION_WORD_BASELINE = 545
DESCRIPTION_WORD_RANGE = range(25, 41)
LONG_REFERENCE_LINE_THRESHOLD = 100
LONG_REFERENCE_RESOURCE_COUNT = 19
MARKDOWN = MarkdownIt("commonmark")

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

CANONICAL_REPOSITORY_REPORT_POLICY = (
    "wiki-reference/references/repository-handoff.md"
)
STANDALONE_REPOSITORY_REPORT_KERNELS = frozenset(
    {
        "attack-surface/SKILL.md",
        "dep-vuln-triage/SKILL.md",
    }
)
DEPENDENCY_BACKED_REPOSITORY_REPORT_REMINDERS = frozenset(
    {
        "infra-review/SKILL.md",
        "wiki-bootstrap/SKILL.md",
    }
)
REPOSITORY_REPORT_REFERENCE_POINTERS = frozenset(
    {
        "attack-surface/reference.md",
        "dep-vuln-triage/reference.md",
        "infra-review/reference.md",
        "wiki-bootstrap/reference.md",
    }
)
EXPLICIT_REPOSITORY_REPORT_DESTINATION = re.compile(r"`reports/[^`\n]+\.md`")


def _manifest(skill_id: str) -> str:
    return (
        skills.BUNDLED_SKILLS_ROOT / skill_id / skills.SKILL_MANIFEST_NAME
    ).read_text(encoding="utf-8")


def _normalized_skill_path(relative: str) -> str:
    content = (skills.BUNDLED_SKILLS_ROOT / relative).read_text(encoding="utf-8")
    return " ".join(content.split()).lower()


def _description_diagnostics() -> tuple[int, str]:
    rows = [
        (skill.skill_id, len(skill.description.split()))
        for skill in skills.list_bundled_skills()
    ]
    diagnostics = "\n".join(
        f"{skill_id}: {word_count} words" for skill_id, word_count in rows
    )
    return sum(word_count for _, word_count in rows), diagnostics


def _second_level_headings(content: str) -> tuple[str, ...]:
    tokens = MARKDOWN.parse(content)
    return tuple(
        tokens[index + 1].content
        for index, token in enumerate(tokens[:-1])
        if token.type == "heading_open" and token.tag == "h2"
    )


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


def test_long_reference_resources_have_complete_one_level_contents_maps() -> None:
    managed_topic_root = (
        skills.BUNDLED_SKILLS_ROOT / skills.REFERENCE_SKILL_ID / "references"
    )
    references = tuple(
        path
        for path in sorted(skills.BUNDLED_SKILLS_ROOT.rglob("*.md"))
        if len(path.read_text(encoding="utf-8").splitlines())
        > LONG_REFERENCE_LINE_THRESHOLD
        and (path.name == "reference.md" or path.parent == managed_topic_root)
    )

    assert len(references) == LONG_REFERENCE_RESOURCE_COUNT, (
        "long reference-resource census changed:\n"
        + "\n".join(
            path.relative_to(skills.BUNDLED_SKILLS_ROOT).as_posix()
            for path in references
        )
    )

    for path in references:
        content = path.read_text(encoding="utf-8")
        relative = path.relative_to(skills.BUNDLED_SKILLS_ROOT).as_posix()
        lines = content.splitlines()
        headings = _second_level_headings(content)

        assert headings.count("Contents") == 1, relative
        assert headings[0] == "Contents", f"Contents map is not first: {relative}"
        contents_index = lines.index("## Contents")
        assert contents_index <= 3, f"Contents map is not near the top: {relative}"

        expected = tuple(
            (heading, markdown_anchor(heading))
            for heading in headings
            if heading != "Contents"
        )
        cursor = contents_index + 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1

        actual: list[tuple[str, str]] = []
        while cursor < len(lines) and lines[cursor].startswith("- "):
            match = re.fullmatch(r"- \[(.+)\]\(#([^)]+)\)", lines[cursor])
            assert match is not None, f"invalid Contents entry: {relative}:{cursor + 1}"
            actual.append((match.group(1), match.group(2)))
            cursor += 1

        assert tuple(actual) == expected, relative
        anchors = tuple(anchor for _, anchor in actual)
        assert len(anchors) == len(set(anchors)), (
            f"duplicate Contents anchor: {relative}"
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


def test_repository_report_writes_require_exact_ignore_proof_and_nonpublication() -> None:
    explicit_destinations: set[str] = set()
    for path in skills.BUNDLED_SKILLS_ROOT.rglob("*.md"):
        relative = path.relative_to(skills.BUNDLED_SKILLS_ROOT).as_posix()
        content = path.read_text(encoding="utf-8")
        if EXPLICIT_REPOSITORY_REPORT_DESTINATION.search(content):
            explicit_destinations.add(relative)

    assert explicit_destinations == {
        path
        for path in (
            STANDALONE_REPOSITORY_REPORT_KERNELS
            | DEPENDENCY_BACKED_REPOSITORY_REPORT_REMINDERS
        )
        if path != "wiki-bootstrap/SKILL.md"
    } | REPOSITORY_REPORT_REFERENCE_POINTERS

    full_policy_carriers = STANDALONE_REPOSITORY_REPORT_KERNELS | {
        CANONICAL_REPOSITORY_REPORT_POLICY
    }
    for relative in sorted(full_policy_carriers):
        normalized = _normalized_skill_path(relative)

        assert "resolve the exact target" in normalized, relative
        assert "git check-ignore -q -- <exact-report-path>" in normalized, relative
        assert "only exit 0 permits that repository write" in normalized, relative
        assert "git/worktree is missing" in normalized, relative
        assert "target is unignored" in normalized, relative
        assert "result is indeterminate" in normalized, relative
        assert "do not create the report inside the repository" in normalized, relative
        assert "already ignored target" in normalized, relative
        assert "user-approved non-repository scratch path" in normalized, relative
        assert "never edit ignore/exclude policy" in normalized, relative
        assert "stage, force-add, commit, or publish" in normalized, relative
        assert "does not waive this rule" in normalized, relative
        assert normalized.count("git check-ignore -q -- <exact-report-path>") == 1

    for relative in sorted(DEPENDENCY_BACKED_REPOSITORY_REPORT_REMINDERS):
        normalized = _normalized_skill_path(relative)

        assert "exact-target fail-closed policy" in normalized, relative
        assert f"{CLAUDE_TOPIC_ROOT}/repository-handoff.md" in normalized, relative
        assert f"{GENERIC_TOPIC_ROOT}/repository-handoff.md" in normalized, relative
        assert (
            "suggested `reports/` path never authorizes repository creation or "
            "publication" in normalized
        ), relative
        assert "git check-ignore -q -- <exact-report-path>" not in normalized, relative

    for relative in sorted(REPOSITORY_REPORT_REFERENCE_POINTERS):
        normalized = _normalized_skill_path(relative)

        assert "treat this path only as a suggestion" in normalized, relative
        assert "exact-target repository-report preflight" in normalized, relative
        assert "[skill.md](skill.md) before any write" in normalized, relative
        assert (
            "path never authorizes repository creation or publication" in normalized
        ), relative
        assert "git check-ignore -q -- <exact-report-path>" not in normalized, relative


def test_repository_report_companions_and_public_logs_keep_sensitive_paths_local() -> None:
    attack = _normalized_skill_path("attack-surface/SKILL.md")
    attack_reference = _normalized_skill_path("attack-surface/reference.md")
    bootstrap_reference = _normalized_skill_path("wiki-bootstrap/reference.md")
    dependency_review = _normalized_skill_path("dep-vuln-triage/SKILL.md")
    infrastructure_review = _normalized_skill_path("infra-review/SKILL.md")

    assert "for every companion" in attack
    assert "resolve its own exact target and repeat the ignore proof" in attack
    assert "unproven target stays in the approved non-repository" in attack
    assert "apply the exact-target proof below before writing that output" in attack
    assert "sibling `skill.md` preflight separately to every companion" in (
        attack_reference
    )
    assert "keep every unproven companion target" in attack_reference
    assert "explicit `--output` payload may use a repository path only after" in (
        attack_reference
    )
    assert "extraction output in a user-approved non-repository scratch path" in (
        dependency_review
    )
    assert "transient extraction output in a user-approved non-repository" in (
        infrastructure_review
    )

    assert "record only that remainder coverage is external or unavailable" in (
        bootstrap_reference
    )
    assert "never record an ignored or non-repository target path" in (
        bootstrap_reference
    )
    assert "return the sensitive path only in the local handoff/result" in (
        bootstrap_reference
    )
    assert "record that fallback in `log.md`" not in bootstrap_reference


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
