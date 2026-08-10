"""Tests for commands/uninstall_cmd.py"""

import types
from pathlib import Path

import pytest

from llm_wiki_cli.config import PathValidationError
from llm_wiki_cli.commands import uninstall_cmd


def _make_args(**kwargs):
    defaults = {
        "wiki_dir": "docs/llm_wiki",
        "remove_wiki": False,
        "dry_run": False,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _setup_wiki_project(project_dir: Path):
    """Set up a project with wiki artifacts for uninstall testing."""
    # Wiki dir
    wiki = project_dir / "docs" / "llm_wiki"
    for d in ["entities", "modules", "workflows"]:
        (wiki / d).mkdir(parents=True, exist_ok=True)
    (wiki / "index.md").write_text("# Index\n")
    (wiki / "log.md").write_text("# Log\n")

    # Agent schema
    Path("CLAUDE.md").write_text(
        uninstall_cmd.CONSTRAINT_START
        + "\nstuff\n"
        + uninstall_cmd.CONSTRAINT_END
        + "\n"
    )

    # Git hooks
    hooks_dir = project_dir / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    (hooks_dir / "post-commit").write_text(
        "#!/bin/sh\n# LLM Wiki sync\nnohup llm-wiki trigger-agent &\n"
    )
    (hooks_dir / "post-commit").chmod(0o755)

    # Temp files
    (project_dir / ".git" / ".llm-wiki-agent").write_text("claude")
    (project_dir / ".git" / "llm-wiki-prompt.txt").write_text("prompt")
    (project_dir / ".git" / "llm-wiki.lock").write_text("")
    (project_dir / ".git" / "llm-wiki-breaker.json").write_text("{}")
    (project_dir / ".git" / "llm-wiki-sync.log").write_text("log")

    return wiki


class TestUninstallRemovesHooks:
    def test_removes_hook(self, tmp_project, capsys, monkeypatch):
        _setup_wiki_project(tmp_project)
        monkeypatch.setattr("builtins.input", lambda _: "y")

        args = _make_args()
        uninstall_cmd.run(args)
        capsys.readouterr()

        hook = tmp_project / ".git" / "hooks" / "post-commit"
        assert not hook.exists()

    def test_preserves_non_wiki_hook(self, tmp_project, capsys, monkeypatch):
        hooks_dir = tmp_project / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        (hooks_dir / "post-commit").write_text("#!/bin/sh\necho custom\n")

        monkeypatch.setattr("builtins.input", lambda _: "y")
        args = _make_args()
        uninstall_cmd.run(args)

        assert (hooks_dir / "post-commit").exists()

    @pytest.mark.parametrize(
        "content",
        [
            '#!/bin/sh\necho "check whether LLM Wiki is stale"\n',
            None,
        ],
    )
    def test_preserves_signature_false_positive_and_edited_managed_hook(
        self,
        tmp_project,
        capsys,
        monkeypatch,
        content: str | None,
    ):
        from llm_wiki_cli.commands import hook_cmd

        hooks_dir = tmp_project / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        actual = content or (
            hook_cmd._build_ide_post_commit("docs/llm_wiki") + "echo user-tail\n"
        )
        hook = hooks_dir / "post-commit"
        hook.write_text(actual, encoding="utf-8")
        (tmp_project / ".git" / "llm-wiki.lock").write_text("", encoding="utf-8")

        monkeypatch.setattr("builtins.input", lambda _: "y")
        uninstall_cmd.run(_make_args())

        assert hook.read_text(encoding="utf-8") == actual
        assert "SKIP hook post-commit" in capsys.readouterr().out

    def test_confirmation_cannot_promote_custom_hook_to_owned_removal(
        self,
        tmp_project,
        capsys,
        monkeypatch,
    ):
        hooks_dir = tmp_project / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook = hooks_dir / "post-commit"
        hook.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")
        lock = tmp_project / ".git" / "llm-wiki.lock"
        lock.write_text("lock", encoding="utf-8")
        promoted = "#!/bin/sh\n# LLM Wiki old hook\n"

        def promote_then_confirm(_prompt: str) -> str:
            hook.write_text(promoted, encoding="utf-8")
            return "y"

        monkeypatch.setattr("builtins.input", promote_then_confirm)
        with pytest.raises(SystemExit) as caught:
            uninstall_cmd.run(_make_args())

        assert caught.value.code == 2
        assert hook.read_text(encoding="utf-8") == promoted
        assert lock.read_text(encoding="utf-8") == "lock"
        assert "SKIP hook post-commit" in capsys.readouterr().out

    def test_confirmation_cannot_add_new_managed_schema_to_removal_plan(
        self,
        tmp_project,
        monkeypatch,
    ):
        lock = tmp_project / ".git" / "llm-wiki.lock"
        lock.write_text("lock", encoding="utf-8")
        schema = Path("AGENTS.md")

        def add_schema_then_confirm(_prompt: str) -> str:
            schema.write_text(
                uninstall_cmd.CONSTRAINT_START
                + "\nstuff\n"
                + uninstall_cmd.CONSTRAINT_END
                + "\n",
                encoding="utf-8",
            )
            return "y"

        monkeypatch.setattr("builtins.input", add_schema_then_confirm)
        with pytest.raises(SystemExit) as caught:
            uninstall_cmd.run(_make_args())

        assert caught.value.code == 2
        assert schema.exists()
        assert lock.read_text(encoding="utf-8") == "lock"

    def test_remove_wiki_rejects_claude_lifecycle_overlap_without_crashing(
        self,
        tmp_project,
        monkeypatch,
        capsys,
    ):
        from llm_wiki_cli.services.skills import provision_reference_skill

        wiki = Path(".claude")
        wiki.mkdir()
        (wiki / "index.md").write_text("# Custom wiki\n", encoding="utf-8")
        assert provision_reference_skill(agent="claude").ok
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args(wiki_dir=".claude", remove_wiki=True))

        output = capsys.readouterr().out
        assert "wiki root overlaps protected project or lifecycle paths" in output
        assert wiki.exists()
        assert (wiki / "index.md").exists()
        assert not (wiki / "skills/wiki-reference").exists()

    def test_remove_wiki_rejects_github_schema_and_workflow_overlap(
        self,
        tmp_project,
        monkeypatch,
        capsys,
    ):
        from llm_wiki_cli.services.ci_installer import (
            CHECKOUT_ACTION_REF,
            MANAGED_WORKFLOW_PATH,
            render_managed_workflow,
        )

        wiki = Path(".github")
        wiki.mkdir()
        (wiki / "index.md").write_text("# Custom wiki\n", encoding="utf-8")
        schema = wiki / "copilot-instructions.md"
        schema.write_text(
            uninstall_cmd.CONSTRAINT_START
            + "\nstuff\n"
            + uninstall_cmd.CONSTRAINT_END
            + "\n",
            encoding="utf-8",
        )
        workflow = Path(MANAGED_WORKFLOW_PATH)
        workflow.parent.mkdir(parents=True)
        workflow.write_bytes(
            render_managed_workflow(
                action_ref=CHECKOUT_ACTION_REF,
                wiki_dir="docs/llm_wiki",
            )
        )
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args(wiki_dir=".github", remove_wiki=True))

        output = capsys.readouterr().out
        assert "wiki root overlaps protected project or lifecycle paths" in output
        assert wiki.exists()
        assert (wiki / "index.md").exists()
        assert not schema.exists()
        assert not workflow.exists()

    @pytest.mark.parametrize(
        ("canonical", "variant"),
        [
            (".git", ".GIT"),
            (".claude/skills", ".CLAUDE/SKILLS"),
            (".llm-wiki/skills", ".LLM-WIKI/SKILLS"),
        ],
    )
    def test_remove_wiki_rejects_case_aliases_of_protected_roots(
        self,
        tmp_project,
        canonical: str,
        variant: str,
    ):
        canonical_path = Path(canonical)
        canonical_path.mkdir(parents=True, exist_ok=True)
        variant_path = Path(variant)
        if not variant_path.exists():
            pytest.skip("filesystem is case-sensitive; no case alias exists")

        inspection = uninstall_cmd._preflight_wiki_removal(
            variant_path,
            requested=True,
        )

        assert inspection.present
        assert not inspection.removable
        assert inspection.reason == (
            "wiki root overlaps protected project or lifecycle paths"
        )

    def test_remove_wiki_rejects_project_root_without_traversal(
        self,
        tmp_project,
    ):
        inspection = uninstall_cmd._preflight_wiki_removal(
            Path("."),
            requested=True,
        )

        assert inspection.present
        assert not inspection.removable
        assert inspection.reason == (
            "wiki root overlaps protected project or lifecycle paths"
        )


class TestUninstallStripsConstraints:
    def test_strips_wiki_block(self, tmp_project, capsys, monkeypatch):
        _setup_wiki_project(tmp_project)
        Path("CLAUDE.md").write_text(
            "# My Rules\n\n"
            + uninstall_cmd.CONSTRAINT_START
            + "\nwiki stuff\n"
            + uninstall_cmd.CONSTRAINT_END
            + "\n"
        )
        monkeypatch.setattr("builtins.input", lambda _: "y")

        args = _make_args()
        uninstall_cmd.run(args)

        content = Path("CLAUDE.md").read_text(encoding="utf-8")
        assert "My Rules" in content
        assert "LLM Wiki Maintainer Constraints" not in content

    def test_deletes_wiki_only_schema(self, tmp_project, capsys, monkeypatch):
        _setup_wiki_project(tmp_project)
        monkeypatch.setattr("builtins.input", lambda _: "y")

        args = _make_args()
        uninstall_cmd.run(args)

        # CLAUDE.md contained only wiki block, should be deleted
        assert not Path("CLAUDE.md").exists()

    def test_invalid_schema_encoding_fails_closed_before_preview_mutation(
        self, tmp_project, capsys
    ):
        wiki = _setup_wiki_project(tmp_project)
        schema = Path("CLAUDE.md")
        schema.write_bytes(b"\x81")
        hook = Path(".git/hooks/post-commit")
        config = Path(".git/.llm-wiki-agent")

        with pytest.raises(SystemExit) as caught:
            uninstall_cmd.run(_make_args(dry_run=True))

        assert caught.value.code == 2
        assert schema.read_bytes() == b"\x81"
        assert hook.exists()
        assert config.exists()
        assert wiki.exists()

    def test_schema_encoding_change_at_confirmation_prevents_all_removal(
        self, tmp_project, capsys, monkeypatch
    ):
        wiki = _setup_wiki_project(tmp_project)
        schema = Path("CLAUDE.md")
        hook = Path(".git/hooks/post-commit")
        hook_before = hook.read_bytes()
        config = Path(".git/.llm-wiki-agent")
        config_before = config.read_bytes()

        def corrupt_then_confirm(_prompt):
            schema.write_bytes(b"\x81")
            return "y"

        monkeypatch.setattr("builtins.input", corrupt_then_confirm)
        with pytest.raises(SystemExit) as caught:
            uninstall_cmd.run(_make_args())

        assert caught.value.code == 2
        assert schema.read_bytes() == b"\x81"
        assert hook.read_bytes() == hook_before
        assert config.read_bytes() == config_before
        assert wiki.exists()

    def test_strips_legacy_agents_md_wiki_block(self, tmp_project, capsys, monkeypatch):
        Path(".agents.md").write_text(
            "# Legacy Agent Rules\n\n"
            + uninstall_cmd.CONSTRAINT_START
            + "\nlegacy wiki stuff\n"
            + uninstall_cmd.CONSTRAINT_END
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args())

        content = Path(".agents.md").read_text(encoding="utf-8")
        assert "Legacy Agent Rules" in content
        assert "LLM Wiki Maintainer Constraints" not in content

    def test_strips_profiled_wiki_block(self, tmp_project, capsys, monkeypatch):
        from llm_wiki_cli.services.schema import (
            SchemaRenderProfile,
            build_schema_content,
        )

        Path("CLAUDE.md").write_text(
            "# My Rules\n\n"
            + build_schema_content(
                "claude",
                "docs/llm_wiki",
                render_profile=SchemaRenderProfile.COMPACT,
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args())

        content = Path("CLAUDE.md").read_text(encoding="utf-8")
        assert content == "# My Rules\n"
        assert "llm-wiki-schema:" not in content

    def test_schema_cleanup_failure_preserves_reference_and_runtime_config(
        self, tmp_project, capsys, monkeypatch
    ):
        from llm_wiki_cli.services.skills import install_reference_skill

        _setup_wiki_project(tmp_project)
        Path("CLAUDE.md").write_text(
            "# My Rules\n\n"
            + uninstall_cmd.CONSTRAINT_START
            + "\nlegacy wiki stuff\n"
            + uninstall_cmd.CONSTRAINT_END
            + "\n",
            encoding="utf-8",
        )
        install_reference_skill()
        reference = Path(".claude/skills/wiki-reference/SKILL.md")
        config = Path(".git/.llm-wiki-agent")
        monkeypatch.setattr("builtins.input", lambda _: "y")

        def fail_schema_write(_path, _content, **_kwargs):
            raise OSError("injected schema cleanup failure")

        monkeypatch.setattr(
            uninstall_cmd,
            "atomic_write_guarded_bytes",
            fail_schema_write,
        )

        with pytest.raises(
            uninstall_cmd.ManagedSchemaPathError,
            match="guarded cleanup",
        ):
            uninstall_cmd.run(_make_args())

        assert reference.is_file()
        assert config.is_file()

    @pytest.mark.parametrize(
        "malformed",
        [
            (
                uninstall_cmd.CONSTRAINT_START
                + "\nfirst\n"
                + uninstall_cmd.CONSTRAINT_END
                + "\n"
                + uninstall_cmd.CONSTRAINT_START
                + "\nsecond\n"
                + uninstall_cmd.CONSTRAINT_END
                + "\n"
            ),
            uninstall_cmd.CONSTRAINT_START + "\nunbalanced\n",
            (
                uninstall_cmd.CONSTRAINT_END
                + "\nreversed\n"
                + uninstall_cmd.CONSTRAINT_START
                + "\n"
            ),
        ],
        ids=["duplicate", "unbalanced", "reversed"],
    )
    def test_malformed_schema_aborts_before_any_uninstall_mutation(
        self, tmp_project, capsys, monkeypatch, malformed
    ):
        from llm_wiki_cli.services.skills import install_reference_skill

        _setup_wiki_project(tmp_project)
        schema = Path("CLAUDE.md")
        schema.write_text(malformed, encoding="utf-8")
        install_reference_skill()
        hook = Path(".git/hooks/post-commit")
        config = Path(".git/.llm-wiki-agent")
        runtime = Path(".git/llm-wiki-prompt.txt")
        reference = Path(".claude/skills/wiki-reference/SKILL.md")
        monkeypatch.setattr(
            "builtins.input",
            lambda _prompt: pytest.fail("malformed schema reached confirmation"),
        )

        with pytest.raises(SystemExit) as exc_info:
            uninstall_cmd.run(_make_args(remove_wiki=True))

        assert exc_info.value.code == 2
        assert "malformed" in capsys.readouterr().err
        assert schema.read_text(encoding="utf-8") == malformed
        assert hook.is_file()
        assert config.is_file()
        assert runtime.is_file()
        assert reference.is_file()

    def test_schema_strip_must_produce_an_absent_managed_block(
        self, tmp_project, capsys, monkeypatch
    ):
        from llm_wiki_cli.services.skills import install_reference_skill

        _setup_wiki_project(tmp_project)
        install_reference_skill()
        schema = Path("CLAUDE.md")
        original = schema.read_text(encoding="utf-8")
        monkeypatch.setattr(uninstall_cmd, "_strip_wiki_block", lambda content: content)
        monkeypatch.setattr(
            "builtins.input",
            lambda _prompt: pytest.fail("unsafe strip reached confirmation"),
        )

        with pytest.raises(SystemExit) as exc_info:
            uninstall_cmd.run(_make_args())

        assert exc_info.value.code == 2
        assert "could not be removed safely" in capsys.readouterr().err
        assert schema.read_text(encoding="utf-8") == original
        assert Path(".git/hooks/post-commit").is_file()
        assert Path(".git/.llm-wiki-agent").is_file()
        assert Path(".claude/skills/wiki-reference/SKILL.md").is_file()


class TestUninstallPathSafety:
    def test_symlinked_schema_parent_aborts_without_touching_outside_or_runtime(
        self, tmp_project, tmp_path, capsys, monkeypatch
    ):
        from llm_wiki_cli.services.skills import install_reference_skill

        _setup_wiki_project(tmp_project)
        install_reference_skill()
        outside = tmp_path / "outside-schema"
        outside.mkdir()
        outside_schema = outside / "copilot-instructions.md"
        outside_content = (
            uninstall_cmd.CONSTRAINT_START
            + "\noutside\n"
            + uninstall_cmd.CONSTRAINT_END
            + "\n"
        )
        outside_schema.write_text(outside_content, encoding="utf-8")
        try:
            Path(".github").symlink_to(outside, target_is_directory=True)
        except OSError as exc:  # pragma: no cover - platform policy
            pytest.skip(f"symlinks unavailable: {exc}")
        local_schema = Path("CLAUDE.md")
        local_content = local_schema.read_text(encoding="utf-8")
        monkeypatch.setattr(
            "builtins.input",
            lambda _prompt: pytest.fail("unsafe schema reached confirmation"),
        )

        with pytest.raises(SystemExit) as exc_info:
            uninstall_cmd.run(_make_args())

        assert exc_info.value.code == 2
        assert "unsafe component" in capsys.readouterr().err
        assert outside_schema.read_text(encoding="utf-8") == outside_content
        assert local_schema.read_text(encoding="utf-8") == local_content
        assert Path(".git/hooks/post-commit").is_file()
        assert Path(".git/.llm-wiki-agent").is_file()
        assert Path(".claude/skills/wiki-reference/SKILL.md").is_file()

    def test_symlinked_hook_aborts_without_reading_or_unlinking_outside(
        self, tmp_project, tmp_path, capsys, monkeypatch
    ):
        from llm_wiki_cli.services.skills import install_reference_skill

        _setup_wiki_project(tmp_project)
        install_reference_skill()
        outside_hook = tmp_path / "outside-post-commit"
        outside_content = "#!/bin/sh\n# LLM Wiki outside sentinel\n"
        outside_hook.write_text(outside_content, encoding="utf-8")
        hook = Path(".git/hooks/post-commit")
        hook.unlink()
        try:
            hook.symlink_to(outside_hook)
        except OSError as exc:  # pragma: no cover - platform policy
            pytest.skip(f"symlinks unavailable: {exc}")
        schema = Path("CLAUDE.md")
        schema_content = schema.read_text(encoding="utf-8")
        monkeypatch.setattr(
            "builtins.input",
            lambda _prompt: pytest.fail("unsafe hook reached confirmation"),
        )

        with pytest.raises(SystemExit) as exc_info:
            uninstall_cmd.run(_make_args())

        assert exc_info.value.code == 2
        assert "hook path contains unsafe component" in capsys.readouterr().err
        assert hook.is_symlink()
        assert outside_hook.read_text(encoding="utf-8") == outside_content
        assert schema.read_text(encoding="utf-8") == schema_content
        assert Path(".git/.llm-wiki-agent").is_file()
        assert Path(".claude/skills/wiki-reference/SKILL.md").is_file()

    def test_symlinked_hooks_directory_aborts_before_any_removal(
        self, tmp_project, tmp_path, capsys, monkeypatch
    ):
        from llm_wiki_cli.services.skills import install_reference_skill

        _setup_wiki_project(tmp_project)
        install_reference_skill()
        hook = Path(".git/hooks/post-commit")
        hooks_dir = hook.parent
        hooks_dir.rename(Path(".git/hooks-local"))
        outside_hooks = tmp_path / "outside-hooks"
        outside_hooks.mkdir()
        outside_hook = outside_hooks / "post-commit"
        outside_content = "#!/bin/sh\n# LLM Wiki outside sentinel\n"
        outside_hook.write_text(outside_content, encoding="utf-8")
        try:
            hooks_dir.symlink_to(outside_hooks, target_is_directory=True)
        except OSError as exc:  # pragma: no cover - platform policy
            pytest.skip(f"symlinks unavailable: {exc}")
        schema = Path("CLAUDE.md")
        schema_content = schema.read_text(encoding="utf-8")
        monkeypatch.setattr(
            "builtins.input",
            lambda _prompt: pytest.fail("unsafe hooks directory reached confirmation"),
        )

        with pytest.raises(SystemExit) as exc_info:
            uninstall_cmd.run(_make_args())

        assert exc_info.value.code == 2
        assert "hook path contains unsafe component" in capsys.readouterr().err
        assert outside_hook.read_text(encoding="utf-8") == outside_content
        assert schema.read_text(encoding="utf-8") == schema_content
        assert Path(".git/.llm-wiki-agent").is_file()
        assert Path(".claude/skills/wiki-reference/SKILL.md").is_file()


class TestUninstallKeepsWiki:
    def test_wiki_preserved_by_default(self, tmp_project, capsys, monkeypatch):
        wiki = _setup_wiki_project(tmp_project)
        monkeypatch.setattr("builtins.input", lambda _: "y")

        args = _make_args(remove_wiki=False)
        uninstall_cmd.run(args)

        assert wiki.exists()
        assert (wiki / "index.md").exists()

    def test_remove_wiki_flag(self, tmp_project, capsys, monkeypatch):
        wiki = _setup_wiki_project(tmp_project)
        monkeypatch.setattr("builtins.input", lambda _: "y")

        args = _make_args(remove_wiki=True)
        uninstall_cmd.run(args)

        assert not wiki.exists()

    def test_remove_wiki_aborts_if_unconfirmed_tree_entry_appears(
        self,
        tmp_project,
        monkeypatch,
    ):
        wiki = _setup_wiki_project(tmp_project)
        added = wiki / "entities" / "new-user-file.txt"
        lock = Path(".git/llm-wiki.lock")
        lock.write_text("keep", encoding="utf-8")

        def add_then_confirm(_prompt: str) -> str:
            added.write_text("unconfirmed\n", encoding="utf-8")
            return "y"

        monkeypatch.setattr("builtins.input", add_then_confirm)

        with pytest.raises(SystemExit) as caught:
            uninstall_cmd.run(_make_args(remove_wiki=True))

        assert caught.value.code == 2
        assert added.read_text(encoding="utf-8") == "unconfirmed\n"
        assert lock.read_text(encoding="utf-8") == "keep"

    @pytest.mark.parametrize("shape", ["file", "symlink"])
    def test_remove_wiki_preserves_unsafe_or_non_directory_root(
        self, tmp_project, capsys, monkeypatch, shape
    ):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.parent.mkdir(parents=True, exist_ok=True)
        outside = tmp_project / "outside-wiki-target"
        if shape == "file":
            wiki.write_text("sentinel", encoding="utf-8")
        else:
            outside.mkdir()
            (outside / "sentinel.md").write_text("outside", encoding="utf-8")
            wiki.symlink_to(outside, target_is_directory=True)
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args(remove_wiki=True))

        output = capsys.readouterr().out
        assert "KEPT" in output
        assert wiki.exists()
        if shape == "file":
            assert wiki.read_text(encoding="utf-8") == "sentinel"
        else:
            assert (outside / "sentinel.md").read_text(encoding="utf-8") == "outside"


class TestUninstallRuntimeArtifacts:
    def test_removes_all_runtime_artifacts(self, tmp_project, capsys, monkeypatch):
        _setup_wiki_project(tmp_project)
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args())

        for name in [
            ".llm-wiki-agent",
            "llm-wiki-prompt.txt",
            "llm-wiki.lock",
            "llm-wiki-breaker.json",
            "llm-wiki-sync.log",
        ]:
            assert not (tmp_project / ".git" / name).exists()

    def test_dry_run_lists_runtime_artifacts(self, tmp_project, capsys):
        _setup_wiki_project(tmp_project)

        uninstall_cmd.run(_make_args(dry_run=True))

        out = capsys.readouterr().out
        assert "Runtime Artifacts" in out
        assert ".git/.llm-wiki-agent" in out
        assert ".git/llm-wiki.lock" in out
        assert ".git/llm-wiki-breaker.json" in out

    def test_nonregular_config_is_preserved_without_partial_crash(
        self, tmp_project, capsys, monkeypatch
    ):
        _setup_wiki_project(tmp_project)
        config = Path(".git/.llm-wiki-agent")
        config.unlink()
        config.mkdir()
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args())

        output = capsys.readouterr().out
        assert config.is_dir()
        assert "KEPT (not a regular file)" in output
        assert not Path("CLAUDE.md").exists()

    def test_removes_non_git_fallback_config(self, tmp_path, capsys, monkeypatch):
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.chdir(project)
        wiki = project / "custom" / "wiki"
        wiki.mkdir(parents=True)
        config = wiki / ".llm-wiki-agent"
        config.write_text('{"agent": "generic"}\n', encoding="utf-8")
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args(wiki_dir="custom/wiki"))

        assert wiki.is_dir()
        assert not config.exists()
        assert "REMOVED: custom/wiki/.llm-wiki-agent" in capsys.readouterr().out

    def test_non_git_remove_wiki_includes_nested_fallback_config_once(
        self, tmp_path, capsys, monkeypatch
    ):
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.chdir(project)
        wiki = project / "custom" / "wiki"
        wiki.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n", encoding="utf-8")
        (wiki / ".llm-wiki-agent").write_text(
            '{"agent": "generic"}\n',
            encoding="utf-8",
        )
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args(wiki_dir="custom/wiki", remove_wiki=True))

        output = capsys.readouterr().out
        assert not wiki.exists()
        assert "REMOVED: custom/wiki/" in output
        assert "Uninstall complete" in output

    def test_removes_both_config_homes_after_non_git_to_git_transition(
        self, tmp_path, capsys, monkeypatch
    ):
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.chdir(project)
        wiki = Path("custom/wiki")
        wiki.mkdir(parents=True)
        fallback = wiki / ".llm-wiki-agent"
        fallback.write_text('{"agent": "generic"}\n', encoding="utf-8")
        git_config = Path(".git/.llm-wiki-agent")
        git_config.parent.mkdir(parents=True)
        git_config.write_text('{"agent": "claude"}\n', encoding="utf-8")
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args(wiki_dir=wiki.as_posix()))

        output = capsys.readouterr().out
        assert not fallback.exists()
        assert not git_config.exists()
        assert output.count("REMOVED: custom/wiki/.llm-wiki-agent") == 1
        assert output.count("REMOVED: .git/.llm-wiki-agent") == 1

    def test_absolute_git_wiki_alias_deduplicates_runtime_config(
        self, tmp_project, capsys, monkeypatch
    ):
        config = Path(".git/.llm-wiki-agent")
        config.write_text('{"agent": "generic"}\n', encoding="utf-8")
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(
            _make_args(wiki_dir=Path(".git").absolute(), remove_wiki=False)
        )

        output = capsys.readouterr().out
        assert not config.exists()
        assert output.count("REMOVED: .git/.llm-wiki-agent") == 1

    def test_hardlinked_config_homes_are_both_unlinked(
        self, tmp_project, capsys, monkeypatch
    ):
        git_config = Path(".git/.llm-wiki-agent")
        git_config.write_text('{"agent": "generic"}\n', encoding="utf-8")
        wiki = Path("custom/wiki")
        wiki.mkdir(parents=True)
        fallback = wiki / ".llm-wiki-agent"
        try:
            fallback.hardlink_to(git_config)
        except OSError as exc:  # pragma: no cover - platform policy
            pytest.skip(f"hard links unavailable: {exc}")
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args(wiki_dir=wiki.as_posix()))

        output = capsys.readouterr().out
        assert not git_config.exists()
        assert not fallback.exists()
        assert output.count("REMOVED:") == 2

    def test_config_inside_preserved_reference_tree_is_not_removed(
        self, tmp_project, capsys
    ):
        from llm_wiki_cli.services.skills import provision_reference_skill

        assert provision_reference_skill(agent="claude").ok
        reference = Path(".claude/skills/wiki-reference")
        nested_config = reference / ".llm-wiki-agent"
        nested_config.write_text('{"agent": "claude"}\n', encoding="utf-8")

        uninstall_cmd.run(_make_args(wiki_dir=reference.as_posix()))

        output = capsys.readouterr().out
        assert nested_config.exists()
        assert reference.exists()
        assert "inside a preserved managed-reference tree" in output
        assert "Nothing safely removable" in output

    def test_preserves_config_reached_through_symlinked_git_dir(
        self, tmp_path, capsys, monkeypatch
    ):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        project.mkdir()
        outside.mkdir()
        try:
            (project / ".git").symlink_to(outside, target_is_directory=True)
        except OSError as exc:  # pragma: no cover - platform policy
            pytest.skip(f"symlinks unavailable: {exc}")
        config = outside / ".llm-wiki-agent"
        config.write_text('{"agent": "generic"}\n', encoding="utf-8")
        monkeypatch.chdir(project)
        Path("AGENTS.md").write_text(
            uninstall_cmd.CONSTRAINT_START
            + "\nlegacy wiki stuff\n"
            + uninstall_cmd.CONSTRAINT_END
            + "\n",
            encoding="utf-8",
        )
        schema_content = Path("AGENTS.md").read_text(encoding="utf-8")
        monkeypatch.setattr("builtins.input", lambda _: "y")

        with pytest.raises(SystemExit) as exc_info:
            uninstall_cmd.run(_make_args())

        assert exc_info.value.code == 2
        assert config.read_text(encoding="utf-8") == '{"agent": "generic"}\n'
        assert Path("AGENTS.md").read_text(encoding="utf-8") == schema_content
        assert "hook path contains unsafe component" in capsys.readouterr().err

    def test_rejects_absolute_wiki_dir_outside_project(
        self, tmp_project, tmp_path, monkeypatch
    ):
        outside = tmp_path / "outside_wiki"
        outside.mkdir()
        monkeypatch.setattr("builtins.input", lambda _: "y")

        with pytest.raises(PathValidationError):
            uninstall_cmd.run(_make_args(wiki_dir=str(outside), remove_wiki=True))

        assert outside.exists()

    def test_rejects_traversal_wiki_dir_outside_project(self, tmp_project, monkeypatch):
        outside = tmp_project.parent / "outside_wiki"
        outside.mkdir()
        monkeypatch.setattr("builtins.input", lambda _: "y")

        with pytest.raises(PathValidationError):
            uninstall_cmd.run(_make_args(wiki_dir="../outside_wiki", remove_wiki=True))

        assert outside.exists()


class TestUninstallDryRun:
    def test_dry_run_no_changes(self, tmp_project, capsys):
        wiki = _setup_wiki_project(tmp_project)
        hook = tmp_project / ".git" / "hooks" / "post-commit"

        args = _make_args(dry_run=True)
        uninstall_cmd.run(args)

        # Everything should still exist
        assert wiki.exists()
        assert hook.exists()
        assert Path("CLAUDE.md").exists()


class TestUninstallReferenceSkill:
    def test_removes_unmodified_skill_copy(self, tmp_project, capsys, monkeypatch):
        from llm_wiki_cli.services.skills import (
            REFERENCE_SKILL_FILES,
            install_reference_skill,
        )

        _setup_wiki_project(tmp_project)
        install_reference_skill()
        skill_dir = Path(".claude/skills/wiki-reference")
        assert {
            path.relative_to(skill_dir).as_posix()
            for path in skill_dir.rglob("*")
            if path.is_file()
        } == set(REFERENCE_SKILL_FILES)
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args())

        assert not Path(".claude/skills/wiki-reference").exists()

    def test_unverifiable_current_tree_is_nonremovable_at_preview(
        self,
        tmp_project,
        capsys,
        monkeypatch,
    ):
        from llm_wiki_cli.services.skills import (
            ReferenceSkillState,
            install_reference_skill,
        )

        install_reference_skill(agent="claude")
        monkeypatch.setattr(
            uninstall_cmd,
            "guarded_tree_manifest",
            lambda _path: (_ for _ in ()).throw(OSError("unverifiable")),
        )

        plan = uninstall_cmd._preflight_reference_skills()

        current = next(item for item in plan if item.present)
        assert current.state is ReferenceSkillState.INSTALL_ERROR
        assert uninstall_cmd._remove_reference_skill(dry_run=True, plan=plan) == 0
        assert "unverifiable" in capsys.readouterr().out

    def test_keeps_modified_skill_copy(self, tmp_project, capsys, monkeypatch):
        from llm_wiki_cli.services.skills import install_reference_skill

        _setup_wiki_project(tmp_project)
        install_reference_skill()
        ref = Path(".claude/skills/wiki-reference/references/maintenance.md")
        ref.write_text("local notes\n", encoding="utf-8")
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args())

        assert ref.read_text(encoding="utf-8") == "local notes\n"
        assert "locally modified" in capsys.readouterr().out

    def test_keeps_incomplete_skill_tree(self, tmp_project, capsys, monkeypatch):
        from llm_wiki_cli.services.skills import install_reference_skill

        _setup_wiki_project(tmp_project)
        install_reference_skill()
        skill_dir = Path(".claude/skills/wiki-reference")
        missing = skill_dir / "references" / "governance.md"
        missing.unlink()
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args())

        assert skill_dir.is_dir()
        assert not missing.exists()
        assert "locally modified" in capsys.readouterr().out

    def test_keeps_tree_with_extra_topic(self, tmp_project, capsys, monkeypatch):
        from llm_wiki_cli.services.skills import install_reference_skill

        _setup_wiki_project(tmp_project)
        install_reference_skill()
        skill_dir = Path(".claude/skills/wiki-reference")
        extra = skill_dir / "references" / "local-notes.md"
        extra.write_text("notes\n", encoding="utf-8")
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args())

        assert extra.read_text(encoding="utf-8") == "notes\n"
        assert "locally modified" in capsys.readouterr().out

    def test_sweeps_all_known_skill_locations(self, tmp_project, capsys, monkeypatch):
        from llm_wiki_cli.services.skills import install_reference_skill

        _setup_wiki_project(tmp_project)
        install_reference_skill(agent="claude")
        install_reference_skill(agent="generic")
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args())

        assert not Path(".claude/skills/wiki-reference").exists()
        assert not Path(".llm-wiki/skills/wiki-reference").exists()

    @pytest.mark.parametrize(
        "state_name",
        [
            "ABSENT",
            "LOCALLY_MODIFIED",
            "INCOMPLETE",
            "PACKAGE_MISSING",
            "INSTALL_ERROR",
        ],
    )
    def test_preserves_every_noncurrent_structured_state(
        self, tmp_project, capsys, monkeypatch, state_name
    ):
        from llm_wiki_cli.services.skills import (
            ReferenceSkillReason,
            ReferenceSkillState,
            ReferenceSkillVerification,
        )

        skill_dir = Path(".claude/skills/wiki-reference")
        skill_dir.mkdir(parents=True)
        sentinel = skill_dir / "local.md"
        sentinel.write_text("local\n", encoding="utf-8")
        state = ReferenceSkillState[state_name]
        reason = {
            ReferenceSkillState.ABSENT: ReferenceSkillReason.ABSENT,
            ReferenceSkillState.LOCALLY_MODIFIED: (
                ReferenceSkillReason.LOCALLY_MODIFIED
            ),
            ReferenceSkillState.INCOMPLETE: ReferenceSkillReason.INCOMPLETE,
            ReferenceSkillState.PACKAGE_MISSING: ReferenceSkillReason.PACKAGE_MISSING,
            ReferenceSkillState.INSTALL_ERROR: ReferenceSkillReason.INSTALL_ERROR,
        }[state]
        verification = ReferenceSkillVerification(state, reason, skill_dir)
        monkeypatch.setattr(
            uninstall_cmd,
            "KNOWN_INSTALL_TARGETS",
            (Path(".claude/skills"),),
        )
        monkeypatch.setattr(
            uninstall_cmd,
            "verify_reference_skill",
            lambda **_kwargs: verification,
        )

        assert uninstall_cmd._remove_reference_skill() == 0

        assert sentinel.read_text(encoding="utf-8") == "local\n"
        assert reason.value in capsys.readouterr().out
