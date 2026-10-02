"""Setup automation and the boundary between preparation and read-only analysis."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import init_cmd
from llm_wiki_cli.services import extractor_helpers as helpers
from llm_wiki_cli.services.helper_preparation import ensure_source_helpers
from llm_wiki_cli.services.source_selection import SourceSelectionError


def _prepare_fixture(language, cache_root):
    root = cache_root / language / "fixture"
    root.mkdir(parents=True, exist_ok=True)
    if language == "typescript":
        artifact = root / "node_modules" / "ts-morph"
        artifact.mkdir(parents=True, exist_ok=True)
        (artifact / "index.js").write_text("fixture", encoding="utf-8")
        (root / "extract.js").write_text("fixture", encoding="utf-8")
    else:
        artifact = root / "extractor"
        artifact.write_text("fixture", encoding="utf-8")
    helpers._write_manifest(
        cache_root,
        language,
        {
            "version": helpers.HELPER_MANIFEST_VERSION,
            "language": language,
            "platform": helpers.platform_id(),
            "source_fingerprint": helpers.helper_source_fingerprint(language),
            "artifact_fingerprint": helpers.helper_artifact_fingerprint(artifact),
            "root": str(root),
            "path": str(artifact),
        },
    )
    return helpers.HelperPrepareResult(language, "prepared", "ok", str(artifact))


@pytest.mark.parametrize(
    "language,suffix",
    [
        ("typescript", "ts"),
        ("typescript", "jsx"),
        ("go", "go"),
        ("rust", "rs"),
        ("haskell", "hs"),
    ],
)
def test_prepares_missing_reuses_current_and_repairs_stale(
    tmp_path, monkeypatch, language, suffix
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / f"main.{suffix}").write_text("fixture", encoding="utf-8")
    builds = []

    def prepare(selected, cache_root):
        builds.append(selected)
        return _prepare_fixture(selected, cache_root)

    monkeypatch.setattr(helpers, "prepare_helper", prepare)
    first = ensure_source_helpers(".")
    second = ensure_source_helpers(".")
    assert [result.status for result in first] == ["prepared"]
    assert [result.status for result in second] == ["already_current"]
    assert builds == [language]

    artifact_path = first[0].path
    assert artifact_path is not None
    artifact = Path(artifact_path)
    damaged = artifact / "index.js" if artifact.is_dir() else artifact
    damaged.write_text("corrupt", encoding="utf-8")
    third = ensure_source_helpers(".")
    assert [result.status for result in third] == ["prepared"]
    assert builds == [language, language]


def test_python_only_setup_needs_neither_cache_nor_toolchain(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.setattr(
        helpers, "resolve_helper_cache_root", lambda *a: pytest.fail("no cache needed")
    )
    monkeypatch.setattr(
        helpers, "prepare_helper", lambda *a: pytest.fail("no helper needed")
    )
    assert ensure_source_helpers(".") == []


def test_selection_is_validated_before_preparation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "main.ts").write_text("fixture", encoding="utf-8")
    policy = tmp_path / "selection.json"
    policy.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        helpers, "resolve_helper_cache_root", lambda *a: pytest.fail("selection first")
    )
    monkeypatch.setattr(
        helpers, "prepare_helper", lambda *a: pytest.fail("selection first")
    )
    with pytest.raises(SourceSelectionError):
        ensure_source_helpers(".", source_selection=policy)


def test_build_io_failure_is_reported_and_other_helpers_are_prepared(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / "main.ts").write_text("fixture", encoding="utf-8")
    (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")

    def prepare(language, cache_root):
        if language == "typescript":
            raise PermissionError("cache is read-only")
        return _prepare_fixture(language, cache_root)

    monkeypatch.setattr(helpers, "prepare_helper", prepare)
    results = ensure_source_helpers(".")
    assert [(r.language, r.status) for r in results] == [
        ("typescript", "failed"),
        ("go", "prepared"),
    ]
    assert "cache is read-only" in results[0].message


def _init(*arguments):
    init_cmd.run(cli._build_parser().parse_args(["init", *arguments]))


def test_init_preparation_is_opt_in_even_after_a_previous_opt_in(
    tmp_project, monkeypatch
):
    _init("--prepare-extractors")
    Path("main.ts").write_text("fixture", encoding="utf-8")
    monkeypatch.setattr(
        init_cmd, "ensure_source_helpers", lambda *a, **kw: pytest.fail("no opt-in")
    )
    _init()


def test_init_uses_stored_selection_and_explicit_cache(tmp_project, monkeypatch):
    policy = Path("selection.json")
    policy.write_text(
        json.dumps(
            {
                "schema_version": "llm-wiki-source-selection/v1",
                "include": ["frontend"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )
    Path("frontend").mkdir()
    Path("frontend/app.jsx").write_text("export const app = 1;", encoding="utf-8")
    Path("outside.go").write_text("package main\n", encoding="utf-8")
    _init("--source-selection", str(policy))
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(tmp_project / "unused-cache"))
    builds = []

    def prepare(language, cache_root):
        builds.append((language, cache_root))
        return _prepare_fixture(language, cache_root)

    monkeypatch.setattr(helpers, "prepare_helper", prepare)
    for _ in range(2):
        _init("--prepare-extractors", "--helper-cache-dir", "helper cache")
    expected_root = tmp_project / "helper cache" / helpers.HELPER_CACHE_DIRNAME
    assert builds == [("typescript", expected_root)]
    assert helpers.get_prepared_typescript_root(".", "helper cache") is not None
    assert not (tmp_project / "unused-cache").exists()


def test_init_failure_does_not_publish_scaffold_and_can_be_retried(
    tmp_project, monkeypatch, capsys
):
    Path("main.ts").write_text("fixture", encoding="utf-8")
    monkeypatch.setattr(
        helpers,
        "prepare_helper",
        lambda *a: helpers.HelperPrepareResult("typescript", "failed", "npm not found"),
    )
    with pytest.raises(SystemExit) as exc:
        _init("--prepare-extractors")
    assert exc.value.code == 1
    assert not Path("AGENTS.md").exists()
    assert not Path("docs/llm_wiki").exists()
    output = capsys.readouterr()
    assert "npm not found" in output.out
    assert "Install Node.js with npm" in output.out
    assert "rerun the same init command" in output.err
    assert "initialized successfully" not in output.out

    monkeypatch.setattr(helpers, "prepare_helper", _prepare_fixture)
    _init("--prepare-extractors")
    assert Path("AGENTS.md").exists()
    assert helpers.get_prepared_typescript_root(".") is not None


def test_init_without_git_requires_cache_only_for_helper_languages(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_WIKI_CACHE_DIR", raising=False)
    Path("main.ts").write_text("fixture", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        _init("--prepare-extractors")
    assert exc.value.code == 1
    assert "--helper-cache-dir PATH" in capsys.readouterr().err
    assert not Path("AGENTS.md").exists()
    monkeypatch.setattr(helpers, "prepare_helper", _prepare_fixture)
    _init("--prepare-extractors", "--helper-cache-dir", "cache")
    assert helpers.get_prepared_typescript_root(".", "cache") is not None


def test_init_rejects_unused_cache_option(tmp_project, capsys):
    with pytest.raises(SystemExit) as exc:
        _init("--helper-cache-dir", "cache")
    assert exc.value.code == 2
    assert "requires --prepare-extractors" in capsys.readouterr().err
    assert not Path("AGENTS.md").exists()


@pytest.mark.parametrize(
    "arguments",
    [
        ["extract", "--deep", "--read-only"],
        ["context", "--budget", "1000", "--focus", "all", "--read-only"],
        [
            "context",
            "--budget",
            "8000",
            "--format",
            "packet",
            "--focus",
            "changed",
            "--knowledge-mode",
            "auto",
            "--read-only",
        ],
    ],
    ids=["extract", "context", "context-packet"],
)
def test_read_only_commands_never_prepare_helpers(
    tmp_path, monkeypatch, capsys, arguments
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(tmp_path / "cache"))
    Path("main.ts").write_text("export const value = 1;", encoding="utf-8")
    monkeypatch.setattr(
        helpers, "prepare_helper", lambda *a: pytest.fail("read must not build")
    )
    monkeypatch.setattr(
        helpers.shutil, "which", lambda name: "node" if name == "node" else None
    )
    monkeypatch.setattr("sys.argv", ["llm-wiki", *arguments])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    message = capsys.readouterr().err
    assert "not prepared" in message
    assert "prepare-extractors" in message
    assert "retry the original command" in message
    assert str(tmp_path / "cache") in message
    assert list(tmp_path.iterdir()) == [tmp_path / "main.ts"]
