"""Tests for the bundled wiki-reference skill and its provisioning.

The agent constraint block points at this skill for contract-level detail,
so its reference.md must keep every contract sentence that used to live in
the injected block (progressive disclosure must not lose content).
"""

from pathlib import Path

from llm_wiki_cli.services.skills import (
    BUNDLED_SKILLS_ROOT,
    REFERENCE_SKILL_ID,
    install_reference_skill,
    list_bundled_skills,
    reference_skill_state,
)


def _reference_text() -> str:
    path = BUNDLED_SKILLS_ROOT / REFERENCE_SKILL_ID / "reference.md"
    return path.read_text(encoding="utf-8")


def _squash_ws(content: str) -> str:
    return " ".join(content.split())


def test_wiki_reference_is_bundled_with_frontmatter():
    skills = {s.skill_id: s for s in list_bundled_skills()}
    assert REFERENCE_SKILL_ID in skills
    skill = skills[REFERENCE_SKILL_ID]
    assert skill.description
    assert "SKILL.md" in skill.files
    assert "reference.md" in skill.files


def test_reference_documents_extractor_helpers_and_toolchains():
    content = _reference_text()

    assert "llm-wiki prepare-extractors --src-dir ." in content
    assert "llm-wiki prepare-extractors --cache-dir .cache/llm-wiki-helpers" in content
    assert (
        "llm-wiki sync --cache-dir .cache/llm-wiki-inventory "
        "--helper-cache-dir .cache/llm-wiki-helpers" in content
    )
    assert "--include-tests go" in content
    assert "LLM_WIKI_GO=/path/to/go" in content
    assert "LLM_WIKI_GHC=/path/to/ghc" in content
    assert "prepared TypeScript/JavaScript/Go/Rust/Haskell helpers" in content


def test_reference_documents_haskell_contract():
    content = _reference_text()
    text = _squash_ws(content)

    assert "normal CLI extraction invokes the prepared Haskell helper" in content
    assert (
        "syntax-only Haskell inventory without typechecking the target project" in text
    )
    assert "does not start Haskell Language Server" in text
    assert (
        "Haskell dependency reconciliation reads Cabal `build-depends` statically"
        in text
    )
    assert (
        "Stack `extra-deps` and Nix package hints as optional advisory metadata" in text
    )
    assert "Unknown Haskell imports are ignored rather than guessed" in text
    assert "GHC 9.6.x is the supported Haskell helper toolchain" in text
    assert "newer GHC 9.x releases are best-effort" in text
    assert "Generated Haskell module pages render declared module names" in content
    assert "Haskell lockfile pinning is intentionally out of scope" in text


def test_reference_documents_haskell_inventory_schema():
    content = _reference_text()
    text = _squash_ws(content)

    assert "Haskell inventory stays additive under `llm-wiki-extract/v1`" in text
    assert (
        "Haskell file entries include `language`, `imports`, `classes`, and `functions`"
        in text
    )
    assert "`module` is present when the source declares one" in text
    assert "`module`, `qualified`, `alias`, and `line`" in content
    assert "`classes` stores type-oriented declarations" in text
    assert "`data`, `newtype`, `type`, `class`, or `instance`" in content
    assert "`functions` stores top-level signatures, functions, and values" in text
    assert "`signature`, `function`, or `value`" in content
    assert "`language_pragmas`, `exports`, and `deriving`" in text


def test_reference_documents_dependency_reconciliation_and_flows():
    content = _reference_text()
    text = _squash_ws(content)

    assert "nested Python `pyproject.toml` and `requirements*.txt` files" in text
    assert "Go `// indirect` requirements are transitive" in text
    assert "optional lockfile-backed `versions`" in content
    assert "Raw Node `http.createServer` and `https.createServer` calls" in content
    assert "javascript_flow_unsupported" in content


def test_reference_documents_site_export_and_context():
    content = _reference_text()

    assert (
        "Docusaurus exports include generated front matter and sidebars.json" in content
    )
    assert "--profile reference" in content
    assert "--file-friendly" in content
    assert (
        "llm-wiki context --budget 8000 --src-dir . "
        "--format markdown --focus changed --read-only" in content
    )
    assert "budget and focus bound emitted output after a full" in content
    assert "do not bound scan work" in content
    assert "For a narrow task" in content
    assert "skip context" in content


def test_reference_documents_resource_aware_execution():
    content = _reference_text()
    text = _squash_ws(content)

    assert "## Resource-aware execution" in content
    for environment in [
        "Interactive IDE or unknown capacity",
        "Isolated terminal",
        "Controlled CI",
    ]:
        assert environment in content
    assert "The supervisor owns the schedule" in content
    assert "must not launch heavy gates unless explicitly assigned" in content
    assert "`requested_jobs` is the user's raw selection" in content
    assert "`resolved_jobs` is the integer concurrency ceiling" in content
    assert "`effective_workers` is the maximum number" in content
    assert "absent languages, cache-elided work, sequential-only" in text
    assert "not a global host-resource cap" in content
    assert "one later manual retry may use `--jobs 1`" in text
    assert "not proof that `llm-wiki` leaked a watcher" in text


class TestReferenceSkillProvisioning:
    def test_install_writes_bundled_files(self, tmp_path):
        report = install_reference_skill(tmp_path)

        assert report.ok
        skill_dir = tmp_path / ".claude" / "skills" / REFERENCE_SKILL_ID
        assert (skill_dir / "SKILL.md").is_file()
        assert (skill_dir / "reference.md").is_file()
        assert reference_skill_state(tmp_path) == "unmodified"

    def test_state_absent_before_install(self, tmp_path):
        assert reference_skill_state(tmp_path) == "absent"

    def test_local_edit_marks_modified_and_force_refresh_restores(self, tmp_path):
        install_reference_skill(tmp_path)
        ref_path = (
            tmp_path / ".claude" / "skills" / REFERENCE_SKILL_ID / "reference.md"
        )
        ref_path.write_text("local notes\n", encoding="utf-8")
        assert reference_skill_state(tmp_path) == "modified"

        # Without force the differing file is preserved and reported
        report = install_reference_skill(tmp_path)
        assert not report.ok
        assert ref_path.read_text(encoding="utf-8") == "local notes\n"

        report = install_reference_skill(tmp_path, force=True)
        assert report.ok
        assert reference_skill_state(tmp_path) == "unmodified"

    def test_extra_file_marks_modified(self, tmp_path):
        install_reference_skill(tmp_path)
        skill_dir = tmp_path / ".claude" / "skills" / REFERENCE_SKILL_ID
        (skill_dir / "notes.md").write_text("extra\n", encoding="utf-8")
        assert reference_skill_state(tmp_path) == "modified"

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
        assert (
            tmp_path / ".llm-wiki" / "skills" / REFERENCE_SKILL_ID / "SKILL.md"
        ).is_file()
        assert reference_skill_state(tmp_path, agent="cursor") == "unmodified"
        assert reference_skill_state(tmp_path, agent="copilot") == "unmodified"
