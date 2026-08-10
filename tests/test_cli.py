"""Tests for llm_wiki_cli.cli."""

from __future__ import annotations

import ast
import errno
import inspect
import textwrap
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.config import read_config


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    function_node = ast.parse(source).body[0]
    assert isinstance(function_node, ast.FunctionDef)
    body = [
        stmt
        for stmt in function_node.body
        if not (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        )
    ]
    first_body_line = min(stmt.lineno for stmt in body)
    last_body_line = max(stmt.end_lineno or stmt.lineno for stmt in body)
    return last_body_line - first_body_line + 1


class TestCliMainStructure:
    def test_main_stays_decomposed(self):
        assert _body_line_count(cli.main) <= 25


@pytest.mark.parametrize("command", ["init", "upgrade"])
def test_issue_reporting_flags_are_documented(command, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["llm-wiki", command, "--help"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--issue-reporting" in help_text
    assert "--no-issue-reporting" in help_text
    assert "local" in help_text
    assert "does not submit" in help_text


@pytest.mark.parametrize(
    ("command", "module_name"),
    [("init", "init_cmd"), ("upgrade", "upgrade_cmd")],
)
@pytest.mark.parametrize(
    ("flag", "expected"),
    [
        (None, None),
        ("--issue-reporting", True),
        ("--no-issue-reporting", False),
    ],
)
def test_issue_reporting_flags_parse(command, module_name, flag, expected, monkeypatch):
    seen = {}
    command_module = getattr(cli, module_name)
    monkeypatch.setattr(
        command_module,
        "run",
        lambda args: seen.setdefault("issue_reporting", args.issue_reporting),
    )
    argv = ["llm-wiki", command]
    if flag is not None:
        argv.append(flag)
    monkeypatch.setattr("sys.argv", argv)

    cli.main()

    assert seen["issue_reporting"] is expected


def test_upgrade_cleanup_source_agent_is_explicit_and_bounded(monkeypatch) -> None:
    seen: dict[str, object] = {}
    monkeypatch.setattr(
        cli.upgrade_cmd,
        "run",
        lambda args: seen.update(vars(args)),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "llm-wiki",
            "upgrade",
            "--agent",
            "claude",
            "--cleanup-source-agent",
            "generic",
            "--skills",
        ],
    )

    cli.main()

    assert seen["agent"] == "claude"
    assert seen["cleanup_source_agent"] == "generic"
    assert seen["skills"] is True


@pytest.mark.parametrize("command", ["init", "upgrade"])
def test_issue_reporting_flags_are_mutually_exclusive(command, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "llm-wiki",
            command,
            "--issue-reporting",
            "--no-issue-reporting",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_init_issue_toggle_without_agent_reuses_stored_agent(
    tmp_project, monkeypatch
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "llm-wiki",
            "init",
            "--agent",
            "copilot",
            "--issue-reporting",
            "--no-skills",
        ],
    )
    cli.main()

    schema = Path(".github/copilot-instructions.md")
    assert "## Report llm-wiki tool issues" in schema.read_text(encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        ["llm-wiki", "init", "--no-issue-reporting", "--no-skills"],
    )
    cli.main()

    assert "## Report llm-wiki tool issues" not in schema.read_text(
        encoding="utf-8"
    )
    assert not Path("AGENTS.md").exists()
    config = read_config("docs/llm_wiki")
    assert config["agent"] == "copilot"
    assert config["issue_reporting"] is False


@pytest.mark.parametrize(
    "command", ["extract", "bootstrap", "lint", "sync", "ci-check", "doctor"]
)
def test_inventory_commands_help_lists_include_tests_go(command, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["llm-wiki", command, "--help"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--include-tests {go}" in help_text
    assert "Include language-specific test files in extraction" in help_text


@pytest.mark.parametrize(
    ("command", "module_name"),
    [
        ("extract", "extract_cmd"),
        ("bootstrap", "bootstrap_cmd"),
        ("lint", "lint_cmd"),
        ("sync", "sync_cmd"),
        ("ci-check", "ci_check_cmd"),
        ("doctor", "doctor_cmd"),
    ],
)
def test_inventory_commands_parse_include_tests_go(command, module_name, monkeypatch):
    seen = {}
    command_module = getattr(cli, module_name)
    monkeypatch.setattr(
        command_module,
        "run",
        lambda args: seen.setdefault("include_tests", args.include_tests),
    )
    monkeypatch.setattr("sys.argv", ["llm-wiki", command, "--include-tests", "go"])

    cli.main()

    assert seen["include_tests"] == ["go"]


@pytest.mark.parametrize(
    "command", ["extract", "bootstrap", "lint", "sync", "ci-check", "doctor"]
)
def test_inventory_commands_reject_unsupported_include_tests_language(
    command, monkeypatch
):
    monkeypatch.setattr("sys.argv", ["llm-wiki", command, "--include-tests", "rust"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


@pytest.mark.parametrize(
    "command", ["extract", "bootstrap", "lint", "sync", "ci-check", "doctor"]
)
def test_inventory_commands_help_lists_helper_cache_dir(command, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["llm-wiki", command, "--help"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--helper-cache-dir PATH" in help_text
    assert "TypeScript/JavaScript/Go/Rust/Haskell" in help_text
    assert "extractor" in help_text
    assert "helpers" in help_text


def test_prepare_extractors_help_lists_haskell_language(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["llm-wiki", "prepare-extractors", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--language {typescript,go,rust,haskell}" in help_text
    assert "Helper language to prepare" in help_text


def test_prepare_extractors_help_lists_allow_external_src(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["llm-wiki", "prepare-extractors", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--allow-external-src" in help_text
    assert "outside the current working" in help_text
    assert "directory" in help_text


def test_prepare_extractors_help_lists_plan_formats(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["llm-wiki", "prepare-extractors", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--plan" in help_text
    assert "--format {text,json}" in help_text
    assert "selected helper languages" in help_text
    assert "without preparing" in help_text


def test_prepare_extractors_parses_json_plan(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        cli.prepare_extractors_cmd,
        "run",
        lambda args: seen.update({"plan": args.plan, "format": args.format}),
    )
    monkeypatch.setattr(
        "sys.argv", ["llm-wiki", "prepare-extractors", "--plan", "--format", "json"]
    )

    cli.main()

    assert seen == {"plan": True, "format": "json"}


def test_prepare_extractors_parses_allow_external_src(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        cli.prepare_extractors_cmd,
        "run",
        lambda args: seen.setdefault("allow_external_src", args.allow_external_src),
    )
    monkeypatch.setattr(
        "sys.argv", ["llm-wiki", "prepare-extractors", "--allow-external-src"]
    )

    cli.main()

    assert seen["allow_external_src"] is True


def test_site_export_parses_file_friendly_mkdocs(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        cli.site_cmd,
        "run",
        lambda args: seen.update(
            {
                "action": args.site_action,
                "format": args.format,
                "file_friendly": args.file_friendly,
            }
        ),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "llm-wiki",
            "site",
            "export",
            "--wiki-dir",
            "docs/llm_wiki",
            "--out-dir",
            "site",
            "--format",
            "mkdocs",
            "--file-friendly",
        ],
    )

    cli.main()

    assert seen == {
        "action": "export",
        "format": "mkdocs",
        "file_friendly": True,
    }


def test_site_check_parses_built_site_dir_and_link_mode(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        cli.site_cmd,
        "run",
        lambda args: seen.update(
            {
                "action": args.site_action,
                "built_site_dir": args.built_site_dir,
                "link_mode": args.link_mode,
                "format": args.format,
            }
        ),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "llm-wiki",
            "site",
            "check",
            "--wiki-dir",
            "docs/llm_wiki",
            "--out-dir",
            "site",
            "--built-site-dir",
            "_site",
            "--link-mode",
            "file",
            "--format",
            "mkdocs",
        ],
    )

    cli.main()

    assert seen == {
        "action": "check",
        "built_site_dir": "_site",
        "link_mode": "file",
        "format": "mkdocs",
    }


def test_site_export_parses_user_profile_and_site_name(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        cli.site_cmd,
        "run",
        lambda args: seen.update(
            {
                "action": args.site_action,
                "profile": args.profile,
                "site_name": args.site_name,
            }
        ),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "llm-wiki",
            "site",
            "export",
            "--out-dir",
            "site",
            "--profile",
            "user",
            "--site-name",
            "Assistant",
        ],
    )

    cli.main()

    assert seen == {
        "action": "export",
        "profile": "user",
        "site_name": "Assistant",
    }


def test_site_export_parses_knowledge_projection_options(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        cli.site_cmd,
        "run",
        lambda args: seen.update(
            {
                "metadata": args.knowledge_metadata,
                "profile": args.knowledge_profile,
                "identity": args.public_repository_identity,
            }
        ),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "llm-wiki",
            "site",
            "export",
            "--out-dir",
            "site",
            "--knowledge-metadata",
            "summary",
            "--knowledge-profile",
            "internal",
            "--knowledge-public-repository-identity",
            "example.invalid/acme/wiki",
        ],
    )

    cli.main()

    assert seen == {
        "metadata": "summary",
        "profile": "internal",
        "identity": "example.invalid/acme/wiki",
    }


def test_obsidian_check_parses_knowledge_projection_options(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        cli.obsidian_cmd,
        "run",
        lambda args: seen.update(
            {
                "metadata": args.knowledge_metadata,
                "profile": args.knowledge_profile,
                "identity": args.knowledge_public_repository_identity,
            }
        ),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "llm-wiki",
            "obsidian",
            "check",
            "--vault-dir",
            "vault",
            "--knowledge-metadata",
            "summary",
            "--knowledge-profile",
            "public-portable",
            "--knowledge-public-repository-identity",
            "example.invalid/acme/wiki",
        ],
    )

    cli.main()

    assert seen == {
        "metadata": "summary",
        "profile": "public-portable",
        "identity": "example.invalid/acme/wiki",
    }


@pytest.mark.parametrize(
    "argv",
    [
        [
            "llm-wiki",
            "site",
            "export",
            "--out-dir",
            "site",
            "--knowledge-profile",
            "internal",
        ],
        [
            "llm-wiki",
            "obsidian",
            "check",
            "--vault-dir",
            "vault",
            "--knowledge-public-repository-identity",
            "example.invalid/acme/wiki",
        ],
    ],
)
def test_projection_options_require_metadata_mode(argv, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", argv)

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 1
    assert "require --knowledge-metadata summary" in capsys.readouterr().err


def test_site_check_parses_user_profile_and_site_name(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        cli.site_cmd,
        "run",
        lambda args: seen.update(
            {
                "action": args.site_action,
                "profile": args.profile,
                "site_name": args.site_name,
            }
        ),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "llm-wiki",
            "site",
            "check",
            "--out-dir",
            "site",
            "--profile",
            "user",
            "--site-name",
            "Assistant",
        ],
    )

    cli.main()

    assert seen == {
        "action": "check",
        "profile": "user",
        "site_name": "Assistant",
    }


@pytest.mark.parametrize(
    ("command", "command_module"),
    [
        ("lint", cli.lint_cmd),
        ("sync", cli.sync_cmd),
        ("ci-check", cli.ci_check_cmd),
        ("doctor", cli.doctor_cmd),
    ],
)
def test_extraction_commands_default_resolved_and_requested_jobs(
    command, command_module, monkeypatch
):
    seen = {}
    monkeypatch.setattr(
        command_module,
        "run",
        lambda args: seen.update(
            jobs=args.jobs, requested_jobs=args.requested_jobs
        ),
    )
    monkeypatch.setattr("sys.argv", ["llm-wiki", command])

    cli.main()

    assert seen == {"jobs": 1, "requested_jobs": 1}


def test_cli_adds_non_causal_resource_guidance_for_wrapped_enospc(
    monkeypatch, capsys
):
    error_number = getattr(errno, "ENOSPC", None)
    if error_number is None:
        pytest.skip("ENOSPC is not defined on this platform")
    inner = OSError(error_number, "capacity exhausted")
    outer = RuntimeError("scan failed")
    outer.__cause__ = inner

    def fail(_args):
        raise outer

    monkeypatch.delenv("LLM_WIKI_DEBUG", raising=False)
    monkeypatch.setattr(cli.lint_cmd, "run", fail)
    monkeypatch.setattr("sys.argv", ["llm-wiki", "lint"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 1
    error = capsys.readouterr().err
    assert "ENOSPC may indicate" in error
    assert "does not identify a single cause" in error
    assert "no automatic retry was attempted" in error
