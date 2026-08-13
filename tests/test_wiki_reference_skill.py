"""Tests for the bundled wiki-reference topics and their provisioning."""

import shutil
from pathlib import Path

import pytest

from llm_wiki_cli.services.skills import (
    BUNDLED_SKILLS_ROOT,
    GENERIC_INSTALL_TARGET,
    REFERENCE_SKILL_ID,
    REFERENCE_SKILL_FILES,
    export_skills,
    install_reference_skill,
    list_bundled_skills,
    reference_skill_state,
)


def _topic_text(filename: str) -> str:
    path = BUNDLED_SKILLS_ROOT / REFERENCE_SKILL_ID / "references" / filename
    return path.read_text(encoding="utf-8")


def _squash_ws(content: str) -> str:
    return " ".join(content.split())


def test_wiki_reference_is_bundled_with_frontmatter():
    skills = {s.skill_id: s for s in list_bundled_skills()}
    assert REFERENCE_SKILL_ID in skills
    skill = skills[REFERENCE_SKILL_ID]
    assert skill.description
    assert skill.files == REFERENCE_SKILL_FILES


def test_reference_documents_extractor_helpers_and_toolchains():
    content = _topic_text("extractors-dependencies.md")

    assert "llm-wiki prepare-extractors --src-dir ." in content
    assert "llm-wiki prepare-extractors --cache-dir .cache/llm-wiki-helpers" in content
    assert (
        "llm-wiki sync --cache-dir .cache/llm-wiki-inventory "
        "--helper-cache-dir .cache/llm-wiki-helpers" in content
    )
    assert "--include-tests go" in content
    assert "LLM_WIKI_GO=/path/to/go" in content
    assert "LLM_WIKI_GHC=/path/to/ghc" in content
    assert (
        "TypeScript/JavaScript, Go, Rust, and Haskell extraction runs through "
        "prepared helper toolchains"
    ) in _squash_ws(content)


def test_reference_documents_haskell_contract():
    content = _topic_text("extractors-dependencies.md")
    text = _squash_ws(content)

    assert "Normal extraction invokes the prepared helper" in text
    assert "syntax-only inventory without typechecking the target project" in text
    assert "starting Haskell Language Server" in text
    assert (
        "Haskell dependency reconciliation reads Cabal `build-depends` statically"
        in text
    )
    assert "Stack `extra-deps`, and Nix package hints" in text
    assert "optional advisory metadata" in text
    assert "Unknown Haskell imports are ignored rather than guessed" in text
    assert "GHC 9.6.x is the supported helper toolchain" in text
    assert "newer GHC 9.x releases are best-effort" in text
    assert "Generated Haskell module pages can render declared module names" in text
    assert "Haskell lockfile pinning is outside" in text


def test_reference_documents_haskell_inventory_schema():
    content = _topic_text("extractors-dependencies.md")
    text = _squash_ws(content)

    assert "Haskell inventory remains additive under `llm-wiki-extract/v1`" in text
    assert (
        "file entries contain `language`, `imports`, `classes`, and `functions`" in text
    )
    assert "`module` is present when source declares one" in text
    assert "import records contain `module`, `qualified`, `alias`, and `line`" in text
    assert "`classes` stores" in text
    assert "`data`, `newtype`, `type`, `class`, or `instance`" in content
    assert "`functions` stores" in text
    assert "`signature`, `function`, or `value`" in content
    assert "`language_pragmas`, `exports`, and `deriving` are best-effort" in text


def test_reference_documents_dependency_reconciliation_and_flows():
    content = _topic_text("extractors-dependencies.md")
    text = _squash_ws(content)

    assert "Nested Python `pyproject.toml` and `requirements*.txt` files" in text
    assert "Go `// indirect` requirements are transitive" in text
    assert "Optional lockfile-backed `versions`" in content
    assert "`dependencies.version_details`" in content
    assert "llm-wiki-dependency-version-details/v1" in content
    assert "`go.mod` selections remain distinct from `go.sum` observations" in text
    assert "`data_flow_details` sibling" in text
    assert "llm-wiki-extract-data-flow-details/v1" in content
    assert "`not_evaluated`, `unsupported`, and `evaluated`" in content
    assert "Raw Node `http.createServer` and `https.createServer` calls" in text
    assert "javascript_flow_unsupported" in content


def test_reference_documents_site_export_and_context():
    publishing = _topic_text("publishing.md")
    context = _topic_text("context-query.md")
    publishing_text = _squash_ws(publishing)
    context_text = _squash_ws(context)

    assert (
        "Docusaurus output includes generated front matter and `sidebars.json`"
        in publishing_text
    )
    assert "--profile reference" in publishing
    assert "--file-friendly" in publishing
    assert (
        "llm-wiki context --budget 8000 --src-dir . "
        "--wiki-dir docs/llm_wiki --format packet --focus changed "
        "--knowledge-mode auto --read-only" in context_text
    )
    assert '"protocol": "llm-wiki-context/v2"' in context
    assert "`prefer_fresh` is independent" in context
    assert "Python or MCP `query_documentation`" in context
    assert "Budget and focus bound emitted output, not scan work" in context_text
    assert "Broad repository orientation" in context
    assert "Exact concept" in context
    assert "Supplied changed paths or unified diff" in context


def test_reference_covers_all_strict_native_categories_without_conflation():
    section = _topic_text("knowledge-consumption.md")

    for category in (
        "knowledge_schema",
        "knowledge_projection",
        "knowledge_snapshot",
        "knowledge_evidence",
        "knowledge_freshness",
        "knowledge_governance",
        "knowledge_review",
        "knowledge_verification",
    ):
        assert f"`{category}`" in section
    normalized = _squash_ws(section)
    assert "human review" in normalized
    assert "machine-verification findings remain separate" in normalized
    assert "never runs a checker" in normalized


def test_reference_documents_typed_context_traversal_and_independent_bounds():
    content = _topic_text("context-query.md")
    normalized = _squash_ws(content)

    for refinement in (
        "relationship_kind",
        "relationship_origin",
        "relationship_resolution",
        "relationship_direction",
    ):
        assert f'"{refinement}"' in content
    for wrapper in (
        "get_concept",
        "list_concept_sections",
        "related_concepts",
        "traverse_typed_graph",
        "explain_evidence",
    ):
        assert wrapper in content
    assert "Build one Python documentation query service" in content
    assert "Supplying `service=` performs no new extraction" in normalized
    assert "A non-truncated query does not prove analyzer completeness" in normalized
    assert "`bounds.edges` describes post-filter response limiting" in normalized
    assert "evidence-sample omission" in normalized
    assert "Resolved, ambiguous, external, and unresolved endpoints remain" in (
        normalized
    )
    assert "legacy MCP `query_graph`" in normalized
    assert "does not alter core results" in normalized


def test_reference_documents_exact_identity_and_governance_lifecycle():
    identity = _topic_text("context-query.md")
    governance = _topic_text("governance.md")
    normalized = _squash_ws(identity)

    assert "current concept locators/MCP URIs" in normalized
    assert "exact canonical wiki path" in normalized
    assert "durable UID" in normalized
    assert "persisted locator/natural-key aliases" in normalized
    for action in (
        "knowledge init",
        "knowledge status",
        "knowledge move",
        "knowledge alias",
        "knowledge lifecycle set",
        "knowledge deprecate",
        "knowledge supersede",
        "knowledge review",
        "knowledge verify",
    ):
        assert action in governance
    normalized_governance = _squash_ws(governance)
    assert "All governance mutations support `--dry-run`" in normalized_governance
    assert "never merge, overwrite, delete, reallocate" in normalized_governance
    assert "disappearance does not deprecate" in normalized_governance
    assert "Agent review cannot satisfy it" in normalized_governance
    assert "restore the exact `.llm-wiki-governance.json`" in normalized_governance
    assert "Never reconstruct it from the generated projection" in (
        normalized_governance
    )


def test_reference_documents_safe_site_and_obsidian_projection_boundary():
    section = _topic_text("publishing.md")
    normalized = _squash_ws(section)

    for required in (
        "--knowledge-metadata summary",
        "--knowledge-profile public-portable",
        "--knowledge-public-repository-identity",
        "`internal`",
        "`not-evaluated`",
        "configured-public",
    ):
        assert required in section
    assert "Canonical Markdown bodies and copied media remain" in normalized
    assert "knowledge projection neither redacts nor reviews them" in normalized
    assert "Rebuild them from the validated canonical snapshot" in normalized


def test_reference_skill_routes_native_contracts_by_task():
    manifest = (BUNDLED_SKILLS_ROOT / REFERENCE_SKILL_ID / "SKILL.md").read_text(
        encoding="utf-8"
    )

    for route in (
        "](references/knowledge-consumption.md)",
        "](references/context-query.md)",
        "](references/governance.md)",
        "](references/publishing.md)",
    ):
        assert route in manifest
    assert "[reference.md](reference.md)" not in manifest
    assert "compatibility index for legacy anchors" in manifest


def test_reference_documents_resource_aware_execution():
    content = _topic_text("resources-context.md")
    text = _squash_ws(content)

    assert "# Resource-aware execution" in content
    for environment in [
        "Interactive IDE or unknown capacity",
        "Isolated terminal",
        "Controlled CI",
    ]:
        assert environment in content
    assert "The supervisor owns the schedule" in content
    assert "must not launch a heavy gate unless explicitly assigned" in content
    assert "`requested_jobs` is the caller's raw choice" in content
    assert "`resolved_jobs` is the integer concurrency ceiling" in content
    assert "`effective_workers` is the maximum number" in content
    assert "absent languages, cache-elided work, sequential-only" in text
    assert "not a global host-resource cap" in content
    assert "One later manual retry may use `--jobs 1`" in text
    assert "not proof that `llm-wiki` leaked a watcher" in text


class TestReferenceSkillProvisioning:
    def test_install_writes_bundled_files(self, tmp_path):
        report = install_reference_skill(tmp_path)

        assert report.ok
        skill_dir = tmp_path / ".claude" / "skills" / REFERENCE_SKILL_ID
        assert {
            path.relative_to(skill_dir).as_posix()
            for path in skill_dir.rglob("*")
            if path.is_file()
        } == set(REFERENCE_SKILL_FILES)
        assert reference_skill_state(tmp_path) == "unmodified"

    def test_state_absent_before_install(self, tmp_path):
        assert reference_skill_state(tmp_path) == "absent"

    def test_root_owned_platform_alias_preserves_install_and_export(
        self, tmp_path
    ):
        alias_root = Path("/var")
        if (
            not alias_root.is_symlink()
            or getattr(alias_root.lstat(), "st_uid", None) != 0
        ):
            pytest.skip("no root-owned /var platform alias")
        try:
            relative = tmp_path.resolve().relative_to(alias_root.resolve())
        except ValueError:
            pytest.skip("temporary directory is not below the /var alias target")

        aliased_tmp = alias_root / relative
        project = aliased_tmp / "alias-project"
        project.mkdir()
        assert reference_skill_state(project, agent="generic") == "absent"

        install_report = install_reference_skill(project, agent="generic")

        assert install_report.ok
        assert reference_skill_state(project, agent="generic") == "unmodified"

        export_dest = aliased_tmp / "alias-export"
        export_report = export_skills(
            export_dest,
            skills=[REFERENCE_SKILL_ID],
        )

        assert export_report.ok
        assert (export_dest / REFERENCE_SKILL_ID / "SKILL.md").is_file()

    def test_local_edit_requires_force_refresh(self, tmp_path):
        install_reference_skill(tmp_path)
        ref_path = (
            tmp_path
            / ".claude"
            / "skills"
            / REFERENCE_SKILL_ID
            / "references"
            / "maintenance.md"
        )
        ref_path.write_text("local notes\n", encoding="utf-8")
        assert reference_skill_state(tmp_path) == "modified"

        report = install_reference_skill(tmp_path)
        assert not report.ok
        assert ref_path.read_text(encoding="utf-8") == "local notes\n"

        report = install_reference_skill(tmp_path, force=True)
        assert report.ok
        assert ref_path.read_text(encoding="utf-8") != "local notes\n"
        assert reference_skill_state(tmp_path) == "unmodified"

    def test_missing_nested_file_is_restored(self, tmp_path):
        install_reference_skill(tmp_path)
        topic = (
            tmp_path
            / ".claude"
            / "skills"
            / REFERENCE_SKILL_ID
            / "references"
            / "governance.md"
        )
        topic.unlink()

        assert reference_skill_state(tmp_path) == "modified"
        report = install_reference_skill(tmp_path, force=True)

        assert report.ok
        assert topic.is_file()
        assert reference_skill_state(tmp_path) == "unmodified"

    def test_extra_file_marks_modified(self, tmp_path):
        install_reference_skill(tmp_path)
        skill_dir = tmp_path / ".claude" / "skills" / REFERENCE_SKILL_ID
        extra = skill_dir / "references" / "notes.md"
        extra.write_text("extra\n", encoding="utf-8")
        assert reference_skill_state(tmp_path) == "modified"

        report = install_reference_skill(tmp_path, force=True)

        assert not report.ok
        assert extra.read_text(encoding="utf-8") == "extra\n"
        assert any(
            issue["category"] == "managed_tree_not_exact" for issue in report.issues
        )

    def test_extra_empty_directory_marks_modified(self, tmp_path):
        install_reference_skill(tmp_path)
        skill_dir = tmp_path / ".claude" / "skills" / REFERENCE_SKILL_ID
        (skill_dir / "references" / "local").mkdir()

        assert reference_skill_state(tmp_path) == "modified"

    def test_expected_file_symlink_is_modified_and_never_followed(self, tmp_path):
        install_reference_skill(tmp_path)
        skill_dir = tmp_path / ".claude" / "skills" / REFERENCE_SKILL_ID
        topic = skill_dir / "references" / "maintenance.md"
        outside = tmp_path / "outside.md"
        sentinel = "outside sentinel must never change\n"
        outside.write_text(sentinel, encoding="utf-8")
        topic.unlink()
        try:
            topic.symlink_to(outside)
        except OSError as exc:  # pragma: no cover - platform policy
            pytest.skip(f"symlinks unavailable: {exc}")

        assert reference_skill_state(tmp_path) == "modified"
        report = install_reference_skill(tmp_path, force=True)

        assert not report.ok
        assert topic.is_symlink()
        assert outside.read_text(encoding="utf-8") == sentinel

    def test_expected_file_directory_conflict_is_preserved(self, tmp_path):
        install_reference_skill(tmp_path)
        skill_dir = tmp_path / ".claude" / "skills" / REFERENCE_SKILL_ID
        topic = skill_dir / "references" / "maintenance.md"
        topic.unlink()
        topic.mkdir()

        report = install_reference_skill(tmp_path, force=True)

        assert not report.ok
        assert topic.is_dir()
        assert reference_skill_state(tmp_path) == "modified"
        assert any(
            issue["category"] == "unsafe_or_conflicting_entry"
            for issue in report.issues
        )

    def test_symlinked_topic_directory_cannot_receive_outside_writes(self, tmp_path):
        install_reference_skill(tmp_path)
        skill_dir = tmp_path / ".claude" / "skills" / REFERENCE_SKILL_ID
        references = skill_dir / "references"
        shutil.rmtree(references)
        outside = tmp_path / "outside"
        outside.mkdir()
        try:
            references.symlink_to(outside, target_is_directory=True)
        except OSError as exc:  # pragma: no cover - platform policy
            pytest.skip(f"symlinks unavailable: {exc}")

        report = install_reference_skill(tmp_path, force=True)

        assert not report.ok
        assert reference_skill_state(tmp_path) == "modified"
        assert list(outside.iterdir()) == []
        assert references.is_symlink()

    def test_symlinked_install_parent_cannot_receive_outside_writes(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        try:
            (project / ".llm-wiki").symlink_to(outside, target_is_directory=True)
        except OSError as exc:  # pragma: no cover - platform policy
            pytest.skip(f"symlinks unavailable: {exc}")

        report = install_reference_skill(project, agent="generic", force=True)

        assert not report.ok
        assert reference_skill_state(project, agent="generic") == "modified"
        assert list(outside.iterdir()) == []
        assert (project / ".llm-wiki").is_symlink()

    def test_state_checks_configured_target(self, tmp_path):
        target = Path("agent-skills")
        install_reference_skill(tmp_path, target=target)
        assert reference_skill_state(tmp_path, target=target) == "unmodified"
        assert reference_skill_state(tmp_path) == "absent"

    def test_agent_resolves_install_dir(self, tmp_path):
        install_reference_skill(tmp_path, agent="claude")
        assert (
            tmp_path / ".claude" / "skills" / REFERENCE_SKILL_ID / "SKILL.md"
        ).is_file()

        install_reference_skill(tmp_path, agent="cursor")
        generic_dir = tmp_path / GENERIC_INSTALL_TARGET / REFERENCE_SKILL_ID
        assert {
            path.relative_to(generic_dir).as_posix()
            for path in generic_dir.rglob("*")
            if path.is_file()
        } == set(REFERENCE_SKILL_FILES)
        assert reference_skill_state(tmp_path, agent="cursor") == "unmodified"
        assert reference_skill_state(tmp_path, agent="copilot") == "unmodified"
