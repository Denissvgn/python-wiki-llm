"""Tests for commands/generate_prompt_cmd.py"""

from __future__ import annotations

import ast
import inspect
import json
import os
import stat
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import generate_prompt_cmd
from llm_wiki_cli.services.documentation_queries import DocumentationQueryError
from llm_wiki_cli.services.source_selection import (
    SOURCE_SELECTION_SCHEMA_VERSION,
    resolve_source_selection,
    with_source_selection_generation_input,
)
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from llm_wiki_cli.services.sync_manifest import SyncManifest
from llm_wiki_cli.services.wiki_git_policy import (
    WikiGitDisposition,
    WikiGitPolicy,
    classify_wiki_git_policy,
)


def _make_args(**kwargs):
    defaults = {
        "wiki_dir": "docs/llm_wiki",
        "src_dir": ".",
        "output": ".git/llm-wiki-prompt.txt",
        "print_prompt": False,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    function_node = ast.parse(source).body[0]
    assert isinstance(function_node, ast.FunctionDef)
    body = list(function_node.body)
    first_body_line = min(stmt.lineno for stmt in body)
    last_body_line = max(stmt.end_lineno or stmt.lineno for stmt in body)
    return last_body_line - first_body_line + 1


def _policy(disposition: WikiGitDisposition) -> WikiGitPolicy:
    return WikiGitPolicy(
        disposition=disposition,
        reason=disposition.value,
        repository_root=Path.cwd(),
        wiki_path="docs/llm_wiki",
    )


def _write_selection_profile(path: Path, include: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": [include],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )


@pytest.fixture(autouse=True)
def _default_included_policy(monkeypatch):
    monkeypatch.setattr(
        generate_prompt_cmd,
        "classify_wiki_git_policy",
        lambda *_args, **_kwargs: _policy(WikiGitDisposition.INCLUDED),
    )


class TestGeneratePromptWritesFile:
    def test_creates_output_file(self, tmp_project):
        args = _make_args()
        generate_prompt_cmd.run(args)

        out = Path(".git/llm-wiki-prompt.txt")
        assert out.exists()
        assert out.stat().st_size > 0

    def test_output_file_is_owner_only(self, tmp_project):
        args = _make_args()
        generate_prompt_cmd.run(args)

        mode = stat.S_IMODE(Path(".git/llm-wiki-prompt.txt").stat().st_mode)
        if os.name == "nt":
            assert Path(".git/llm-wiki-prompt.txt").is_file()
        else:
            assert mode == 0o600

    def test_prompt_contains_wiki_dir(self, tmp_project):
        args = _make_args(wiki_dir="my_docs/wiki")
        generate_prompt_cmd.run(args)

        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "my_docs/wiki" in content

    def test_prompt_contains_extract_command(self, tmp_project):
        args = _make_args()
        generate_prompt_cmd.run(args)

        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "llm-wiki extract" in content
        assert "--changed" in content
        assert "--summary" in content

    def test_custom_output_path(self, tmp_project, tmp_path):
        out_file = str(tmp_path / "my_prompt.txt")
        args = _make_args(output=out_file)
        generate_prompt_cmd.run(args)

        assert Path(out_file).exists()

    def test_prompt_quotes_paths_with_spaces(self, tmp_project):
        args = _make_args(wiki_dir="my docs/wiki", src_dir="src dir")
        generate_prompt_cmd.run(args)

        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "llm-wiki extract --src-dir 'src dir' --changed --summary" in content
        assert (
            "llm-wiki lint --jobs 1 --wiki-dir 'my docs/wiki' --src-dir 'src dir'"
            in content
        )
        assert "git add -- 'my docs/wiki/'" in content
        assert (
            "git check-ignore --no-index -- 'my docs/wiki/' "
            "'my docs/wiki/index.md'"
        ) in content
        assert "CHANGELOG.md" not in content.split("git add --", 1)[1].splitlines()[0]

    def test_ignored_wiki_run_emits_local_only_handoff(
        self, tmp_project, monkeypatch
    ):
        (tmp_project / ".gitignore").write_text(
            "docs/llm_wiki/\n", encoding="utf-8"
        )
        monkeypatch.setattr(
            generate_prompt_cmd,
            "classify_wiki_git_policy",
            classify_wiki_git_policy,
        )

        generate_prompt_cmd.run(_make_args())

        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "Wiki Git disposition: **ignored**" in content
        assert "\ngit add " not in content
        assert "\nLLM_WIKI_AUTO_COMMIT" not in content
        assert "local-only" in content

    def test_output_message_quotes_output_path_with_spaces(self, tmp_project, capsys):
        args = _make_args(output=".git/wiki prompt.txt")
        generate_prompt_cmd.run(args)

        out = capsys.readouterr().out
        assert "cat '.git/wiki prompt.txt'" in out

    def test_redacts_credential_like_diff_values_and_appends_count(
        self, tmp_project, monkeypatch
    ):
        secrets = (
            "sk-abcdefghijklmnopqrstuvwxyz",
            "Bearer abc",
            "ghp_abcdefghijklmnopqrstuvwxyz",
        )
        diff = "\n".join(f"+{value}" for value in secrets)
        monkeypatch.setattr(generate_prompt_cmd, "_git_diff", lambda: diff)
        monkeypatch.setattr(
            generate_prompt_cmd,
            "render_prompt_template",
            lambda _template, values: "Git diff:\n" + values["diff"] + "\n",
        )
        args = _make_args(template="test-template")

        generate_prompt_cmd.run(args)

        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert not any(secret in content for secret in secrets)
        assert content.count("[REDACTED:credential]") == 3
        assert content.endswith("[3 credential-like values redacted]\n")

    def test_configured_prompt_pins_profile_and_uses_selected_diffs_only(
        self, tmp_project, monkeypatch
    ):
        Path("selected").mkdir()
        Path("excluded").mkdir()
        Path("selected/app.py").write_text("VALUE = 1\n", encoding="utf-8")
        Path("excluded/secret.py").write_text("SECRET = 1\n", encoding="utf-8")
        profile = Path("config/team selection.json")
        _write_selection_profile(profile, "selected")
        policy = resolve_source_selection(".", profile.as_posix())
        assert policy is not None
        snapshot = build_source_snapshot(
            ".",
            source_selection=profile.as_posix(),
        )
        wiki = Path("docs/llm_wiki")
        wiki.mkdir(parents=True)
        SyncManifest(
            generation_inputs=with_source_selection_generation_input(
                {},
                policy.identity,
                snapshot.source_selection_inputs,
            )
        ).save(wiki)
        diff = (
            "diff --git a/selected/app.py b/selected/app.py\n"
            "--- a/selected/app.py\n+++ b/selected/app.py\n@@ -1 +1 @@\n"
            "+VALUE = 2\n"
            "diff --git a/excluded/secret.py b/excluded/secret.py\n"
            "--- a/excluded/secret.py\n+++ b/excluded/secret.py\n@@ -1 +1 @@\n"
            "+SECRET = 2\n"
        )
        monkeypatch.setattr(generate_prompt_cmd, "_git_diff", lambda: diff)

        generate_prompt_cmd.run(
            _make_args(source_selection=profile.as_posix())
        )

        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "--source-selection 'config/team selection.json'" in content
        assert "Never run an unrestricted Git diff" in content
        assert "git diff --stat HEAD~1..HEAD" not in content
        assert "excluded/secret.py" not in content
        selected_diff = generate_prompt_cmd._selected_prompt_diff(
            diff,
            src_dir=".",
            wiki_dir=wiki.as_posix(),
            source_selection=profile.as_posix(),
        )
        assert "selected/app.py" in selected_diff
        assert "excluded/secret.py" not in selected_diff

    def test_external_prompt_recipes_preserve_source_authorization(
        self, tmp_project, monkeypatch
    ):
        external = tmp_project.parent / "external source"
        selected = external / "selected"
        selected.mkdir(parents=True)
        (selected / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        profile = external / "selection.json"
        _write_selection_profile(profile, "selected")
        snapshot = build_source_snapshot(
            external,
            source_selection="selection.json",
        )
        wiki = Path("docs/llm_wiki")
        wiki.mkdir(parents=True)
        SyncManifest(
            generation_inputs=with_source_selection_generation_input(
                {},
                snapshot.source_selection_identity,
                snapshot.source_selection_inputs,
            )
        ).save(wiki)
        monkeypatch.setattr(
            generate_prompt_cmd,
            "_prompt_git_diff",
            lambda _src_dir: (
                "diff --git a/selected/app.py b/selected/app.py\n"
                "--- a/selected/app.py\n"
                "+++ b/selected/app.py\n"
                "@@ -1 +1 @@\n"
                "+VALUE = 2\n"
            ),
        )

        generate_prompt_cmd.run(
            _make_args(
                src_dir=str(external),
                allow_external_src=True,
                source_selection="selection.json",
            )
        )

        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        source_commands = [
            line
            for line in content.splitlines()
            if line.startswith(("llm-wiki extract", "llm-wiki sync", "llm-wiki lint"))
        ]
        assert source_commands
        assert all("--allow-external-src" in line for line in source_commands)
        assert all("--source-selection selection.json" in line for line in source_commands)
        assert f"git -C '{external}' diff" in content
        assert "\ngit diff" not in content

    def test_selection_preflight_runs_before_git_diff(
        self, tmp_project, monkeypatch
    ):
        Path("selected-a").mkdir()
        Path("selected-b").mkdir()
        Path("selected-a/app.py").write_text("VALUE = 1\n", encoding="utf-8")
        Path("selected-b/app.py").write_text("VALUE = 2\n", encoding="utf-8")
        profile_a = Path("config/a.json")
        profile_b = Path("config/b.json")
        _write_selection_profile(profile_a, "selected-a")
        _write_selection_profile(profile_b, "selected-b")
        policy_a = resolve_source_selection(".", profile_a.as_posix())
        assert policy_a is not None
        snapshot_a = build_source_snapshot(
            ".",
            source_selection=profile_a.as_posix(),
        )
        wiki = Path("docs/llm_wiki")
        wiki.mkdir(parents=True)
        SyncManifest(
            generation_inputs=with_source_selection_generation_input(
                {},
                policy_a.identity,
                snapshot_a.source_selection_inputs,
            )
        ).save(wiki)
        monkeypatch.setattr(
            generate_prompt_cmd,
            "_git_diff",
            lambda: pytest.fail("Git diff must not run before selection validation"),
        )

        with pytest.raises(DocumentationQueryError, match="llm-wiki sync"):
            generate_prompt_cmd.run(
                _make_args(source_selection=profile_b.as_posix())
            )

    def test_omitted_persisted_profile_fails_before_source_snapshot(
        self, tmp_project, monkeypatch
    ):
        Path("selected").mkdir()
        Path("selected/app.py").write_text("VALUE = 1\n", encoding="utf-8")
        profile = Path("config/explicit.json")
        _write_selection_profile(profile, "selected")
        snapshot = build_source_snapshot(
            ".",
            source_selection=profile.as_posix(),
        )
        wiki = Path("docs/llm_wiki")
        wiki.mkdir(parents=True)
        SyncManifest(
            generation_inputs=with_source_selection_generation_input(
                {},
                snapshot.source_selection_identity,
                snapshot.source_selection_inputs,
            )
        ).save(wiki)
        monkeypatch.setattr(
            generate_prompt_cmd,
            "build_source_snapshot",
            lambda *_args, **_kwargs: pytest.fail(
                "source snapshot must not be built before persisted-boundary validation"
            ),
        )
        monkeypatch.setattr(
            generate_prompt_cmd,
            "_prompt_git_diff",
            lambda _src_dir: pytest.fail(
                "Git diff must not run before persisted-boundary validation"
            ),
        )

        with pytest.raises(DocumentationQueryError, match="source-selection"):
            generate_prompt_cmd.run(_make_args())

    def test_changed_selection_controls_fail_before_source_snapshot(
        self, tmp_project, monkeypatch
    ):
        selected = Path("selected")
        selected.mkdir()
        (selected / "keep.py").write_text("KEEP = 1\n", encoding="utf-8")
        (selected / "secret.py").write_text("SECRET = 1\n", encoding="utf-8")
        ignore = selected / ".gitignore"
        ignore.write_text("secret.py\n", encoding="utf-8")
        profile = Path("config/explicit.json")
        _write_selection_profile(profile, "selected")
        snapshot = build_source_snapshot(
            ".",
            source_selection=profile.as_posix(),
        )
        wiki = Path("docs/llm_wiki")
        wiki.mkdir(parents=True)
        SyncManifest(
            generation_inputs=with_source_selection_generation_input(
                {},
                snapshot.source_selection_identity,
                snapshot.source_selection_inputs,
            )
        ).save(wiki)
        ignore.write_text("", encoding="utf-8")
        monkeypatch.setattr(
            generate_prompt_cmd,
            "build_source_snapshot",
            lambda *_args, **_kwargs: pytest.fail(
                "source snapshot must not be built after selection controls change"
            ),
        )

        with pytest.raises(DocumentationQueryError, match="inputs changed"):
            generate_prompt_cmd.run(
                _make_args(source_selection=profile.as_posix())
            )


class TestGeneratePromptPrintMode:
    def test_print_goes_to_stdout(self, tmp_project, capsys):
        args = _make_args(print_prompt=True)
        generate_prompt_cmd.run(args)

        out = capsys.readouterr().out
        assert "Wiki synchronizer" in out
        # No file should be written
        assert not Path(".git/llm-wiki-prompt.txt").exists()


class TestGeneratePromptBuildPrompt:
    def test_build_prompt_stays_decomposed(self):
        assert _body_line_count(generate_prompt_cmd._build_prompt) <= 40

    def test_prompt_contains_section_headings(self, tmp_project):
        """Prompt should have the goal-driven section headings."""
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "## Context" in content
        assert "## Success Criteria" in content
        assert "## Verify & Handoff" in content
        assert "## Repository Policy & Handoff" in content

    def test_prompt_contains_lint_success_criterion(self, tmp_project):
        """Prompt should frame lint exit 0 as a success criterion."""
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "llm-wiki lint" in content
        assert "exits 0" in content

    def test_prompt_contains_log_criterion(self, tmp_project):
        """Prompt should require a log.md entry as a success criterion."""
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "log.md" in content
        assert "new entry" in content

    def test_prompt_contains_only_affected_criterion(self, tmp_project):
        """Prompt should instruct agents to only modify affected pages."""
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "Only affected pages" in content

    def test_prompt_runs_sync_before_semantic_pass(self, tmp_project):
        """Prompt should scope first, then sync before semantic enrichment."""
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert (
            "llm-wiki sync --jobs 1 --wiki-dir docs/llm_wiki --src-dir ." in content
        )
        assert "## Semantic Pass" in content
        assert "Semantic pass complete" in content
        assert "_Auto-generated from ..._" in content
        assert "generated AST/docstring skeletons" in content
        assert content.index("extract --src-dir . --changed --summary") < content.index(
            "llm-wiki sync --jobs 1"
        )
        assert content.index("git diff --stat HEAD~1..HEAD") < content.index(
            "llm-wiki sync --jobs 1"
        )

    def test_prompt_uses_stat_then_targeted_git_diffs(self, tmp_project):
        """Prompt should scope diff reading from a stat and affected paths."""
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "git diff --stat HEAD~1..HEAD" in content
        assert "git diff HEAD~1..HEAD -- path/to/affected-file" in content
        assert "Full diff of the last commit" not in content

    def test_prompt_serializes_heavy_gates_without_context_scan(self, tmp_project):
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        text = " ".join(content.split())

        assert "supervisor owns this heavy-gate schedule" in text
        assert "Do not launch context, full tests, coverage, builds" in text
        assert "unless the supervisor explicitly assigns" in text
        assert "unconditional repository-wide context scan" in text
        assert "llm-wiki context" not in content
        assert "llm-wiki lint --jobs 1" in content

    def test_prompt_commit_uses_auto_commit_guard(self, tmp_project):
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert (
            'LLM_WIKI_AUTO_COMMIT=1 git commit -m "docs(wiki): auto-update [bot]"'
            in content
        )

    @pytest.mark.parametrize(
        "disposition",
        [WikiGitDisposition.IGNORED, WikiGitDisposition.INDETERMINATE],
    )
    def test_local_only_policy_omits_git_mutation_commands(
        self, tmp_project, disposition
    ):
        prompt = generate_prompt_cmd._build_prompt(
            "docs/llm_wiki",
            ".",
            change_type="generic",
            diff_text="",
            policy=_policy(disposition),
        )

        assert f"Wiki Git disposition: **{disposition.value}**" in prompt
        assert "\ngit add " not in prompt
        assert "\nLLM_WIKI_AUTO_COMMIT" not in prompt
        assert "local-only" in prompt
        assert "do not stage, commit, push, tag" in prompt

    def test_included_handoff_is_conditional_and_rechecked(self, tmp_project):
        prompt = generate_prompt_cmd._build_prompt(
            "docs/llm_wiki",
            ".",
            change_type="generic",
            diff_text="",
            policy=_policy(WikiGitDisposition.INCLUDED),
        )

        assert (
            "git check-ignore --no-index -- docs/llm_wiki/ "
            "docs/llm_wiki/index.md"
        ) in prompt
        assert "Exit status 1" in prompt
        assert "Exit status 0 or any other outcome" in prompt
        assert "eligibility, not authorization" in prompt
        assert "git add -- docs/llm_wiki/" in prompt
        assert "git add -- docs/llm_wiki/ CHANGELOG.md" not in prompt
        assert "Never force-add" in prompt
