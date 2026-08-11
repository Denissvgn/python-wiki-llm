"""Tests for schema block replacement."""

import re
import shlex
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services import schema
from llm_wiki_cli.services.schema import (
    CONSTRAINT_END,
    CONSTRAINT_START,
    SCHEMA_BLOCK_VERSION,
    ManagedSchemaBlock,
    ManagedSchemaBlockState,
    SchemaRenderProfile,
    build_schema_content as _build_schema_content,
    build_upgraded_schema_content,
    classify_managed_schema_block,
    replace_schema_block,
    replace_schema_block_content,
)


def _squash_ws(content: str) -> str:
    return " ".join(content.split())


def build_schema_content(
    agent: str,
    wiki_dir: str,
    *,
    quality_hints: bool = True,
    issue_reporting: bool = False,
    source_selection: str | Path | None = None,
) -> str:
    """Render the expanded-inline profile used by detailed contract assertions."""
    return _build_schema_content(
        agent,
        wiki_dir,
        render_profile=SchemaRenderProfile.EXPANDED_INLINE,
        quality_hints=quality_hints,
        issue_reporting=issue_reporting,
        source_selection=source_selection,
    )


def build_compact_schema_content(
    agent: str,
    wiki_dir: str,
    *,
    quality_hints: bool = True,
    issue_reporting: bool = False,
    source_selection: str | Path | None = None,
) -> str:
    """Render the compact profile used by safety-kernel assertions."""
    return _build_schema_content(
        agent,
        wiki_dir,
        render_profile=SchemaRenderProfile.COMPACT,
        quality_hints=quality_hints,
        issue_reporting=issue_reporting,
        source_selection=source_selection,
    )


def test_replace_schema_block_preserves_literal_backslashes(tmp_path):
    schema_path = tmp_path / "AGENTS.md"
    schema_path.write_text(
        f"User intro\n\n{CONSTRAINT_START}\nold\n{CONSTRAINT_END}\n\nUser outro\n",
        encoding="utf-8",
    )
    new_content = f"{CONSTRAINT_START}\npath \\1 \\g<name>\n{CONSTRAINT_END}\n"

    replace_schema_block(schema_path, new_content)

    text = schema_path.read_text(encoding="utf-8")
    assert "path \\1 \\g<name>" in text
    assert "User intro" in text
    assert "User outro" in text


@pytest.mark.parametrize("render_profile", list(SchemaRenderProfile))
@pytest.mark.parametrize("quality_hints", [False, True])
@pytest.mark.parametrize("issue_reporting", [False, True])
def test_schema_profiles_are_deterministic_and_machine_classified(
    render_profile: SchemaRenderProfile,
    quality_hints: bool,
    issue_reporting: bool,
) -> None:
    first = _build_schema_content(
        "generic",
        "docs/llm_wiki",
        render_profile=render_profile,
        quality_hints=quality_hints,
        issue_reporting=issue_reporting,
        source_selection="config/team selection.json",
    )
    second = _build_schema_content(
        "generic",
        "docs/llm_wiki",
        render_profile=render_profile,
        quality_hints=quality_hints,
        issue_reporting=issue_reporting,
        source_selection="config/team selection.json",
    )

    assert first == second
    assert first.splitlines()[1] == (
        f"<!-- llm-wiki-schema: version={SCHEMA_BLOCK_VERSION} "
        f"profile={render_profile.value} -->"
    )
    assert classify_managed_schema_block(first) == ManagedSchemaBlock(
        ManagedSchemaBlockState.PROFILED,
        profile=render_profile,
        version=SCHEMA_BLOCK_VERSION,
        raw_profile=render_profile.value,
    )
    assert ("## Agent quality guidelines" in first) is quality_hints
    assert ("## Report llm-wiki tool issues" in first) is issue_reporting


def test_schema_renderer_does_not_verify_installed_skill_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_verification(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("renderer attempted managed-reference verification")

    monkeypatch.setattr(
        "llm_wiki_cli.services.skills.BUNDLED_SKILLS_ROOT",
        tmp_path / "missing-bundle",
    )
    monkeypatch.setattr(
        "llm_wiki_cli.services.skills.reference_skill_state",
        unexpected_verification,
    )

    for render_profile in SchemaRenderProfile:
        content = _build_schema_content(
            "generic",
            "docs/llm_wiki",
            render_profile=render_profile,
        )
        assert classify_managed_schema_block(content).profile is render_profile
    assert not (tmp_path / "missing-bundle").exists()


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("# User content\n", ManagedSchemaBlockState.ABSENT),
        (
            f"{CONSTRAINT_START}\nlegacy body\n{CONSTRAINT_END}\n",
            ManagedSchemaBlockState.LEGACY_EXPANDED_INLINE,
        ),
        (
            f"{CONSTRAINT_START}\nlegacy body\n",
            ManagedSchemaBlockState.MALFORMED,
        ),
        (
            f"{CONSTRAINT_START}\nlegacy\n{CONSTRAINT_END}\n"
            f"{CONSTRAINT_START}\nduplicate\n{CONSTRAINT_END}\n",
            ManagedSchemaBlockState.MALFORMED,
        ),
        (
            f"{CONSTRAINT_START}\nbody first\n"
            "<!-- llm-wiki-schema: version=1 profile=compact -->\n"
            f"{CONSTRAINT_END}\n",
            ManagedSchemaBlockState.MALFORMED,
        ),
        (
            f"{CONSTRAINT_START}\n"
            "<!-- llm-wiki-schema: version=2 profile=compact -->\nbody\n"
            f"{CONSTRAINT_END}\n",
            ManagedSchemaBlockState.UNSUPPORTED_VERSION,
        ),
        (
            f"{CONSTRAINT_START}\n"
            "<!-- llm-wiki-schema: version=1 profile=unknown -->\nbody\n"
            f"{CONSTRAINT_END}\n",
            ManagedSchemaBlockState.UNSUPPORTED_PROFILE,
        ),
        (
            f"{CONSTRAINT_START}\n"
            "<!-- llm-wiki-schema: profile=compact version=1 -->\nbody\n"
            f"{CONSTRAINT_END}\n",
            ManagedSchemaBlockState.MALFORMED,
        ),
    ],
)
def test_managed_schema_classifier_fails_closed(
    content: str,
    expected: ManagedSchemaBlockState,
) -> None:
    assert classify_managed_schema_block(content).state is expected


def test_classifier_retains_unsupported_marker_diagnostics() -> None:
    unsupported_version = classify_managed_schema_block(
        f"{CONSTRAINT_START}\n"
        "<!-- llm-wiki-schema: version=9 profile=compact -->\nbody\n"
        f"{CONSTRAINT_END}\n"
    )
    unsupported_profile = classify_managed_schema_block(
        f"{CONSTRAINT_START}\n"
        "<!-- llm-wiki-schema: version=1 profile=future_profile -->\nbody\n"
        f"{CONSTRAINT_END}\n"
    )

    assert unsupported_version == ManagedSchemaBlock(
        ManagedSchemaBlockState.UNSUPPORTED_VERSION,
        version=9,
        raw_profile="compact",
    )
    assert unsupported_profile == ManagedSchemaBlock(
        ManagedSchemaBlockState.UNSUPPORTED_PROFILE,
        version=SCHEMA_BLOCK_VERSION,
        raw_profile="future_profile",
    )


def test_classifier_normalizes_legacy_and_profiled_crlf() -> None:
    legacy = f"{CONSTRAINT_START}\r\nlegacy\r\n{CONSTRAINT_END}\r\n"
    profiled = _build_schema_content(
        "generic",
        "docs/llm_wiki",
        render_profile=SchemaRenderProfile.COMPACT,
    ).replace("\n", "\r\n")

    assert classify_managed_schema_block(legacy).state is (
        ManagedSchemaBlockState.LEGACY_EXPANDED_INLINE
    )
    assert classify_managed_schema_block(profiled).profile is (
        SchemaRenderProfile.COMPACT
    )


def test_legacy_block_upgrades_to_profiled_block_without_touching_user_text() -> None:
    existing = (
        "# User intro\n\n"
        f"{CONSTRAINT_START}\nlegacy body\n{CONSTRAINT_END}\n\n"
        "# User outro\n"
    )
    managed = _build_schema_content(
        "generic",
        "docs/llm_wiki",
        render_profile=SchemaRenderProfile.EXPANDED_INLINE,
    )

    updated = replace_schema_block_content(existing, managed)

    assert updated.startswith("# User intro\n\n")
    assert updated.endswith("# User outro\n")
    assert updated.count(CONSTRAINT_START) == 1
    assert classify_managed_schema_block(updated).profile is (
        SchemaRenderProfile.EXPANDED_INLINE
    )


def test_upgraded_schema_content_composes_managed_and_plugin_blocks_once() -> None:
    existing = (
        "# User intro\n\n"
        f"{CONSTRAINT_START}\nlegacy body\n{CONSTRAINT_END}\n\n"
        "# --- LLM Wiki Skill: demo/rules ---\nold\n"
        "# --- End LLM Wiki Skill: demo/rules ---\n"
    )
    managed = _build_schema_content(
        "generic",
        "docs/llm_wiki",
        render_profile=SchemaRenderProfile.EXPANDED_INLINE,
    )
    blocks = (("demo", "rules", "new rules"), ("extra", "checks", "be exact"))

    updated, refreshed = build_upgraded_schema_content(existing, managed, blocks)
    repeated, repeated_ids = build_upgraded_schema_content(updated, managed, blocks)

    assert refreshed == repeated_ids == ["demo/rules", "extra/checks"]
    assert updated == repeated
    assert updated.startswith("# User intro\n\n")
    assert updated.count(CONSTRAINT_START) == 1
    assert updated.count("# --- LLM Wiki Skill: demo/rules ---") == 1
    assert "\nold\n" not in updated
    assert "new rules" in updated
    assert updated.count("# --- LLM Wiki Skill: extra/checks ---") == 1


def test_schema_replacement_preserves_crlf_user_and_plugin_bytes() -> None:
    user_prefix = "# User heading\r\nkeep trailing spaces  \r\n\r\n"
    old_managed = (
        f"{CONSTRAINT_START}\r\nlegacy body\r\n{CONSTRAINT_END}\r\n"
    )
    untouched_tail = (
        "# --- LLM Wiki Skill: external/rules ---\r\n"
        "preserve \\slashes, trailing spaces  \r\n"
        "# --- End LLM Wiki Skill: external/rules ---\r\n"
        "\r\n# User footer\r\n"
    )
    replacement = build_compact_schema_content("generic", "docs/team wiki")

    updated = replace_schema_block_content(
        user_prefix + old_managed + untouched_tail,
        replacement,
    )

    assert updated.startswith(user_prefix)
    assert updated.endswith(untouched_tail)
    assert updated.count(CONSTRAINT_START) == 1
    assert classify_managed_schema_block(updated).profile is SchemaRenderProfile.COMPACT


def test_schema_and_plugin_refresh_preserve_unmanaged_crlf_slices() -> None:
    user_prefix = "# User intro\r\n\r\n"
    old_managed = f"{CONSTRAINT_START}\r\nold\r\n{CONSTRAINT_END}\r\n"
    old_plugin = (
        "# --- LLM Wiki Skill: demo/rules ---\r\n"
        "old rules\r\n"
        "# --- End LLM Wiki Skill: demo/rules ---\r\n"
    )
    untouched_tail = (
        "# User-owned separator with trailing spaces  \r\n"
        "# --- LLM Wiki Skill: external/checks ---\r\n"
        "do not normalize \\1 \\g<name>\r\n"
        "# --- End LLM Wiki Skill: external/checks ---\r\n"
        "# User outro\r\n"
    )
    managed = build_compact_schema_content("generic", "docs/team wiki")

    updated, refreshed = build_upgraded_schema_content(
        user_prefix + old_managed + old_plugin + untouched_tail,
        managed,
        (("demo", "rules", "new rules"),),
    )

    assert refreshed == ["demo/rules"]
    assert updated.startswith(user_prefix)
    assert updated.endswith(untouched_tail)
    assert updated.count("# --- LLM Wiki Skill: demo/rules ---") == 1
    assert "\nnew rules\n" in updated


def test_refresh_skill_blocks_adapter_performs_one_atomic_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    Path("AGENTS.md").write_text("# User rules\n", encoding="utf-8")
    monkeypatch.setattr(
        schema,
        "installed_skill_block_contents",
        lambda: (("demo", "rules", "new rules"), ("extra", "checks", "exact")),
    )
    writes: list[tuple[Path, bytes]] = []
    original_write = schema.write_bytes_atomic

    def track_write(path: Path, content: bytes) -> Path:
        writes.append((path, content))
        return original_write(path, content)

    monkeypatch.setattr(schema, "write_bytes_atomic", track_write)

    refreshed = schema.refresh_skill_blocks("generic", "docs/llm_wiki")

    assert refreshed == ["demo/rules", "extra/checks"]
    assert len(writes) == 1
    assert writes[0][0] == Path("AGENTS.md")
    assert Path("AGENTS.md").read_bytes() == writes[0][1]


def test_agent_schema_mentions_current_sync_and_lint_runtime():
    content = build_schema_content("generic", "docs/llm_wiki")

    assert "llm-wiki sync --jobs 1 --wiki-dir docs/llm_wiki --src-dir ." in content
    assert (
        "llm-wiki lint --strict --jobs 1 --wiki-dir docs/llm_wiki --src-dir ."
        in content
    )
    assert (
        "llm-wiki lint --profile --cache-stats --wiki-dir docs/llm_wiki --src-dir ."
        in content
    )
    assert (
        "llm-wiki lint --strict --jobs 1 --wiki-dir docs/llm_wiki "
        "--src-dir <repo> --allow-external-src" in content
    )
    assert "llm-wiki prepare-extractors --src-dir ." in content
    assert "persistent inventory cache" in content
    assert "--allow-external-src" in content
    assert "project-root write guard" in content
    assert "large-diff guard" in content
    assert "semantic pass" in content
    assert "Lint passing is not enough" in content
    assert "_Auto-generated from ..._" in content


def test_agent_schema_pins_configured_source_selection_in_maintenance_recipes():
    profile = "config/team selection.json"
    content = build_schema_content(
        "generic",
        "docs/llm_wiki",
        source_selection=profile,
    )
    selection_arg = "--source-selection 'config/team selection.json'"

    for recipe in (
        "llm-wiki context --budget 8000 --src-dir . "
        "--wiki-dir docs/llm_wiki --format packet --focus changed "
        "--knowledge-mode auto --read-only",
        "llm-wiki extract --src-dir .",
        "llm-wiki generate-prompt",
        "llm-wiki lint --strict --jobs 1",
        "llm-wiki prepare-extractors --src-dir .",
        "llm-wiki sync --jobs 1",
    ):
        recipe_lines = [line for line in content.splitlines() if recipe in line]
        assert recipe_lines
        assert all(selection_arg in line for line in recipe_lines)


def test_bundled_sync_skill_preserves_profile_and_uses_selected_diffs_only():
    skill_root = (
        Path(__file__).parents[1] / "src" / "llm_wiki_cli" / "skills" / "wiki-sync"
    )
    skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    reference = (skill_root / "reference.md").read_text(encoding="utf-8")

    assert "--source-selection <profile>" in skill
    assert "--source-selection <profile>" in reference
    assert "never run an unrestricted `git diff` or `git diff --stat`" in skill
    assert "never read an unrestricted diff or stat" in reference


def test_agent_schema_is_scope_and_resource_aware():
    content = build_schema_content("generic", "docs/llm_wiki")
    text = _squash_ws(content)

    assert "## Resource-aware execution" in content
    assert "For broad repository-wide work" in content
    assert (
        "llm-wiki context --budget 8000 --src-dir . "
        "--wiki-dir docs/llm_wiki --format packet --focus changed "
        "--knowledge-mode auto --read-only" in content
    )
    assert "For a narrow task with supplied files or a supplied diff" in content
    assert "skip the full context scan" in text
    assert "full deep inventory" in content
    assert "bound emitted output, not scan cost" in text
    assert "The supervisor owns heavy-gate scheduling" in content
    assert "must not launch a heavy gate unless the supervisor" in text
    assert "Use `--jobs 1` for interactive" in content
    assert "isolated terminal or controlled CI runner" in text
    assert "mark unfinished gates inconclusive" in text


def test_agent_schema_distinguishes_aggregate_and_concept_freshness():
    content = build_schema_content("generic", "docs/llm_wiki")
    text = _squash_ws(content)

    assert "`freshness`, and `freshness_evaluated`" in text
    assert "`evaluated (N concepts)`" in text
    assert "`unevaluated (snapshot-only read)`" in text
    assert "one result per concept" in text
    assert "does not mean every concept had a live comparison" in text
    assert "state, reason, and `live_comparison_performed`" in text
    assert "`live_comparison_performed: false` remains non-live" in text


def test_agent_schema_mentions_dependency_architecture_responsibilities():
    content = build_schema_content("generic", "docs/llm_wiki")

    assert "dependencies.md" in content
    assert "load-order.md" in content
    assert "--skip-dependencies" in content
    assert "## Notes" in content
    assert "agent-owned" in content
    assert "Import cycles" in content
    assert "undeclared" in content
    assert "unused" in content
    assert "warning diagnostics" in content


def test_agent_schema_points_to_direct_managed_reference_topics():
    content = build_schema_content("generic", "docs/llm_wiki")
    text = _squash_ws(content)

    assert "## Deep reference (read on demand)" in content
    claude_content = build_schema_content("claude", "docs/llm_wiki")
    for topic in (
        "context-query",
        "extractors-dependencies",
        "knowledge-consumption",
        "maintenance",
        "publishing",
        "repository-handoff",
        "resources-context",
        "surfaces-naming",
    ):
        suffix = f"wiki-reference/references/{topic}.md"
        assert f".llm-wiki/skills/{suffix}" in content
        assert f".claude/skills/{suffix}" in claude_content
    assert "wiki-reference/reference.md" not in content
    assert "wiki-reference/reference.md" not in claude_content
    assert (
        "llm-wiki skills install --dest .llm-wiki/skills --skill wiki-reference --force"
    ) in content
    assert (
        "llm-wiki skills install --dest .claude/skills --skill wiki-reference --force"
    ) in claude_content
    assert "llm-wiki skills export --dest exported-skills" in content
    assert "Do not read every topic upfront" in text
    # Inline pointers keep trigger conditions next to the rules that need them.
    assert "extractor and dependency" in text
    assert "static-site and Obsidian" in content
    assert "context, packet, exact-query" in content
    assert "not required to recover this core loop" in text


def test_agent_schema_mentions_data_flow_review_responsibilities():
    content = build_schema_content("generic", "docs/llm_wiki")

    assert "## Data flow" in content
    assert "static-analysis gaps" in content
    assert "## Behavior" in content
    assert "observed side effects" in content


def test_agent_schema_mentions_canonical_surfaces_and_generated_ownership():
    content = build_schema_content("generic", "docs/llm_wiki")

    assert "canonical wiki surfaces" in content
    for path in [
        "docs/llm_wiki/index.md",
        "docs/llm_wiki/log.md",
        "docs/llm_wiki/entities/",
        "docs/llm_wiki/modules/",
        "docs/llm_wiki/workflows/",
        "docs/llm_wiki/guides/",
        "docs/llm_wiki/flows/",
        "docs/llm_wiki/infrastructure/",
        "docs/llm_wiki/dependencies.md",
        "docs/llm_wiki/load-order.md",
    ]:
        assert path in content
    assert "Do not edit generated Mermaid diagrams by hand" in content
    assert "Diagram style plugins may configure generated Mermaid flowchart" in content
    assert "cannot inject arbitrary Markdown" in content
    assert "semantic sections" in content
    assert "`sync` does not generate or overwrite guide prose" in content
    assert "Static-site mirror output" in content
    assert "not as an editable source of truth" in content


def test_agent_schema_mentions_user_docs_usage_example_workflow():
    content = build_schema_content("generic", "docs/llm_wiki")
    text = _squash_ws(content)

    assert "## User docs and usage examples" in content
    assert (
        "wiki-bootstrap -> wiki-sync -> user-docs-author -> usage-examples -> publish-docs"
        in text
    )
    assert "assets/<surface>/<page-stem>/" in content
    assert "semantic prose only" in content
    assert "generated blocks are CLI-owned" in content
    assert "source targets read-only" in content
    assert "no toolchain installs" in content
    assert "validation loop before delivery" in content
    assert "When repository policy permits a wiki commit" in content
    assert "keep it separate from code commits" in text
    assert "capture tooling" in content
    assert "agent platform" in content


def test_agent_schema_requires_repository_aware_git_handoff():
    content = build_schema_content("generic", "docs/llm_wiki")
    text = _squash_ws(content)

    assert "## Repository delivery preflight" in content
    assert (
        "git check-ignore --no-index -- docs/llm_wiki/ "
        "docs/llm_wiki/index.md" in content
    )
    assert "user's instructions and every applicable local repository rule" in text
    assert "Exit 0 means the wiki is local-only" in text
    assert "Exit 1 is only conditionally Git-eligible" in text
    assert "Any other result is indeterminate and fails closed" in text
    assert "do not stage, commit, force-add, or change ignore/exclude rules" in text
    assert "wiki-reference/references/repository-handoff.md" in text
    assert "`external_agent_docs` keeps its stricter packet boundary" in text


def test_agent_schema_omits_tool_issue_reporting_by_default():
    content = build_schema_content("generic", "docs/llm_wiki")

    assert "## Report llm-wiki tool issues" not in content
    assert "llm-wiki-issues/" not in content


def test_agent_schema_mentions_tool_issue_reporting_when_enabled():
    content = build_schema_content("generic", "docs/llm_wiki", issue_reporting=True)
    text = _squash_ws(content)

    assert "## Report llm-wiki tool issues" in content
    assert "never work around it silently" in text
    assert "llm-wiki-issues/<YYYY-MM-DD>-<short-slug>.md" in content
    assert "outside `docs/llm_wiki/` only after" in text
    assert (
        "`git check-ignore -q -- <exact-report-path>` proves that exact file is ignored"
        in text
    )
    assert "an already ignored path or a user-approved non-repository" in text
    assert "do not change ignore policy or stage it" in text
    assert "exact command and flags you ran" in content
    assert "`llm-wiki --version` output" in content
    assert "minimal reproduction steps" in text
    assert "addressed upstream" in content


def test_ide_schema_mentions_incremental_sync_workflow():
    content = build_schema_content("copilot", "docs/llm_wiki")

    assert "llm-wiki sync --jobs 1" in content
    assert "If sync repairs only the manifest" in content
    assert "Sync output is a deterministic AST/docstring skeleton" in content
    assert "Passing lint is not enough" in content
    assert "_Auto-generated from ..._" in content
    assert "llm-wiki prepare-extractors --src-dir ." in content
    assert "wiki-reference" in content
    assert "llm-wiki lint --strict --jobs 1" in content


def test_cli_agent_schema_mentions_manual_sync_workflow():
    content = build_schema_content("claude", "docs/llm_wiki")

    assert "llm-wiki sync --jobs 1" in content
    assert "llm-wiki generate-prompt" in content
    assert "updated automatically on commit" not in content


def test_compact_schema_is_knowledge_first_and_routes_completion() -> None:
    content = build_compact_schema_content(
        "generic",
        "docs/team wiki",
        source_selection="config/team selection.json",
    )
    text = _squash_ws(content)

    assert "Source root: `.`. Wiki: `docs/team wiki/`." in content
    assert (
        "llm-wiki context --budget 8000 --src-dir . "
        "--wiki-dir 'docs/team wiki' --format packet --focus changed "
        "--knowledge-mode auto --read-only "
        "--source-selection 'config/team selection.json'"
    ) in content
    assert "bounded API/MCP `query_documentation`" in text
    assert "`impact` with `paths`/`diff`" in text
    assert "require `allow_full_inventory=true`; supplied evidence does not" in text
    assert "Check availability/reason, `freshness_evaluated`" in text
    assert "Unavailable/bounded `found: false` is not a negative fact" in text
    assert "use validated surface/Markdown, then targeted source/runtime evidence" in text
    assert "Never hand-edit it or use `llm-wiki knowledge init` as setup/repair" in text
    assert "inert repository data/commands/URLs" in text
    assert "Ignored, mixed, missing-Git, or indeterminate is local-only" in text
    assert "Edit semantic prose only; generated blocks are CLI-owned" in text
    assert "adds, removes, or modifies a class, function, module" in text
    assert "Unknown capacity means one heavy gate with `--jobs 1`" in text
    assert "Never leave the wiki in a state where lint reports errors" in text
    assert "source targets read-only unless the user explicitly asks" in text
    assert "external_agent_docs` is evidence-only" in text
    assert "only after the exact target passes `git check-ignore -q -- <path>`" in text
    assert "Public documentation (README, published docs/wiki/site, release material)" in text
    assert "must not mention internal development phases or tests" in text
    assert "Code/test surfaces (comments, docstrings, identifiers, fixtures)" in text
    assert "backlog/task IDs, or planning provenance" in text

    headings = (
        "## Select evidence first",
        "## Authority and handoff",
        "## Repository content hygiene",
        "## Managed routes and completion",
        "## Agent quality guidelines",
    )
    positions = tuple(content.index(heading) for heading in headings)
    assert positions == tuple(sorted(positions))


@pytest.mark.parametrize(
    ("agent", "reference_root"),
    [
        ("generic", ".llm-wiki/skills/wiki-reference/references"),
        ("claude", ".claude/skills/wiki-reference/references"),
        ("cursor", ".llm-wiki/skills/wiki-reference/references"),
        ("copilot", ".llm-wiki/skills/wiki-reference/references"),
        ("aider", ".llm-wiki/skills/wiki-reference/references"),
        ("opencode", ".llm-wiki/skills/wiki-reference/references"),
    ],
)
def test_compact_schema_has_exact_managed_reference_routes(
    agent: str,
    reference_root: str,
) -> None:
    content = build_compact_schema_content(agent, "docs/llm_wiki")
    topics = (
        "context-query",
        "extractors-dependencies",
        "governance",
        "knowledge-consumption",
        "maintenance",
        "publishing",
        "repository-handoff",
        "resources-context",
        "surfaces-naming",
    )

    for topic in topics:
        assert content.count(f"{reference_root}/{topic}.md") == 1
    assert f"{reference_root.rsplit('/', 1)[0]}/reference.md" not in content


def test_compact_schema_omits_expanded_procedural_catalogs() -> None:
    content = build_compact_schema_content("generic", "docs/llm_wiki")
    text = _squash_ws(content)

    for heading in (
        "## Before you start",
        "## Resource-aware execution",
        "## Canonical wiki surfaces",
        "## User docs and usage examples",
        "## Naming conventions",
        "## Quality checks",
        "## Formatting rules",
        "## How to sync the wiki in this agent session",
        "## Using `llm-wiki sync` for incremental updates",
        "## Large codebases",
    ):
        assert heading not in content
    assert "The canonical wiki surfaces are:" not in content
    assert "_Auto-generated from ..._" not in content
    assert "--prefer-fresh" not in content
    assert "read raw knowledge JSON" not in text
    assert "edit raw knowledge JSON" not in text
    assert "never raw knowledge JSON" in text
    assert "governance needs explicit owner approval and a recovery plan" in text
    assert "Optional user-selected routes" in text
    assert (
        "`wiki-bootstrap`, `wiki-sync`, `user-docs-author`, `usage-examples`, "
        "and `publish-docs`"
    ) in text


def test_compact_issue_reporting_requires_exact_ignore_proof() -> None:
    content = build_compact_schema_content(
        "generic",
        "docs/team wiki",
        issue_reporting=True,
    )
    text = _squash_ws(content)

    assert "## Report llm-wiki tool issues" in content
    assert "llm-wiki-issues/<date>-<slug>.md" in content
    assert "outside `docs/team wiki/` only when" in text
    assert "`git check-ignore -q -- <exact-report-path>` proves the file ignored" in text
    assert "use a user-approved non-repository scratch path" in text
    assert "Never publish, stage, force-add, or change `.gitignore`" in text
    assert content.index("## Managed routes and completion") < content.index(
        "## Report llm-wiki tool issues"
    ) < content.index("## Agent quality guidelines")


@pytest.mark.parametrize("agent", tuple(sorted(schema.SCHEMA_FILENAMES)))
@pytest.mark.parametrize("render_profile", list(SchemaRenderProfile))
@pytest.mark.parametrize("quality_hints", [False, True])
@pytest.mark.parametrize("issue_reporting", [False, True])
def test_generated_context_recipe_parses_with_custom_paths(
    agent: str,
    render_profile: SchemaRenderProfile,
    quality_hints: bool,
    issue_reporting: bool,
) -> None:
    content = _build_schema_content(
        agent,
        "docs/team wiki",
        render_profile=render_profile,
        quality_hints=quality_hints,
        issue_reporting=issue_reporting,
        source_selection="config/team selection.json",
    )
    commands = re.findall(r"`(llm-wiki context [^`\n]+)`", content)

    assert len(commands) == 1
    tokens = shlex.split(commands[0])
    assert tokens[0] == "llm-wiki"
    args = cli._build_parser().parse_args(tokens[1:])
    assert args.command == "context"
    assert args.budget == 8000
    assert args.src_dir == "."
    assert args.wiki_dir == "docs/team wiki"
    assert args.format == "packet"
    assert args.focus == "changed"
    assert args.knowledge_mode == "auto"
    assert args.read_only is True
    assert args.prefer_fresh is False
    assert args.source_selection == "config/team selection.json"

    knowledge_route = content.index("--knowledge-mode auto")
    exact_route = content.index("query_documentation", knowledge_route)
    navigation_fallback = content.index("docs/team wiki/index.md", exact_route)
    markdown_fallback = content.index(
        (
            "use validated surface/Markdown"
            if render_profile is SchemaRenderProfile.COMPACT
            else "then canonical Markdown"
        ),
        exact_route,
    )
    assert knowledge_route < exact_route < navigation_fallback
    assert knowledge_route < markdown_fallback


def _generated_cli_recipes(content: str) -> tuple[str, ...]:
    inline = re.findall(r"`(llm-wiki\s+[^`]+)`", content, flags=re.DOTALL)
    fenced = re.findall(r"(?m)^\s*(llm-wiki [^\n]+)$", content)
    return tuple(" ".join(recipe.split()) for recipe in (*inline, *fenced))


@pytest.mark.parametrize("agent", tuple(sorted(schema.SCHEMA_FILENAMES)))
@pytest.mark.parametrize("render_profile", list(SchemaRenderProfile))
@pytest.mark.parametrize("quality_hints", [False, True])
@pytest.mark.parametrize("issue_reporting", [False, True])
def test_generated_command_recipes_parse_for_every_target_and_option(
    agent: str,
    render_profile: SchemaRenderProfile,
    quality_hints: bool,
    issue_reporting: bool,
) -> None:
    content = _build_schema_content(
        agent,
        "docs/team wiki",
        render_profile=render_profile,
        quality_hints=quality_hints,
        issue_reporting=issue_reporting,
        source_selection="config/team selection.json",
    )
    recipes = _generated_cli_recipes(content)
    parser = cli._build_parser()

    assert recipes
    for recipe in recipes:
        tokens = shlex.split(recipe)
        assert tokens[0] == "llm-wiki"
        if tokens[1:] == ["--version"]:
            with pytest.raises(SystemExit) as caught:
                parser.parse_args(tokens[1:])
            assert caught.value.code == 0
        else:
            parser.parse_args(tokens[1:])


def test_expanded_schema_is_self_contained_when_references_are_unavailable() -> None:
    content = build_schema_content("generic", "docs/llm_wiki")
    text = _squash_ws(content)

    assert "This expanded profile is self-contained" in content
    assert "Managed topic paths below are optional detail" in text
    assert "follow the inline procedure without installing" in text
    assert "--format packet" in content
    assert "--knowledge-mode auto" in content
    assert "--prefer-fresh" not in content
    assert "non-ready, incompatible, snapshot-only, bounded, or insufficient" in text
    assert (
        "use an independently validated surface, then canonical Markdown, then "
        "targeted source/runtime evidence"
    ) in text
    assert "If a surface cannot be validated, skip it" in text
    assert "indeterminate and fails closed" in text
    assert "Never leave the wiki in a state where lint reports errors" in text
