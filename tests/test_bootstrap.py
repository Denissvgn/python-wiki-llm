"""Tests for commands/bootstrap_cmd.py"""

import ast
import inspect
import json
import os
import re
import shutil
import subprocess
import textwrap
import types
from copy import deepcopy
from pathlib import Path

import pytest
from llm_wiki_cli import cli
from llm_wiki_cli.commands import bootstrap_cmd, init_cmd
from llm_wiki_cli.commands.extract_cmd import (
    ExtractorStatus,
    InventoryResult,
    get_inventory,
    resolve_call_edges,
)
from llm_wiki_cli.services.data_flow import analyze_data_flow
from llm_wiki_cli.services.dependencies import analyze_dependencies
from llm_wiki_cli.services.diagrams import (
    GENERATED_DIAGRAM_CHAR_LIMIT,
    GENERATED_DIAGRAM_LINE_LIMIT,
    GENERATED_DIAGRAM_NODE_LIMIT,
)
from llm_wiki_cli.services.entrypoints import build_flow, get_entry_points
from llm_wiki_cli.services import knowledge_orchestration, plugins
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.wiki_surface import iter_directory_kinds, is_safe_page_id
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME

# True when git is on PATH; used to guard git-dependent fixture steps.
_GIT_AVAILABLE = shutil.which("git") is not None


def _make_args(**kwargs):
    defaults = {
        "src_dir": ".",
        "wiki_dir": "docs/llm_wiki",
        "overwrite": False,
        "depth": "full",
        "skip_workflows": True,
        "skip_data_flow": False,
        "format": "text",
        "source_adapter": False,
        "allow_external_src": False,
        "helper_cache_dir": None,
        "include_tests": None,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _assert_generated_diagram_budgets(markdown: str) -> None:
    blocks = re.findall(r"```mermaid\n(.*?)\n```", markdown, flags=re.DOTALL)
    assert blocks
    for body in blocks:
        lines = body.splitlines()
        nodes = sum(
            line.lstrip().startswith("participant ")
            or re.match(r"^\s+[A-Za-z_][A-Za-z0-9_]*\s*[\[({]", line) is not None
            for line in lines
        )
        assert nodes <= GENERATED_DIAGRAM_NODE_LIMIT
        assert len(lines) <= GENERATED_DIAGRAM_LINE_LIMIT
        assert len(body) <= GENERATED_DIAGRAM_CHAR_LIMIT


def test_bootstrap_constraint_refresh_pins_selection_for_default_wiki(
    tmp_project,
):
    init_cmd.run(
        types.SimpleNamespace(
            agent="generic",
            wiki_dir="docs/llm_wiki",
            no_skills=True,
        )
    )

    bootstrap_cmd._update_agent_constraints(
        "docs/llm_wiki",
        source_selection="config/selection.json",
    )

    constraints = Path("AGENTS.md").read_text(encoding="utf-8")
    assert "--source-selection config/selection.json" in constraints


def _dense_module_dependency_summary():
    module = "pkg/focal.py"
    neighbors = [f"pkg/n{index:02d}.py" for index in range(11)]
    direct_edges = [
        *((neighbor, module) for neighbor in neighbors[:6]),
        *((module, neighbor) for neighbor in neighbors[6:]),
    ]
    contextual_edges = [
        (source, target)
        for source_index, source in enumerate(neighbors)
        for target in neighbors[source_index + 1 :]
    ][:49]
    cycle_edge = contextual_edges[-1]
    return (
        {
            "file": module,
            "detail": "module",
            "inbound": neighbors[:6],
            "outbound": neighbors[6:],
            "nodes": [module, *neighbors],
            "edges": [*direct_edges, *contextual_edges],
            "cycle_participation": True,
            "cycle_edges": [cycle_edge],
            "external": {},
            "overflow": {
                "node_limit": 12,
                "total_neighbor_count": 11,
                "omitted_count": 0,
            },
        },
        direct_edges,
        cycle_edge,
    )


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


def _write_entrypoint_detector_plugin(root: Path, *, body: str) -> None:
    plugin_dir = root / "vendor" / "detector-plugin"
    plugin_dir.mkdir(parents=True)
    module_name = "detectors_" + "_".join(root.parts[-3:])
    module_name = "".join(
        ch if ch.isalnum() or ch == "_" else "_" for ch in module_name
    )
    (plugin_dir / plugins.MANIFEST_FILENAME).write_text(
        textwrap.dedent(f"""\
        {{
          "id": "detector-plugin",
          "version": "0.1.0",
          "llm_wiki_version": "*",
          "components": [
            {{
              "type": "entrypoint_detector",
              "id": "worker",
              "entry_point": "{module_name}:detect"
            }}
          ]
        }}
        """),
        encoding="utf-8",
    )
    (plugin_dir / f"{module_name}.py").write_text(
        textwrap.dedent(body), encoding="utf-8"
    )
    plugins.install_plugin(str(plugin_dir), root=root, yes=True)


def _write_project_team_open_style_async_main(root: Path) -> None:
    cli_dir = root / "src" / "cli"
    cli_dir.mkdir(parents=True)
    (root / "src" / "__init__.py").write_text("", encoding="utf-8")
    (cli_dir / "__init__.py").write_text("", encoding="utf-8")
    (root / "src" / "main.py").write_text(
        textwrap.dedent("""\
        import asyncio
        from src.cli.commands import main as cli_main
        from src.cli.commands import print_banner
        from src.cli.orchestrator import CLIOrchestrator

        async def main_entry():
            cli_main()
            print_banner(None)

        if __name__ == "__main__":
            asyncio.run(main_entry())
    """),
        encoding="utf-8",
    )
    (cli_dir / "commands.py").write_text(
        textwrap.dedent("""\
        def main():
            parse()

        def parse():
            pass

        def print_banner(console):
            pass
    """),
        encoding="utf-8",
    )
    (cli_dir / "orchestrator.py").write_text(
        "class CLIOrchestrator:\n    pass\n", encoding="utf-8"
    )


def _write_diagram_style_plugin(root: Path, *, body: str) -> None:
    plugin_dir = root / "vendor" / "diagram-style-plugin"
    plugin_dir.mkdir(parents=True)
    module_name = "styles_" + "_".join(root.parts[-3:])
    module_name = "".join(
        ch if ch.isalnum() or ch == "_" else "_" for ch in module_name
    )
    (plugin_dir / plugins.MANIFEST_FILENAME).write_text(
        textwrap.dedent(f"""\
        {{
          "id": "diagram-style-plugin",
          "version": "0.1.0",
          "llm_wiki_version": "*",
          "components": [
            {{
              "type": "diagram_style",
              "id": "brand",
              "entry_point": "{module_name}:style"
            }}
          ]
        }}
        """),
        encoding="utf-8",
    )
    (plugin_dir / f"{module_name}.py").write_text(
        textwrap.dedent(body), encoding="utf-8"
    )
    plugins.install_plugin(str(plugin_dir), root=root, yes=True)


def _write_toy_extractor_plugin(root: Path) -> None:
    plugin_dir = root / "vendor" / "toy-extractor-plugin"
    plugin_dir.mkdir(parents=True)
    module_name = "bootstrap_toy_" + "_".join(root.parts[-3:])
    module_name = "".join(
        character if character.isalnum() or character == "_" else "_"
        for character in module_name
    )
    (plugin_dir / plugins.MANIFEST_FILENAME).write_text(
        json.dumps(
            {
                "id": "bootstrap-toy-extractor",
                "version": "0.1.0",
                "llm_wiki_version": "*",
                "components": [
                    {
                        "type": "extractor",
                        "id": "toy",
                        "language": "javascript",
                        "entry_point": f"{module_name}:ToyExtractor",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (plugin_dir / f"{module_name}.py").write_text(
        textwrap.dedent(
            """\
            from pathlib import Path


            class ToyExtractor:
                last_error = None

                def extract(self, src_dir, only_files=None, deep=False):
                    selected = set(only_files or ())
                    files = sorted(Path(src_dir).glob("*.jscustom"))
                    if only_files is not None:
                        files = [path for path in files if path.name in selected]
                    return {
                        path.name: {
                            "language": "javascript",
                            "classes": [],
                            "functions": [{"name": path.stem, "line": 1}],
                            "imports": [],
                        }
                        for path in files
                    }
            """
        ),
        encoding="utf-8",
    )
    plugins.install_plugin(str(plugin_dir), root=root, yes=True)


def test_bootstrap_run_stays_a_short_coordinator():
    assert _body_line_count(bootstrap_cmd.run) <= 40


def test_bootstrap_parser_accepts_skip_data_flow_flag():
    parser = cli._build_parser()

    args = parser.parse_args(["bootstrap", "--skip-data-flow"])

    assert args.skip_data_flow is True


def test_bootstrap_help_hides_overwrite_compatibility_tombstone(capsys):
    parser = cli._build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["bootstrap", "--help"])

    assert exc_info.value.code == 0
    assert "--overwrite" not in capsys.readouterr().out
    assert parser.parse_args(["bootstrap", "--overwrite"]).overwrite is True


def test_bootstrap_excludes_agent_worktree_surfaces(tmp_path, monkeypatch, capsys):
    (tmp_path / "app.py").write_text(
        textwrap.dedent("""\
        class App:
            pass
        """),
        encoding="utf-8",
    )
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    worktree = tmp_path / ".claude" / "worktrees" / "agent-strict-instructions"
    worktree.mkdir(parents=True)
    (worktree / "app.py").write_text(
        textwrap.dedent("""\
        class WorktreeApp:
            pass
        """),
        encoding="utf-8",
    )
    (worktree / "Dockerfile").write_text("FROM alpine\n", encoding="utf-8")
    wiki_dir = tmp_path / "wiki"
    monkeypatch.chdir(tmp_path)

    bootstrap_cmd.run(
        _make_args(src_dir=".", wiki_dir=str(wiki_dir), source_adapter=True)
    )
    capsys.readouterr()

    index = (wiki_dir / "index.md").read_text(encoding="utf-8")
    module_pages = [path.name for path in (wiki_dir / "modules").glob("*.md")]
    infrastructure_pages = [
        path.name for path in (wiki_dir / "infrastructure").glob("*.md")
    ]

    assert ".claude/worktrees" not in index
    assert not any("_claude_worktrees" in name for name in module_pages)
    assert not any("agent-strict-instructions" in name for name in module_pages)
    assert not any("_claude_worktrees" in name for name in infrastructure_pages)
    assert not any("agent-strict-instructions" in name for name in infrastructure_pages)


@pytest.fixture
def tmp_collision_project(tmp_path):
    """Project with the same class/module name in two different service directories."""
    proj = tmp_path / "project"
    proj.mkdir()

    if _GIT_AVAILABLE:
        subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", str(proj), "config", "user.email", "t@t.com"],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(proj), "config", "user.name", "T"],
            capture_output=True,
            check=True,
        )
    else:
        (proj / ".git").mkdir(exist_ok=True)

    (proj / "pyproject.toml").write_text(
        '[project]\nname = "sample"\nversion = "0.1.0"\n'
    )

    # Two services each with a config.py that defines a Config class
    svc_a = proj / "services" / "auth-service" / "src"
    svc_a.mkdir(parents=True)
    (svc_a / "config.py").write_text(
        textwrap.dedent("""\
        class Config:
            \"\"\"Auth service config.\"\"\"
            secret: str = "s3cr3t"
    """)
    )

    svc_b = proj / "services" / "order-service" / "src"
    svc_b.mkdir(parents=True)
    (svc_b / "config.py").write_text(
        textwrap.dedent("""\
        class Config:
            \"\"\"Order service config.\"\"\"
            db_url: str = "sqlite://"
    """)
    )

    old_cwd = os.getcwd()
    os.chdir(proj)
    yield proj
    os.chdir(old_cwd)


class TestBootstrapCollisions:
    def test_bootstrap_tracks_empty_surface_directories(self, tmp_project):
        wiki_dir = tmp_project / "docs" / "llm_wiki"

        bootstrap_cmd.run(
            _make_args(
                src_dir=".",
                wiki_dir=str(wiki_dir),
                source_adapter=True,
            )
        )

        directory_names = {
            surface.directory
            for surface in iter_directory_kinds()
            if surface.directory is not None
        }
        assert directory_names
        for directory_name in directory_names:
            assert (wiki_dir / directory_name / ".gitkeep").is_file()

    def test_bootstrap_json_summary_is_parseable_stdout(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(
            src_dir=".", wiki_dir=str(wiki_dir), format="json", source_adapter=True
        )

        bootstrap_cmd.run(args)

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["schema_version"] == "llm-wiki-bootstrap-summary/v1"
        assert data["generated_wiki_path"] == str(wiki_dir).replace("\\", "/")
        assert data["source_files"] >= 3
        assert data["classes"] >= 2
        assert data["manifest_path"].endswith(".llm-wiki-manifest.json")
        assert data["created_files"]
        assert "Bootstrapping wiki" in captured.err

    def test_bootstrap_empty_inventory_json_includes_knowledge_state(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        wiki_dir = tmp_path / "wiki"

        bootstrap_cmd.run(
            _make_args(
                src_dir=".",
                wiki_dir=str(wiki_dir),
                format="json",
                source_adapter=True,
            )
        )

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["manifest_path"] is None
        assert data["knowledge_path"] is None
        assert data["knowledge_status"] is None
        assert data["knowledge_schema_version"] == "llm-wiki-knowledge/v1"
        assert "Nothing to bootstrap" in captured.err

    def test_bootstrap_artifact_reporting_accounts_for_each_action(
        self, tmp_path, monkeypatch
    ):
        state = types.SimpleNamespace(
            created_files=[],
            updated_files=[],
            skipped_files=[],
        )
        messages = []
        monkeypatch.setattr(
            bootstrap_cmd,
            "_emit_bootstrap",
            lambda _state, message, **_kwargs: messages.append(message),
        )
        created = tmp_path / ".llm-wiki-surface.json"
        updated = tmp_path / ".llm-wiki-knowledge.json"
        unchanged = tmp_path / ".llm-wiki-manifest.json"

        bootstrap_cmd._record_bootstrap_artifact(
            state,
            path=created,
            write_state=bootstrap_cmd.ArtifactWriteState.CREATED,
        )
        bootstrap_cmd._record_bootstrap_artifact(
            state,
            path=updated,
            write_state=bootstrap_cmd.ArtifactWriteState.UPDATED,
        )
        bootstrap_cmd._record_bootstrap_artifact(
            state,
            path=unchanged,
            write_state=bootstrap_cmd.ArtifactWriteState.UNCHANGED,
        )

        assert state.created_files == [str(created).replace("\\", "/")]
        assert state.updated_files == [str(updated).replace("\\", "/")]
        assert state.skipped_files == [str(unchanged).replace("\\", "/")]
        assert messages == [
            f"  CREATE {created}",
            f"  UPDATE {updated}",
            f"  SKIP {unchanged} (unchanged)",
        ]

    def test_bootstrap_reports_missing_haskell_helper_failure(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        hls_app = tmp_path / "hls-analysis" / "app"
        hls_src = tmp_path / "hls-analysis" / "src" / "HLSAnalysis"
        hls_app.mkdir(parents=True)
        hls_src.mkdir(parents=True)
        (hls_app / "Main.hs").write_text("module Main where\n", encoding="utf-8")
        (hls_src / "API.hs").write_text(
            "module HLSAnalysis.API where\n", encoding="utf-8"
        )

        with pytest.raises(SystemExit) as exc_info:
            bootstrap_cmd.run(
                _make_args(
                    src_dir=".",
                    wiki_dir="wiki",
                    format="json",
                    source_adapter=True,
                )
            )

        captured = capsys.readouterr()
        assert exc_info.value.code == 1
        assert captured.out == ""
        assert "Error: haskell extraction failed" in captured.err
        assert "prepare-extractors --language haskell" in captured.err
        assert "Unsupported sources detected" not in captured.err
        assert list((tmp_path / "wiki" / "modules").glob("*.md")) == []

    def test_bootstrap_prints_long_phase_progress(self, tmp_collision_project, capsys):
        wiki_dir = tmp_collision_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))

        bootstrap_cmd.run(args)

        out = capsys.readouterr().out
        assert "Extracting source inventory..." in out
        assert "Building cross-reference relationships..." in out
        assert "Generating entity and module pages..." in out
        assert "Writing sync manifest..." in out

    def test_entity_collision_uses_simple_name(self, tmp_collision_project, capsys):
        """When two files define the same class name, both get qualified pages."""
        wiki_dir = tmp_collision_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        entity_pages = list((wiki_dir / "entities").glob("*.md"))
        entity_names = {p.stem for p in entity_pages}

        # Both qualified entities must exist (one per source file)
        assert len([n for n in entity_names if "Config" in n]) == 2
        # Each qualified name must end with _Config
        for n in entity_names:
            if "Config" in n:
                assert n.endswith("_Config"), n

    def test_entity_page_contains_valid_source(self, tmp_collision_project, capsys):
        wiki_dir = tmp_collision_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        entity_pages = list((wiki_dir / "entities").glob("*Config*.md"))
        assert len(entity_pages) >= 1
        for ep in entity_pages:
            content = ep.read_text(encoding="utf-8")
            # Page must reference one of the two source files
            assert "config.py" in content

    def test_module_collision_uses_simple_name(self, tmp_collision_project, capsys):
        """When two files share the same stem, both get qualified module pages."""
        wiki_dir = tmp_collision_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        module_pages = list((wiki_dir / "modules").glob("*.md"))
        module_names = {p.stem for p in module_pages}

        # Both qualified modules must exist (one per source file)
        assert len([n for n in module_names if "config" in n]) == 2

    def test_module_collision_after_parent_prefix_uses_source_path_context(self):
        inventory = {
            "scripts/compliance/report.py": {
                "language": "python",
                "classes": [],
                "functions": [],
                "imports": [],
            },
            "services/other/report.py": {
                "language": "python",
                "classes": [],
                "functions": [],
                "imports": [],
            },
            "services/mlflow-service/tests/compliance/compliance_report.py": {
                "language": "python",
                "classes": [],
                "functions": [],
                "imports": [],
            },
        }

        page_map = bootstrap_cmd.build_module_page_map(inventory)

        assert len(set(page_map.values())) == len(page_map)
        assert page_map["scripts/compliance/report.py"] == "scripts_compliance_report"
        assert (
            page_map["services/mlflow-service/tests/compliance/compliance_report.py"]
            == "services_mlflow-service_tests_compliance_compliance_report"
        )

    def test_duplicate_entity_names_in_same_file_get_distinct_pages(
        self, tmp_path, monkeypatch, capsys
    ):
        source = tmp_path / "tests" / "test_news_sentiment_integration.py"
        source.parent.mkdir(parents=True)
        source.write_text(
            textwrap.dedent("""\
                class TestErrorHandling:
                    pass

                class TestErrorHandling:
                    pass
            """),
            encoding="utf-8",
        )
        inventory = {
            "tests/test_news_sentiment_integration.py": {
                "language": "python",
                "classes": [
                    {
                        "name": "TestErrorHandling",
                        "bases": [],
                        "line": 1,
                        "docstring": "First error handling tests.",
                        "decorators": [],
                        "attributes": [],
                        "methods": [],
                    },
                    {
                        "name": "TestErrorHandling",
                        "bases": [],
                        "line": 4,
                        "docstring": "Second error handling tests.",
                        "decorators": [],
                        "attributes": [],
                        "methods": [],
                    },
                ],
                "functions": [],
                "imports": [],
                "module_docstring": "",
            }
        }
        result = InventoryResult(
            inventory,
            {"python": ExtractorStatus("python", "ok", 1)},
        )
        occurrence_map = bootstrap_cmd.build_entity_occurrence_page_map(inventory)
        assert (
            occurrence_map[
                ("TestErrorHandling", "tests/test_news_sentiment_integration.py", 1)
            ]
            == "TestErrorHandling"
        )
        assert (
            occurrence_map[
                ("TestErrorHandling", "tests/test_news_sentiment_integration.py", 2)
            ]
            == "TestErrorHandling_2"
        )
        assert (
            bootstrap_cmd.build_entity_page_map(inventory)[
                ("TestErrorHandling", "tests/test_news_sentiment_integration.py")
            ]
            == "TestErrorHandling"
        )
        monkeypatch.setattr(
            bootstrap_cmd, "get_inventory_result", lambda *a, **k: result
        )
        monkeypatch.setattr(bootstrap_cmd, "get_docker_inventory", lambda *a, **k: {})

        monkeypatch.chdir(tmp_path)
        wiki_dir = tmp_path / "wiki"
        bootstrap_cmd.run(
            _make_args(
                src_dir=".",
                wiki_dir=str(wiki_dir),
                format="json",
                source_adapter=True,
            )
        )

        summary = json.loads(capsys.readouterr().out)
        entity_pages = sorted((wiki_dir / "entities").glob("TestErrorHandling*.md"))
        module = (
            wiki_dir / "modules" / "test_news_sentiment_integration.md"
        ).read_text(encoding="utf-8")
        index = (wiki_dir / "index.md").read_text(encoding="utf-8")

        assert summary["skipped_files"] == []
        assert [page.stem for page in entity_pages] == [
            "TestErrorHandling",
            "TestErrorHandling_2",
        ]
        assert "../entities/TestErrorHandling.md" in module
        assert "../entities/TestErrorHandling_2.md" in module
        assert "| Entities | 2 |" in index

    def test_index_has_no_duplicate_entries(self, tmp_collision_project, capsys):
        wiki_dir = tmp_collision_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        lines = (wiki_dir / "index.md").read_text(encoding="utf-8").splitlines()
        link_lines = [line for line in lines if line.startswith("- [")]
        seen = set()
        for line in link_lines:
            assert line not in seen, f"Duplicate index entry: {line}"
            seen.add(line)

    def test_no_collision_keeps_short_name(self, tmp_project, capsys):
        """Single-definition classes/modules must keep their plain short name."""
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        assert (wiki_dir / "entities" / "User.md").exists()
        assert (wiki_dir / "modules" / "models.md").exists()

    def test_same_directory_multilanguage_stem_collision_gets_extension_suffixes(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        from llm_wiki_cli.commands import lint_cmd

        (tmp_path / "foo.py").write_text("class Thing:\n    pass\n", encoding="utf-8")
        (tmp_path / "foo.ts").write_text(
            "export class Thing {}\n",
            encoding="utf-8",
        )
        inventory = {
            "foo.py": {
                "language": "python",
                "classes": [
                    {
                        "name": "Thing",
                        "bases": [],
                        "line": 1,
                        "docstring": "",
                        "decorators": [],
                        "attributes": [],
                        "methods": [],
                    }
                ],
                "functions": [],
                "imports": [],
                "module_docstring": "",
            },
            "foo.ts": {
                "language": "typescript",
                "classes": [
                    {
                        "name": "Thing",
                        "bases": [],
                        "line": 1,
                        "docstring": "",
                        "decorators": [],
                        "attributes": [],
                        "methods": [],
                    }
                ],
                "functions": [],
                "imports": [],
                "module_docstring": "",
            },
        }
        result = InventoryResult(
            inventory,
            {
                "python": ExtractorStatus("python", "ok", 1),
                "typescript": ExtractorStatus("typescript", "ok", 1),
            },
        )
        monkeypatch.setattr(
            bootstrap_cmd, "get_inventory_result", lambda *a, **k: result
        )
        monkeypatch.setattr(bootstrap_cmd, "get_docker_inventory", lambda *a, **k: {})
        monkeypatch.setattr(lint_cmd, "get_inventory_result", lambda *a, **k: result)
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        monkeypatch.chdir(tmp_path)
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="docs/llm_wiki"))

        assert (wiki_dir / "modules" / "foo_py.md").exists()
        assert (wiki_dir / "modules" / "foo_ts.md").exists()
        assert (wiki_dir / "entities" / "foo_py_Thing.md").exists()
        assert (wiki_dir / "entities" / "foo_ts_Thing.md").exists()

        lint_cmd.run(types.SimpleNamespace(src_dir=".", wiki_dir="docs/llm_wiki"))

    def test_relationship_collision_resolves_by_import_module(
        self, tmp_path, monkeypatch
    ):
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / "pkg_a").mkdir()
        (proj / "pkg_b").mkdir()
        (proj / "consumer.py").write_text(
            "from pkg_a.models import User\n\n"
            "def consume(user: User) -> User:\n"
            "    return user\n"
        )
        (proj / "pkg_a" / "models.py").write_text("class User:\n    pass\n")
        (proj / "pkg_b" / "models.py").write_text("class User:\n    pass\n")

        monkeypatch.chdir(proj)
        wiki_dir = proj / "docs" / "llm_wiki"
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir=str(wiki_dir)))

        a_page = (wiki_dir / "entities" / "pkg_a_models_User.md").read_text(
            encoding="utf-8"
        )
        b_page = (wiki_dir / "entities" / "pkg_b_models_User.md").read_text(
            encoding="utf-8"
        )
        assert (
            "| `consume` | type_reference | [consumer](../modules/consumer.md) |"
            in a_page
        )
        assert "../modules/consumer.md" in a_page
        assert "type_reference" not in b_page
        assert "../modules/consumer.md" not in b_page

    def test_relationship_resolves_current_package_relative_import(
        self, tmp_path, monkeypatch
    ):
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / "pkg").mkdir()
        (proj / "pkg" / "models.py").write_text("class User:\n    pass\n")
        (proj / "pkg" / "service.py").write_text(
            "from .models import User\n\n"
            "def consume(user: User) -> User:\n"
            "    return user\n"
        )

        monkeypatch.chdir(proj)
        wiki_dir = proj / "docs" / "llm_wiki"
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir=str(wiki_dir)))

        page = (wiki_dir / "entities" / "User.md").read_text(encoding="utf-8")
        assert (
            "| `consume` | type_reference | [service](../modules/service.md) |" in page
        )
        assert "../modules/service.md" in page

    def test_relationship_resolves_parent_package_relative_import(
        self, tmp_path, monkeypatch
    ):
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / "pkg" / "sub").mkdir(parents=True)
        (proj / "pkg" / "models.py").write_text("class User:\n    pass\n")
        (proj / "pkg" / "sub" / "service.py").write_text(
            "from ..models import User\n\n"
            "def consume(user: User) -> User:\n"
            "    return user\n"
        )

        monkeypatch.chdir(proj)
        wiki_dir = proj / "docs" / "llm_wiki"
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir=str(wiki_dir)))

        page = (wiki_dir / "entities" / "User.md").read_text(encoding="utf-8")
        assert (
            "| `consume` | type_reference | [service](../modules/service.md) |" in page
        )
        assert "../modules/service.md" in page

    def test_ambiguous_duplicate_relationship_is_skipped(self, tmp_path, monkeypatch):
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / "pkg_a").mkdir()
        (proj / "pkg_b").mkdir()
        (proj / "consumer.py").write_text(
            "from shared import User\n\n"
            "def consume(user: User) -> User:\n"
            "    return user\n"
        )
        (proj / "pkg_a" / "models.py").write_text("class User:\n    pass\n")
        (proj / "pkg_b" / "models.py").write_text("class User:\n    pass\n")

        monkeypatch.chdir(proj)
        wiki_dir = proj / "docs" / "llm_wiki"
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir=str(wiki_dir)))

        for page in (wiki_dir / "entities").glob("*User.md"):
            content = page.read_text(encoding="utf-8")
            assert "**used_by**" not in content
            assert "**imported_by**" not in content

    def test_workflow_links_use_collision_aware_module_pages(
        self, tmp_path, monkeypatch, capsys
    ):
        from llm_wiki_cli.commands import lint_cmd

        proj = tmp_path / "project"
        proj.mkdir()
        (proj / "models").mkdir()
        (proj / "schemas").mkdir()
        (proj / "routers").mkdir()
        (proj / "models" / "task.py").write_text("class Task:\n    pass\n")
        (proj / "schemas" / "task.py").write_text("class TaskCreate:\n    pass\n")
        (proj / "schemas" / "common.py").write_text(
            "class MessageResponse:\n    pass\n"
        )
        (proj / "routers" / "tasks.py").write_text(
            textwrap.dedent("""\
            from models.task import Task
            from schemas.task import TaskCreate as CreateSchema
            from schemas.common import MessageResponse

            def create_task(task: Task, data: CreateSchema) -> MessageResponse:
                return MessageResponse()
        """)
        )

        monkeypatch.chdir(proj)
        wiki_dir = proj / "docs" / "llm_wiki"
        bootstrap_cmd.run(
            _make_args(src_dir=".", wiki_dir=str(wiki_dir), skip_workflows=False)
        )

        workflow = (wiki_dir / "workflows" / "create_task.md").read_text(
            encoding="utf-8"
        )
        assert "../modules/task.md" not in workflow
        assert "../modules/models_task.md" in workflow
        assert "../modules/schemas_task.md" in workflow

        lint_cmd.run(types.SimpleNamespace(src_dir=".", wiki_dir=str(wiki_dir)))


class TestBootstrapEntityPages:
    def test_creates_entity_per_class(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        assert (wiki_dir / "entities" / "User.md").exists()
        assert (wiki_dir / "entities" / "Item.md").exists()

    def test_entity_content(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        content = (wiki_dir / "entities" / "User.md").read_text(encoding="utf-8")
        assert "# User" in content
        assert "name" in content
        assert "email" in content

    def test_entity_relationship_section_renders_diagram_links_and_tables(
        self, tmp_project, capsys
    ):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        content = (wiki_dir / "entities" / "User.md").read_text(encoding="utf-8")

        assert "## Relationships" in content
        assert "Auto-generated relationship summary" in content
        assert "```mermaid\nflowchart LR" in content
        assert 'click n0 "../modules/models.md"' in content
        assert '"../modules/main.md"' in content
        assert "| Module | Methods | Attributes |" in content
        assert "| Reference | Kind | Source |" in content
        assert (
            "| `create_user` | type_reference | [main](../modules/main.md) |" in content
        )
        assert (
            "| `list_items` | type_reference | [main](../modules/main.md) |" in content
        )

        dense_summary = {
            "name": "Dense",
            "file": None,
            "methods_count": 0,
            "attributes": [],
            "bases": [{"name": f"Base{index}"} for index in range(20)],
            "subclasses": [{"name": f"Subclass{index}"} for index in range(20)],
            "references": [
                {
                    "symbol": f"reference_{index}",
                    "module": f"module_{index}",
                    "kind": "call",
                }
                for index in range(20)
            ],
        }
        dense = "\n".join(
            bootstrap_cmd._generate_entity_relationship_section(
                dense_summary,
                {},
                {},
            )
        )
        dense_diagram = re.findall(
            r"```mermaid\n(.*?)\n```", dense, flags=re.DOTALL
        )[0]

        assert len(dense_diagram.splitlines()) == GENERATED_DIAGRAM_LINE_LIMIT
        assert "Relationship diagram shows 39 of 60 relationships; 21 omitted" in dense
        assert "Base19" in dense_diagram
        assert "Subclass18" in dense_diagram
        assert "Subclass19" not in dense_diagram
        assert "reference_0" not in dense_diagram
        assert "| `reference_19` | call |" in dense
        _assert_generated_diagram_budgets(dense)

    def test_entity_relationship_diagram_uses_bounded_plugin_style(
        self, tmp_project, capsys
    ):
        _write_diagram_style_plugin(
            tmp_project,
            body="""
            def style(context):
                assert context["surface"] == "relationships"
                return {
                    "direction": "BT",
                    "node_classes": {
                        "User (models.py)": "entity",
                        "create_user (main.py)": "bad; click n0",
                    },
                    "category_colors": {
                        "entity": "#123456",
                        "bad; click n0": "#fff",
                    },
                    "markdown": "```markdown\\n# injected",
                }
            """,
        )
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        content = (wiki_dir / "entities" / "User.md").read_text(encoding="utf-8")

        assert "```mermaid\nflowchart BT" in content
        assert "    class n0 entity" in content
        assert "    classDef entity fill:#123456,stroke:#123456" in content
        assert "bad; click" not in content
        assert "# injected" not in content

    def test_entity_relationship_section_uses_note_without_blank_diagram(
        self, tmp_path, monkeypatch, capsys
    ):
        (tmp_path / "models.py").write_text("class Lonely:\n    pass\n")
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))

        content = (tmp_path / "wiki" / "entities" / "Lonely.md").read_text(
            encoding="utf-8"
        )
        relationships = content.split("## Relationships", 1)[1]
        assert "No generated relationships detected" in relationships
        assert "```mermaid" not in relationships

    def test_entity_relationship_section_is_deterministic(self, tmp_project, capsys):
        first_wiki = tmp_project / "docs" / "first"
        second_wiki = tmp_project / "docs" / "second"
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir=str(first_wiki)))
        first = (first_wiki / "entities" / "User.md").read_text(encoding="utf-8")

        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir=str(second_wiki)))
        second = (second_wiki / "entities" / "User.md").read_text(encoding="utf-8")

        assert first == second


class TestBootstrapModulePages:
    def test_creates_module_per_file(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        assert (wiki_dir / "modules" / "models.md").exists()
        assert (wiki_dir / "modules" / "main.md").exists()

    def test_module_content(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        content = (wiki_dir / "modules" / "models.md").read_text(encoding="utf-8")
        assert "# models Module" in content

    def test_python_signature_renders_all_parameter_kinds_and_escapes_pipes(self):
        signature = bootstrap_cmd._format_signature(
            {
                "params": [
                    {"name": "source", "kind": "positional_only", "type": "str"},
                    {
                        "name": "target",
                        "kind": "positional_or_keyword",
                        "type": "str",
                        "default": "'out'",
                    },
                    {"name": "values", "kind": "var_positional", "type": "float"},
                    {"name": "required", "kind": "keyword_only", "type": "bool"},
                    {
                        "name": "mode",
                        "kind": "keyword_only",
                        "type": "str | None",
                        "default": "None",
                    },
                    {"name": "extras", "kind": "var_keyword", "type": "object"},
                ],
                "return_type": "str | None",
            }
        )

        assert signature == (
            "(source: str, /, target: str = 'out', *values: float, "
            "required: bool, mode: str | None = None, **extras: object) -> str | None"
        )
        assert bootstrap_cmd._table_inline_code(signature).count("\\|") == 2
        assert (
            bootstrap_cmd._format_signature(
                {
                    "params": [
                        {
                            "name": "source",
                            "kind": "positional_or_keyword",
                            "type": "str",
                        },
                        {"name": "required", "kind": "keyword_only", "type": "bool"},
                    ],
                    "return_type": "",
                }
            )
            == "(source: str, *, required: bool)"
        )

    def test_python_contract_entity_renders_model_metadata(self):
        content = bootstrap_cmd._generate_entity_md(
            {
                "name": "Request",
                "kind": "class",
                "model_kind": "pydantic",
                "bases": ["BaseModel"],
                "line": 4,
                "docstring": "Request payload.",
                "decorators": [],
                "model_config": [
                    {
                        "name": "extra",
                        "value": "'forbid'",
                        "source": "model_config",
                    }
                ],
                "attributes": [
                    {
                        "name": "name",
                        "type": "str | None",
                        "required": True,
                        "nullable": True,
                        "alias": "fullName",
                        "constraints": {"min_length": "1"},
                        "description": "Display name.",
                        "examples": ["'Ada'"],
                    },
                    {
                        "name": "labels",
                        "type": "list[str]",
                        "required": False,
                        "nullable": False,
                        "default_factory": "list",
                        "validation_alias": "inputLabels",
                        "serialization_alias": "outputLabels",
                    },
                ],
                "methods": [
                    {
                        "name": "normalize_name",
                        "params": [
                            {
                                "name": "value",
                                "kind": "positional_or_keyword",
                                "type": "str",
                            }
                        ],
                        "return_type": "str",
                        "decorators": ["field_validator('name')"],
                        "validator": {
                            "kind": "field",
                            "fields": ["name"],
                            "mode": "after",
                        },
                    }
                ],
            },
            "models.py",
            {},
        )

        assert "**Kind:** Pydantic model" in content
        assert "## Model Configuration" in content
        assert "## Validators" in content
        assert "| `name` | `str \\| None` | `fullName` | Yes | Yes | — |" in content
        assert "min_length=1" in content
        assert "Display name." in content
        assert "factory: `list`" in content
        assert "input: inputLabels; output: outputLabels" in content
        assert "Call(func=" not in content

    def test_enum_and_type_alias_contracts_render_declared_values(self):
        enum_content = bootstrap_cmd._generate_entity_md(
            {
                "name": "Color",
                "kind": "enum",
                "bases": ["str", "Enum"],
                "line": 2,
                "attributes": [
                    {"name": "RED", "value": "'red'"},
                    {"name": "AUTOMATIC", "value": "auto()"},
                ],
                "methods": [],
            },
            "types.py",
            {},
        )
        alias_content = bootstrap_cmd._generate_entity_md(
            {
                "name": "Mode",
                "kind": "type_alias",
                "bases": [],
                "line": 8,
                "target": "Literal['fast', 'safe']",
                "attributes": [],
                "methods": [],
            },
            "types.py",
            {},
        )

        assert "**Kind:** Enum" in enum_content
        assert "| `RED` | `'red'` | — |" in enum_content
        assert "| `AUTOMATIC` | `auto()` | — |" in enum_content
        assert "**Kind:** Type alias" in alias_content
        assert "**Target:** `Literal['fast', 'safe']`" in alias_content
        assert "## Attributes" in alias_content
        assert "## Methods" in alias_content

    def test_python_contract_round_trips_from_source_to_markdown(
        self, tmp_path, monkeypatch, capsys
    ):
        (tmp_path / "api.py").write_text(
            textwrap.dedent("""\
            from typing import Annotated, Literal
            from pydantic import BaseModel, Field

            class Request(BaseModel):
                name: Annotated[
                    str,
                    Field(alias="fullName", min_length=1, description="Display name"),
                ]
                labels: list[str] = Field(default_factory=list)

            def publish(
                source: str,
                /,
                *values: float,
                required: bool,
                mode: Literal["fast", "safe"] = "safe",
                **extras: object,
            ) -> Request | None:
                return None
            """),
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))

        module = (tmp_path / "wiki" / "modules" / "api.md").read_text(encoding="utf-8")
        entity = (tmp_path / "wiki" / "entities" / "Request.md").read_text(
            encoding="utf-8"
        )
        assert (
            "(source: str, /, *values: float, required: bool, "
            "mode: Literal['fast', 'safe'] = 'safe', **extras: object) "
            "-> Request \\| None"
        ) in module
        assert "| `name` | `Annotated[str, Field(" in entity
        assert "`fullName` | Yes | No | — | min_length=1" in entity
        assert "Display name" in entity
        assert "factory: `list`" in entity
        assert "Call(func=" not in entity

    def test_module_local_dependency_map_renders_diagram_tables_and_counts(
        self, tmp_path, monkeypatch, capsys
    ):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "sample"\nversion = "0.1.0"\ndependencies = ["requests"]\n'
        )
        (tmp_path / "api.py").write_text(
            "from service import Service\nimport requests\n\n"
            "def run() -> Service:\n"
            "    requests.get('https://example.test')\n"
            "    return Service()\n"
        )
        (tmp_path / "service.py").write_text(
            "from api import run\n\nclass Service:\n    pass\n"
        )
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))

        content = (tmp_path / "wiki" / "modules" / "api.md").read_text(encoding="utf-8")
        assert "## Local dependency map" in content
        assert "Auto-generated local dependency summary" in content
        assert "```mermaid\nflowchart LR" in content
        assert 'click n0 "../modules/api.md"' in content
        assert 'click n1 "../modules/service.md"' in content
        assert "==>" in content
        assert "| Outbound | [service](../modules/service.md) |" in content
        assert "| python | 1 | 0 |" in content

    def test_package_submodule_imports_drive_module_map_and_load_order(
        self, tmp_path, monkeypatch
    ):
        package = tmp_path / "pkg"
        commands = package / "commands"
        services = package / "services"
        commands.mkdir(parents=True)
        services.mkdir()
        (package / "cli.py").write_text(
            "from .commands import build_cmd\n"
            "from .services import runtime\n\n"
            "def main():\n"
            "    return build_cmd.run(), runtime.start()\n",
            encoding="utf-8",
        )
        (commands / "build_cmd.py").write_text(
            "def run():\n    return 1\n",
            encoding="utf-8",
        )
        (services / "runtime.py").write_text(
            "def start():\n    return 2\n",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))

        module = (tmp_path / "wiki" / "modules" / "cli.md").read_text(
            encoding="utf-8"
        )
        load_order = (tmp_path / "wiki" / "load-order.md").read_text(
            encoding="utf-8"
        )
        assert "| Outbound | [build_cmd](../modules/build_cmd.md) |" in module
        assert "| Outbound | [runtime](../modules/runtime.md) |" in module
        assert load_order.index("[build_cmd](modules/build_cmd.md)") < load_order.index(
            "[cli](modules/cli.md)"
        )
        assert load_order.index("[runtime](modules/runtime.md)") < load_order.index(
            "[cli](modules/cli.md)"
        )

    def test_module_local_dependency_map_uses_note_without_blank_diagram(
        self, tmp_path, monkeypatch, capsys
    ):
        (tmp_path / "solo.py").write_text("def run():\n    return 1\n")
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))

        content = (tmp_path / "wiki" / "modules" / "solo.md").read_text(
            encoding="utf-8"
        )
        local_map = content.split("## Local dependency map", 1)[1]
        assert "No internal module dependencies detected" in local_map
        assert "```mermaid" not in local_map

    def test_module_local_dependency_map_does_not_link_package_buckets(self):
        summary = {
            "file": "pkg/service.py",
            "detail": "package",
            "inbound": [{"package": "adapters", "count": 2}],
            "outbound": [{"package": "storage", "count": 3}],
            "nodes": ["adapters", "pkg/service.py", "storage"],
            "edges": [
                ("adapters", "pkg/service.py"),
                ("pkg/service.py", "storage"),
            ],
            "cycle_participation": False,
            "cycle_edges": [],
            "external": {},
            "overflow": {
                "node_limit": 4,
                "total_neighbor_count": 5,
                "omitted_count": 2,
            },
        }

        content = "\n".join(
            bootstrap_cmd._generate_module_dependency_section(
                summary,
                {
                    "adapters": "adapters-collision",
                    "pkg/service.py": "service",
                    "storage": "storage-collision",
                },
            )
        )
        rendered = bootstrap_cmd._module_dependency_graph(
            summary,
            {
                "adapters": "adapters-collision",
                "pkg/service.py": "service",
                "storage": "storage-collision",
            },
            {},
        )

        assert rendered is not None
        assert rendered.projection == "package"
        assert 'click n1 "../modules/service.md"' in content
        assert "../modules/adapters.md" not in content
        assert "../modules/storage.md" not in content
        assert "adapters-collision" not in content
        assert "storage-collision" not in content
        assert "Complete inbound and outbound dependencies" not in content
        assert (
            "the diagram and table below group them by top-level package"
            in content
        )
        assert "Counts report the number of module neighbors" in content
        assert (
            "All 5 module neighbor(s) are summarized by package because the "
            "module-level view exceeds the 4-node limit."
        ) in content
        assert "Showing 4 local graph nodes" not in content

    def test_dense_module_dependency_map_bounds_only_visual_edges(self):
        summary, direct_edges, cycle_edge = _dense_module_dependency_summary()
        original = deepcopy(summary)
        page_map = {
            node: Path(node).stem for node in summary["nodes"]
        }

        rendered = bootstrap_cmd._module_dependency_graph(summary, page_map, {})
        repeated = bootstrap_cmd._module_dependency_graph(summary, page_map, {})

        assert rendered == repeated
        assert rendered is not None
        assert rendered.diagram is not None
        assert rendered.projection == "module"
        assert (
            rendered.total_edges,
            rendered.shown_edges,
            rendered.omitted_edges,
        ) == (60, 55, 5)
        body = rendered.diagram.splitlines()[1:-1]
        assert len(body) == GENERATED_DIAGRAM_LINE_LIMIT

        aliases = {
            node: f"n{index}" for index, node in enumerate(summary["nodes"])
        }
        for source, target in direct_edges:
            assert f"    {aliases[source]} --> {aliases[target]}" in rendered.diagram
        assert (
            f"    {aliases[cycle_edge[0]]} ==> {aliases[cycle_edge[1]]}"
            in rendered.diagram
        )

        content = "\n".join(
            bootstrap_cmd._generate_module_dependency_section(summary, page_map, {})
        )
        assert (
            "> Diagram shows 55 of 60 local dependency edges; 5 omitted to keep "
            "the visualization within the generated-diagram limits. Complete "
            "inbound and outbound dependencies remain in the tables below."
        ) in content
        assert content.count("| Inbound |") == 6
        assert content.count("| Outbound |") == 5
        assert summary == original

    def test_module_dependency_map_falls_back_to_packages_then_tables(self):
        summary, _, _ = _dense_module_dependency_summary()
        page_map = {
            node: Path(node).stem for node in summary["nodes"]
        }
        oversized_summary = deepcopy(summary)
        oversized_summary["nodes"] = [
            *summary["nodes"],
            *(f"extra/module_{index}.py" for index in range(29)),
        ]

        rendered = bootstrap_cmd._module_dependency_graph(
            oversized_summary, page_map, {}
        )

        assert rendered is not None
        assert rendered.diagram is not None
        assert rendered.projection == "package"
        assert rendered.total_edges == rendered.shown_edges == 2
        assert rendered.omitted_edges == 0
        assert len(rendered.diagram.splitlines()[1:-1]) <= (
            GENERATED_DIAGRAM_LINE_LIMIT
        )
        assert 'click n1 "../modules/focal.md"' in rendered.diagram
        assert "../modules/pkg.md" not in rendered.diagram
        package_content = "\n".join(
            bootstrap_cmd._generate_module_dependency_section(
                oversized_summary, page_map, {}
            )
        )
        assert "collapsed to package relationships" in package_content
        assert (
            "Complete inbound and outbound dependencies remain in the tables below."
            in package_content
        )
        assert package_content.count("| Inbound |") == 6
        assert package_content.count("| Outbound |") == 5

        table_only_summary = {
            "file": "pkg/focal.py",
            "detail": "module",
            "inbound": [f"package_{index}" for index in range(40)],
            "outbound": [],
            "nodes": [
                "pkg/focal.py",
                *(f"package_{index}" for index in range(40)),
            ],
            "edges": [
                (f"package_{index}", "pkg/focal.py") for index in range(40)
            ],
            "cycle_participation": False,
            "cycle_edges": [],
            "external": {},
            "overflow": {},
        }
        table_only = bootstrap_cmd._module_dependency_graph(
            table_only_summary, page_map, {}
        )
        table_content = "\n".join(
            bootstrap_cmd._generate_module_dependency_section(
                table_only_summary, page_map, {}
            )
        )

        assert table_only is not None
        assert table_only.diagram is None
        assert (
            table_only.total_edges,
            table_only.shown_edges,
            table_only.omitted_edges,
        ) == (40, 0, 40)
        assert "```mermaid" not in table_content
        assert (
            "Diagram shows 0 of 40 local dependency edges; 40 omitted because "
            "its fixed nodes"
        ) in table_content
        assert "No internal module dependencies detected" not in table_content
        assert table_content.count("| Inbound |") == 40
        assert table_content.count("| Outbound |") == 0

        character_page_map = {
            node: f"{Path(node).stem}-{'x' * 440}"
            for node in summary["nodes"]
        }
        character_limited = bootstrap_cmd._module_dependency_graph(
            summary, character_page_map, {}
        )

        assert character_limited is not None
        assert character_limited.diagram is not None
        assert character_limited.projection == "module"
        assert 0 < character_limited.shown_edges < 55
        assert character_limited.omitted_edges > 5
        character_body = character_limited.diagram.splitlines()[1:-1]
        assert len(character_body) <= GENERATED_DIAGRAM_LINE_LIMIT
        assert len("\n".join(character_body)) <= GENERATED_DIAGRAM_CHAR_LIMIT
        character_content = "\n".join(
            bootstrap_cmd._generate_module_dependency_section(
                summary, character_page_map, {}
            )
        )
        assert (
            f"Diagram shows {character_limited.shown_edges} of 60 local "
            f"dependency edges; {character_limited.omitted_edges} omitted to "
            "keep the visualization within the generated-diagram limits."
        ) in character_content

    def test_package_detail_table_only_message_describes_aggregates(
        self, monkeypatch
    ):
        summary = {
            "file": "pkg/service.py",
            "detail": "package",
            "inbound": [{"package": "adapters", "count": 2}],
            "outbound": [{"package": "storage", "count": 3}],
            "nodes": ["adapters", "pkg/service.py", "storage"],
            "edges": [
                ("adapters", "pkg/service.py"),
                ("pkg/service.py", "storage"),
            ],
            "cycle_participation": False,
            "cycle_edges": [],
            "external": {},
            "overflow": {},
        }
        monkeypatch.setattr(
            bootstrap_cmd,
            "_module_dependency_graph",
            lambda *_args, **_kwargs: types.SimpleNamespace(
                diagram=None,
                total_edges=2,
                shown_edges=0,
                omitted_edges=2,
                projection="none",
            ),
        )

        content = "\n".join(
            bootstrap_cmd._generate_module_dependency_section(summary, {}, {})
        )

        assert "0 of 2 package relationship edges" in content
        assert "every module neighbor count by top-level package" in content
        assert "Complete inbound and outbound dependencies" not in content
        assert "| Inbound | `adapters` (2) |" in content
        assert "| Outbound | `storage` (3) |" in content

    def test_entity_docstrings_escape_source_symbol_links(self):
        content = bootstrap_cmd._generate_entity_md(
            {
                "name": "Emitter",
                "line": 10,
                "docstring": (
                    "See [`Manager::manage`](`crate::Manager::manage`) and "
                    "[targets](EventTarget). See [site](https://example.test)."
                ),
                "methods": [
                    {
                        "name": "emit",
                        "signature": "(event: &str)",
                        "decorators": [],
                        "docstring": "Emits to [targets](EventTarget).",
                    }
                ],
            },
            "src/lib.rs",
            {},
            "src_lib",
        )

        assert "](`crate::Manager::manage`)" not in content
        assert "](EventTarget)" not in content
        assert "`Manager::manage` (`crate::Manager::manage`)" in content
        assert "targets (`EventTarget`)" in content
        assert "[site](https://example.test)" in content

    def test_haskell_module_page_uses_declared_module_and_inventory_shapes(self):
        content = bootstrap_cmd._generate_module_md(
            "hls-analysis/src/HLSAnalysis/API.hs",
            {
                "language": "haskell",
                "module": "HLSAnalysis.API",
                "imports": [
                    {
                        "module": "Data.Text",
                        "qualified": False,
                        "alias": None,
                        "line": 4,
                    },
                    {
                        "module": "Data.Map",
                        "qualified": True,
                        "alias": "Map",
                        "line": 5,
                    },
                ],
                "classes": [
                    {"name": "User", "kind": "data", "line": 7},
                    {"name": "Token", "kind": "newtype", "line": 9},
                    {"name": "UserId", "kind": "type", "line": 11},
                    {"name": "Renderable", "kind": "class", "line": 13},
                    {
                        "name": "instance Renderable User",
                        "kind": "instance",
                        "line": 16,
                    },
                ],
                "functions": [
                    {
                        "name": "apiName",
                        "kind": "signature",
                        "signature": "Text",
                        "line": 20,
                    },
                    {"name": "apiName", "kind": "value", "line": 21},
                ],
            },
            {
                "User": "User",
                "Token": "Token",
                "UserId": "UserId",
                "Renderable": "Renderable",
                "instance Renderable User": "instance_Renderable_User",
            },
        )

        assert "# HLSAnalysis.API Module" in content
        assert "**Path:** `hls-analysis/src/HLSAnalysis/API.hs`" in content
        assert "**Declared module:** `HLSAnalysis.API`" in content
        assert "| `Data.Map` | yes | `Map` | 5 |" in content
        assert "| `Data.Text` | no | — | 4 |" in content
        assert "## Declarations" in content
        assert "## Classes" not in content
        assert "| [User](../entities/User.md) | Data | 7 | — |" in content
        assert "| [Token](../entities/Token.md) | Newtype | 9 | — |" in content
        assert "| [UserId](../entities/UserId.md) | Type alias | 11 | — |" in content
        assert (
            "| [Renderable](../entities/Renderable.md) | Type class | 13 | — |"
            in content
        )
        assert (
            "| [instance Renderable User](../entities/instance_Renderable_User.md) | "
            "Instance | 16 | — |"
        ) in content
        assert "| `apiName` | Signature | `Text` | 20 | — |" in content
        assert "| `apiName` | Value | — | 21 | — |" in content

    def test_haskell_entity_page_uses_declaration_wording_and_safe_page_ids(self):
        inventory = {
            "hls-analysis/src/HLSAnalysis/API.hs": {
                "language": "haskell",
                "module": "HLSAnalysis.API",
                "classes": [
                    {
                        "name": "instance Renderable User",
                        "kind": "instance",
                        "line": 16,
                    }
                ],
                "functions": [],
                "imports": [],
            }
        }

        page_map = bootstrap_cmd.build_entity_page_map(inventory)
        page_id = page_map[
            ("instance Renderable User", "hls-analysis/src/HLSAnalysis/API.hs")
        ]
        content = bootstrap_cmd._generate_entity_md(
            {
                "name": "instance Renderable User",
                "kind": "instance",
                "line": 16,
            },
            "hls-analysis/src/HLSAnalysis/API.hs",
            {},
            "API",
        )

        assert page_id == "instance_Renderable_User"
        assert is_safe_page_id(page_id)
        assert "**Kind:** `Instance`" in content
        assert "## Declaration" in content
        assert "## Attributes" not in content
        assert "## Methods" not in content
        assert "**Bases:**" not in content

    def test_haskell_entity_relationship_summary_uses_declaration_kind_table(self):
        content = bootstrap_cmd._generate_entity_md(
            {"name": "Renderable", "kind": "class", "line": 13},
            "hls-analysis/src/HLSAnalysis/API.hs",
            {},
            "API",
            relationship_summary={
                "name": "Renderable",
                "file": "hls-analysis/src/HLSAnalysis/API.hs",
                "kind": "class",
                "methods_count": 4,
                "attributes": ["python_shaped_noise"],
                "bases": [
                    {
                        "name": "BaseRenderable",
                        "file": "hls-analysis/src/HLSAnalysis/Base.hs",
                    }
                ],
                "subclasses": [
                    {
                        "name": "HtmlRenderable",
                        "file": "hls-analysis/src/HLSAnalysis/Html.hs",
                    }
                ],
                "references": [
                    {
                        "symbol": "renderUser",
                        "kind": "type_reference",
                        "file": "hls-analysis/app/Main.hs",
                    }
                ],
            },
            module_page_map={
                "hls-analysis/src/HLSAnalysis/API.hs": "API",
                "hls-analysis/src/HLSAnalysis/Base.hs": "Base",
                "hls-analysis/src/HLSAnalysis/Html.hs": "Html",
                "hls-analysis/app/Main.hs": "Main",
            },
        )

        relationships = content.split("## Relationships", 1)[1]
        assert "| Module | Declaration kind |" in relationships
        assert "| [API](../modules/API.md) | Type class |" in relationships
        assert "| Module | Methods | Attributes |" not in relationships
        assert "Methods" not in relationships
        assert "Attributes" not in relationships
        assert "### Structure" in relationships
        assert (
            "| Base | `BaseRenderable` | [Base](../modules/Base.md) |" in relationships
        )
        assert (
            "| Subclass | `HtmlRenderable` | [Html](../modules/Html.md) |"
            in relationships
        )
        assert "### References" in relationships
        assert (
            "| `renderUser` | type_reference | [Main](../modules/Main.md) |"
            in relationships
        )

    def test_non_haskell_class_kind_keeps_methods_attributes_summary(self):
        content = "\n".join(
            bootstrap_cmd._generate_entity_relationship_section(
                {
                    "name": "Client",
                    "file": "web/client.ts",
                    "kind": "class",
                    "methods_count": 2,
                    "attributes": ["baseUrl"],
                    "bases": [],
                    "subclasses": [],
                    "references": [],
                },
                {"web/client.ts": "web_client"},
            )
        )

        assert "| Module | Methods | Attributes |" in content
        assert "| [web_client](../modules/web_client.md) | 2 | `baseUrl` |" in content
        assert "| Module | Declaration kind |" not in content

    def test_empty_haskell_module_inventory_does_not_render_broken_tables(self):
        content = bootstrap_cmd._generate_module_md(
            "Empty.hs",
            {
                "language": "haskell",
                "module": "Empty",
                "imports": [],
                "classes": [],
                "functions": [],
            },
        )

        assert "# Empty Module" in content
        assert "## Imports" not in content
        assert "## Declarations" not in content
        assert "## Functions" not in content
        assert "None" not in content

    def test_typescript_module_only_inventory_renders_module_signals(self):
        content = bootstrap_cmd._generate_module_md(
            "frontend/src/lib/api.ts",
            {
                "language": "typescript",
                "imports": [{"module": "axios", "name": "axios", "type": "default"}],
                "classes": [],
                "functions": [],
                "exports": ["default"],
                "constants": [
                    {"name": "BASE_URL", "line": 4, "exported": False},
                    {"name": "api", "line": 5, "exported": False},
                ],
                "module_calls": [
                    {"name": "create", "target": "api", "line": 5},
                    {"name": "use", "line": 7},
                ],
            },
        )

        assert "# api Module" in content
        assert "## Classes" not in content
        assert "## Functions" not in content
        assert "## Module Signals" in content
        assert "| Exports | `default` |" in content
        assert "| Constants | `BASE_URL`, `api` |" in content
        assert "| Module calls | `api = create`, `use` |" in content

    def test_javascript_module_only_inventory_renders_module_signals(self):
        content = bootstrap_cmd._generate_module_md(
            "feature-showcase/script.js",
            {
                "language": "javascript",
                "imports": [{"module": "react", "name": "React", "type": "default"}],
                "classes": [],
                "functions": [],
                "exports": ["runShowcase"],
                "constants": [{"name": "root", "line": 4, "exported": False}],
                "module_calls": [{"name": "render", "target": "root", "line": 8}],
            },
        )

        assert "# script Module" in content
        assert "## Module Signals" in content
        assert "| Exports | `runShowcase` |" in content
        assert "| Constants | `root` |" in content
        assert "| Module calls | `root = render` |" in content

    def test_javascript_function_declarations_render_on_module_not_entity_pages(self):
        inventory = {
            "docker/web-auth-proxy.js": {
                "language": "javascript",
                "imports": [],
                "classes": [],
                "functions": [
                    {
                        "name": "isTruthy",
                        "kind": "function",
                        "line": 3,
                        "end_line": 5,
                        "params": [{"name": "value", "type": "", "default": ""}],
                        "return_type": "",
                        "decorators": [],
                        "docstring": "",
                    },
                    {
                        "name": "withAuthHeaders",
                        "kind": "function",
                        "line": 7,
                        "end_line": 9,
                        "params": [{"name": "headers", "type": "", "default": "{}"}],
                        "return_type": "",
                        "decorators": [],
                        "docstring": "",
                    },
                ],
            }
        }

        content = bootstrap_cmd._generate_module_md(
            "docker/web-auth-proxy.js",
            inventory["docker/web-auth-proxy.js"],
            {},
        )

        assert bootstrap_cmd.build_entity_page_map(inventory) == {}
        assert "## Functions" in content
        assert "| `isTruthy` | `(value)` | — | — |" in content
        assert "| `withAuthHeaders` | `(headers = {})` | — | — |" in content
        assert "## Classes" not in content


class TestBootstrapIndex:
    def test_creates_index(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        index = (wiki_dir / "index.md").read_text(encoding="utf-8")
        assert "## Surface Overview" in index
        assert "| Entities | 2 |" in index
        assert "| Modules | 3 |" in index
        assert "| Workflows | 0 |" in index
        assert "| Guides | 0 |" in index
        assert "| Entry-point flows | 0 | No pages |" in index
        assert "| HTTP API contracts | 0 | No pages |" in index
        assert "| Dependency architecture | 2 |" in index
        assert "| Log | 1 | [Open log](log.md) |" in index
        assert "User" in index
        assert "Item" in index
        assert "models" in index

    def test_index_uses_landing_page_sections(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        index = (wiki_dir / "index.md").read_text(encoding="utf-8")
        assert (
            "This page is an exhaustive reference inventory of the selected "
            "source. Task-oriented guides are not yet available."
        ) in index
        assert "## Log" in index
        assert "- [Architectural log](log.md)" in index
        assert (wiki_dir / "guides").exists()

    def test_index_normalizes_module_summary_and_uses_precise_surface_labels(self):
        index = bootstrap_cmd._generate_index_md(
            [],
            [
                {
                    "name": "context_service",
                    "path": "pkg/context_service.py",
                    "docstring": (
                        "Returns priority-ranked, token-budgeted\n"
                        "context for supported clients.\n\n"
                        "Implementation details follow in a second paragraph."
                    ),
                },
                {"name": "fallback", "path": "pkg/fallback.py", "docstring": ""},
            ],
            flow_entries=[{"id": "api-run", "entry": "run"}],
            api_contracts_present=True,
            log_present=False,
        )

        assert (
            "[context_service](modules/context_service.md) - Returns "
            "priority-ranked, token-budgeted context for supported clients."
        ) in index
        assert "Implementation details follow" not in index
        assert "[fallback](modules/fallback.md) - `pkg/fallback.py`" in index
        assert "| Entry-point flows | 1 | [Open section](#entry-point-flows) |" in index
        assert (
            "| HTTP API contracts | 1 | [Open contracts](api-contracts.md) |"
            in index
        )
        assert "## Entry-point flows" in index
        assert "## HTTP API contracts" in index
        assert '<a id="user-flows"></a>' in index
        assert '<a id="api-contracts"></a>' in index
        assert "User Flows" not in index


class TestBootstrapLog:
    def test_appends_log(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        log = (wiki_dir / "log.md").read_text(encoding="utf-8")
        knowledge = load_knowledge_state(wiki_dir).knowledge
        assert knowledge is not None
        assert "### Wiki bootstrap" in log
        assert "### feat:" not in log
        assert "- Source: `.`" in log
        assert f"- Generator version: `{bootstrap_cmd.__version__}`" in log
        assert "- Source selection profile: none (default discovery)" in log
        assert "- Source selection fingerprint: none" in log
        assert (
            f"- Source snapshot digest: "
            f"`{knowledge.bundle.snapshot.source_snapshot_hash}`"
        ) in log
        assert "- Entry-point flows created:" in log
        assert "- HTTP API contract pages created:" in log
        assert str(tmp_project.resolve()) not in log

    def test_configured_snapshot_log_provenance_uses_canonical_profile(self, tmp_project):
        profile_path = tmp_project / "config" / "sources.json"
        profile_path.parent.mkdir()
        profile_path.write_text(
            json.dumps(
                {
                    "schema_version": "llm-wiki-source-selection/v1",
                    "include": ["main.py", "models.py"],
                    "exclude": [],
                }
            ),
            encoding="utf-8",
        )
        snapshot = bootstrap_cmd.build_source_snapshot(
            tmp_project,
            source_selection="config/sources.json",
        )

        lines = bootstrap_cmd._source_snapshot_log_lines(snapshot)
        expected_digest = bootstrap_cmd.runtime_source_snapshot_hash(
            snapshot,
            generation_inputs={},
        )

        assert "- Source selection profile: `config/sources.json`" in lines
        assert (
            f"- Source selection fingerprint: "
            f"`{snapshot.source_selection_fingerprint}`"
        ) in lines
        assert (
            f"- Source snapshot digest: "
            f"`{expected_digest}`"
        ) in lines
        assert str(tmp_project.resolve()) not in lines


class TestBootstrapOverwrite:
    def test_existing_wiki_is_rejected_without_mutation(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        user_page = wiki_dir / "entities" / "User.md"
        user_page.write_text("CUSTOM CONTENT")
        before = _tree_bytes(wiki_dir)
        capsys.readouterr()

        with pytest.raises(SystemExit) as exc_info:
            bootstrap_cmd.run(args)

        assert exc_info.value.code == 2
        assert _tree_bytes(wiki_dir) == before
        assert user_page.read_text(encoding="utf-8") == "CUSTOM CONTENT"
        output = capsys.readouterr().out
        assert "Bootstrap is first-use only" in output
        assert "llm-wiki sync --jobs 1" in output
        assert "llm-wiki migrate --dry-run" not in output
        assert "No files were changed" in output

    def test_overwrite_compatibility_flag_is_rejected_before_mutation(
        self, tmp_project, capsys
    ):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        user_page = wiki_dir / "entities" / "User.md"
        user_page.write_text("CUSTOM CONTENT")
        before = _tree_bytes(wiki_dir)
        capsys.readouterr()

        args_ow = _make_args(src_dir=".", wiki_dir=str(wiki_dir), overwrite=True)
        with pytest.raises(SystemExit) as exc_info:
            bootstrap_cmd.run(args_ow)

        assert exc_info.value.code == 2
        assert _tree_bytes(wiki_dir) == before
        assert user_page.read_text(encoding="utf-8") == "CUSTOM CONTENT"
        assert "compatibility `overwrite` option is no longer supported" in (
            capsys.readouterr().out
        )

    def test_exact_init_scaffold_is_accepted(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        init_cmd.run(
            types.SimpleNamespace(
                agent="generic",
                wiki_dir=str(wiki_dir),
                no_skills=True,
            )
        )
        assert not (wiki_dir / ".llm-wiki-manifest.json").exists()
        capsys.readouterr()

        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir=str(wiki_dir)))

        assert (wiki_dir / ".llm-wiki-manifest.json").is_file()

    def test_exact_init_scaffold_with_fallback_agent_config_is_accepted(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        project = tmp_path / "non_git_project"
        project.mkdir()
        (project / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        monkeypatch.chdir(project)
        wiki_dir = project / "docs" / "llm_wiki"
        init_cmd.run(
            types.SimpleNamespace(
                agent="generic",
                wiki_dir=str(wiki_dir),
                no_skills=True,
            )
        )
        config_path = wiki_dir / ".llm-wiki-agent"
        assert config_path.is_file()
        capsys.readouterr()

        bootstrap_cmd.run(
            _make_args(
                src_dir=".",
                wiki_dir=str(wiki_dir),
                source_adapter=True,
            )
        )

        assert (wiki_dir / ".llm-wiki-manifest.json").is_file()

    def test_modified_fallback_agent_config_is_rejected_without_mutation(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        project = tmp_path / "non_git_project"
        project.mkdir()
        (project / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        monkeypatch.chdir(project)
        wiki_dir = project / "docs" / "llm_wiki"
        init_cmd.run(
            types.SimpleNamespace(
                agent="generic",
                wiki_dir=str(wiki_dir),
                no_skills=True,
            )
        )
        config_path = wiki_dir / ".llm-wiki-agent"
        config_path.write_text(
            config_path.read_text(encoding="utf-8").replace(
                '"agent": "generic"',
                '"agent": "custom"',
            ),
            encoding="utf-8",
        )
        before = _tree_bytes(wiki_dir)
        capsys.readouterr()
        monkeypatch.setattr(
            bootstrap_cmd,
            "get_inventory_result",
            lambda *_args, **_kwargs: pytest.fail(
                "modified-config preflight must run before extraction"
            ),
        )

        with pytest.raises(SystemExit) as exc_info:
            bootstrap_cmd.run(
                _make_args(
                    src_dir=".",
                    wiki_dir=str(wiki_dir),
                    source_adapter=True,
                )
            )

        assert exc_info.value.code == 2
        assert _tree_bytes(wiki_dir) == before


class TestBootstrapShallow:
    def test_shallow_depth(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir), depth="shallow")
        bootstrap_cmd.run(args)

        # Pages created but minimal content
        assert (wiki_dir / "entities" / "User.md").exists()


class TestBootstrapSkipWorkflows:
    def test_skip_workflows_flag(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir), skip_workflows=True)
        bootstrap_cmd.run(args)

        workflows_dir = wiki_dir / "workflows"
        workflow_files = list(workflows_dir.glob("*.md"))
        assert len(workflow_files) == 0

    def test_workflow_docstring_escapes_source_symbol_links(self):
        content = bootstrap_cmd._generate_workflow_md(
            "emit_to",
            {
                "entry": "lib.emit_to",
                "modules_touched_paths": ["src/lib.rs"],
                "chain": [],
                "docstring": (
                    "Emits to [targets](EventTarget). See [docs](https://example.test)."
                ),
            },
            {"src/lib.rs": "src_lib"},
        )

        assert "](EventTarget)" not in content
        assert "> Emits to targets (`EventTarget`)." in content
        assert "[docs](https://example.test)" in content
        assert "## Behavior" in content
        assert "This workflow starts at `lib.emit_to`." in content
        assert "No call-chain steps were detected by static analysis." in content
        assert "belong in Behavior" in content
        assert "placeholder" not in content.casefold()
        assert "refine" not in content.casefold()

    def test_workflow_regeneration_preserves_reviewed_behavior(self):
        original = bootstrap_cmd._generate_workflow_md(
            "dispatch",
            {
                "entry": "app.dispatch",
                "modules_touched": ["app"],
                "chain": ["app.dispatch", "app.prepare"],
            },
        )
        reviewed = original.replace(
            "This workflow starts at `app.dispatch`. The generated sequence is "
            "a bounded static projection; runtime ordering, branching, and side "
            "effects require source-level confirmation.",
            "Dispatches a reviewed request through the primary path.",
        )
        regenerated = bootstrap_cmd._generate_workflow_md(
            "dispatch",
            {
                "entry": "app.dispatch",
                "modules_touched": ["app"],
                "chain": ["app.dispatch", "app.finish"],
            },
        )

        merged = bootstrap_cmd._preserve_level_two_section(
            reviewed, regenerated, "Behavior"
        )

        assert "app.finish" in merged
        assert "app.prepare" not in merged
        assert "Dispatches a reviewed request through the primary path." in merged


class TestBootstrapUpdatesAgentConstraints:
    def test_source_adapter_skips_agent_constraint_update(self, tmp_project, capsys):
        from llm_wiki_cli.commands import init_cmd
        import types

        init_cmd.run(types.SimpleNamespace(agent="claude", wiki_dir="docs/llm_wiki"))
        wiki_dir = tmp_project / "adapter_wiki"

        bootstrap_cmd.run(
            _make_args(src_dir=".", wiki_dir=str(wiki_dir), source_adapter=True)
        )

        content = Path("CLAUDE.md").read_text(encoding="utf-8")
        start = content.index("# --- LLM Wiki Maintainer Constraints ---")
        end = content.index("# --- End LLM Wiki Constraints ---") + len(
            "# --- End LLM Wiki Constraints ---"
        )
        block = content[start:end]
        assert "docs/llm_wiki" in block
        assert str(wiki_dir) not in block

    def test_updates_path_in_constraint_block(self, tmp_project, capsys):
        from llm_wiki_cli.commands import init_cmd
        import types

        init_cmd.run(types.SimpleNamespace(agent="claude", wiki_dir="docs/llm_wiki"))
        assert "docs/llm_wiki" in Path("CLAUDE.md").read_text(encoding="utf-8")

        # Bootstrap to a different wiki dir
        wiki_dir = tmp_project / "my_docs" / "wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        content = Path("CLAUDE.md").read_text(encoding="utf-8")
        # Verify the constraint block was updated (preamble outside the block is unchanged)
        start = content.index("# --- LLM Wiki Maintainer Constraints ---")
        end = content.index("# --- End LLM Wiki Constraints ---") + len(
            "# --- End LLM Wiki Constraints ---"
        )
        block = content[start:end]
        assert str(wiki_dir) in block
        assert "docs/llm_wiki" not in block

    def test_no_change_when_default_path(self, tmp_project, capsys):
        from llm_wiki_cli.commands import init_cmd
        import types

        init_cmd.run(types.SimpleNamespace(agent="claude", wiki_dir="docs/llm_wiki"))
        original = Path("CLAUDE.md").read_text(encoding="utf-8")

        # Bootstrap with the default path — file should be unchanged
        args = _make_args(src_dir=".", wiki_dir="docs/llm_wiki")
        bootstrap_cmd.run(args)

        assert Path("CLAUDE.md").read_text(encoding="utf-8") == original


class TestBootstrapCreatesManifest:
    """bootstrap must write a sync manifest so `llm-wiki sync` works afterwards."""

    def test_manifest_created(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        manifest_path = wiki_dir / ".llm-wiki-manifest.json"
        assert manifest_path.exists(), "bootstrap should create the sync manifest"
        surface_path = wiki_dir / SURFACE_INDEX_FILENAME
        assert surface_path.exists(), "bootstrap should create the surface index"

    def test_manifest_contains_sources(self, tmp_project, capsys):
        import json

        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        data = json.loads(
            (wiki_dir / ".llm-wiki-manifest.json").read_text(encoding="utf-8")
        )
        assert "sources" in data
        assert len(data["sources"]) > 0
        # Every source entry should have a hash and entities list
        for filepath, entry in data["sources"].items():
            assert "hash" in entry
            assert "entities" in entry

    def test_include_tests_go_creates_go_test_module_and_manifest_entry(
        self, tmp_path, monkeypatch, capsys
    ):
        (tmp_path / "main_test.go").write_text(
            "package main\n\nfunc TestMain() {}\n", encoding="utf-8"
        )
        wiki_dir = tmp_path / "wiki"
        seen = {}
        real_build_source_snapshot = bootstrap_cmd.build_source_snapshot

        def fake_snapshot(src_dir, **kwargs):
            seen["snapshot_include_tests"] = kwargs.get("include_tests")
            return real_build_source_snapshot(src_dir, **kwargs)

        def fake_inventory(src_dir, *args, **kwargs):
            seen["inventory_include_tests"] = kwargs["include_tests"]
            return InventoryResult(
                {
                    "main_test.go": {
                        "classes": [],
                        "functions": [{"name": "TestMain", "line": 3}],
                        "language": "go",
                    }
                },
                {"go": ExtractorStatus("go", "ok", 1)},
            )

        monkeypatch.setattr(bootstrap_cmd, "build_source_snapshot", fake_snapshot)
        monkeypatch.setattr(bootstrap_cmd, "get_inventory_result", fake_inventory)
        monkeypatch.setattr(bootstrap_cmd, "get_docker_inventory", lambda *a, **k: {})
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(
            _make_args(
                src_dir=".",
                wiki_dir=str(wiki_dir),
                include_tests=["go"],
                skip_flows=True,
                skip_dependencies=True,
            )
        )

        assert set(seen["snapshot_include_tests"]) == {"go"}
        assert set(seen["inventory_include_tests"]) == {"go"}
        assert (wiki_dir / "modules" / "main_test.md").exists()
        data = json.loads(
            (wiki_dir / ".llm-wiki-manifest.json").read_text(encoding="utf-8")
        )
        assert "main_test.go" in data["sources"]
        assert data["sources"]["main_test.go"]["module_page"] == "main_test"

    def test_haskell_inventory_creates_module_summary_and_manifest_entry(
        self, tmp_path, monkeypatch, capsys
    ):
        (tmp_path / "Main.hs").write_text("module Main where\n", encoding="utf-8")
        wiki_dir = tmp_path / "wiki"
        seen = {}

        def fake_inventory(src_dir, *args, **kwargs):
            seen["helper_cache_dir"] = kwargs["helper_cache_dir"]
            return InventoryResult(
                {
                    "Main.hs": {
                        "classes": [],
                        "functions": [{"name": "main", "line": 1}],
                        "language": "haskell",
                    }
                },
                {"haskell": ExtractorStatus("haskell", "ok", 1)},
            )

        monkeypatch.setattr(bootstrap_cmd, "get_inventory_result", fake_inventory)
        monkeypatch.setattr(bootstrap_cmd, "get_docker_inventory", lambda *a, **k: {})
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(
            _make_args(
                src_dir=".",
                wiki_dir=str(wiki_dir),
                format="json",
                source_adapter=True,
                helper_cache_dir=str(tmp_path / "helper-cache"),
                skip_flows=True,
                skip_dependencies=True,
            )
        )

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert seen["helper_cache_dir"] == str(tmp_path / "helper-cache")
        assert data["source_files"] == 1
        assert data["functions"] == 1
        assert "unsupported_sources" not in data
        assert (wiki_dir / "modules" / "Main.md").exists()
        manifest = json.loads(
            (wiki_dir / ".llm-wiki-manifest.json").read_text(encoding="utf-8")
        )
        assert manifest["sources"]["Main.hs"]["language"] == "haskell"
        assert manifest["sources"]["Main.hs"]["module_page"] == "Main"

    def test_haskell_local_dependency_map_uses_declared_module_imports(
        self, tmp_path, monkeypatch, capsys
    ):
        (tmp_path / "hls-analysis" / "app").mkdir(parents=True)
        (tmp_path / "hls-analysis" / "src" / "HLSAnalysis").mkdir(parents=True)
        (tmp_path / "hls-analysis" / "app" / "Main.hs").write_text(
            "module Main where\nimport HLSAnalysis.API\n", encoding="utf-8"
        )
        (tmp_path / "hls-analysis" / "src" / "HLSAnalysis" / "API.hs").write_text(
            "module HLSAnalysis.API where\n", encoding="utf-8"
        )
        wiki_dir = tmp_path / "wiki"

        def fake_inventory(src_dir, *args, **kwargs):
            return InventoryResult(
                {
                    "hls-analysis/app/Main.hs": {
                        "language": "haskell",
                        "module": "Main",
                        "imports": [
                            {
                                "module": "HLSAnalysis.API",
                                "qualified": False,
                                "alias": None,
                                "line": 2,
                            }
                        ],
                        "classes": [],
                        "functions": [{"name": "main", "kind": "value", "line": 3}],
                    },
                    "hls-analysis/src/HLSAnalysis/API.hs": {
                        "language": "haskell",
                        "module": "HLSAnalysis.API",
                        "imports": [],
                        "classes": [{"name": "User", "kind": "data", "line": 3}],
                        "functions": [],
                    },
                },
                {"haskell": ExtractorStatus("haskell", "ok", 2)},
            )

        monkeypatch.setattr(bootstrap_cmd, "get_inventory_result", fake_inventory)
        monkeypatch.setattr(bootstrap_cmd, "get_docker_inventory", lambda *a, **k: {})
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(
            _make_args(
                src_dir=str(tmp_path),
                wiki_dir=str(wiki_dir),
                skip_flows=True,
            )
        )

        main_module = (wiki_dir / "modules" / "Main.md").read_text(encoding="utf-8")
        api_module = (wiki_dir / "modules" / "API.md").read_text(encoding="utf-8")
        assert "[API](../modules/API.md)" in main_module
        assert "[Main](../modules/Main.md)" in api_module

    def test_surface_index_contains_pages_and_counts(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        data = json.loads(
            (wiki_dir / SURFACE_INDEX_FILENAME).read_text(encoding="utf-8")
        )
        assert data["schema_version"] == "llm-wiki-surface-index/v1"
        assert data["counts"]["by_kind"]["entities"] == 2
        assert data["counts"]["by_kind"]["modules"] == 3
        assert data["counts"]["dependency_architecture"] == 2
        assert any(page["canonical_path"] == "index.md" for page in data["pages"])
        assert all(
            not Path(page["source_path"] or "").is_absolute() for page in data["pages"]
        )
        by_path = {page["canonical_path"]: page for page in data["pages"]}
        assert (
            by_path["entities/User.md"]["id"],
            by_path["entities/User.md"]["mcp_uri"],
        ) == ("User", "llm-wiki://entities/User")
        assert (
            by_path["modules/models.md"]["id"],
            by_path["modules/models.md"]["mcp_uri"],
        ) == ("models", "llm-wiki://modules/models")

        deterministic_payloads = [
            data,
            json.loads(
                (wiki_dir / ".llm-wiki-knowledge.json").read_text(encoding="utf-8")
            ),
            json.loads(
                (wiki_dir / ".llm-wiki-manifest.json").read_text(encoding="utf-8")
            ),
        ]

        def nested_keys(value):
            if isinstance(value, dict):
                return set(value).union(
                    *(nested_keys(item) for item in value.values())
                )
            if isinstance(value, list):
                return set().union(*(nested_keys(item) for item in value))
            return set()

        forbidden_time_keys = {
            "created_at",
            "generated_at",
            "mtime",
            "mtime_ns",
            "timestamp",
            "updated_at",
        }
        assert all(
            nested_keys(payload).isdisjoint(forbidden_time_keys)
            for payload in deterministic_payloads
        )

    def test_sync_succeeds_after_bootstrap(self, tmp_project, capsys):
        """After bootstrap, running sync should not fail with 'no manifest'."""
        from llm_wiki_cli.commands import sync_cmd
        import types

        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        sync_args = types.SimpleNamespace(
            src_dir=".",
            wiki_dir=str(wiki_dir),
        )
        # Should not raise SystemExit
        sync_cmd.run(sync_args)


class TestBootstrapExternalSource:
    def test_allows_external_src_with_explicit_flag(
        self, tmp_path, monkeypatch, capsys
    ):
        workspace = tmp_path / "workspace"
        source = tmp_path / "source"
        workspace.mkdir()
        source.mkdir()
        (source / "app.py").write_text(
            "class ExternalApp:\n    pass\n", encoding="utf-8"
        )

        monkeypatch.chdir(workspace)
        bootstrap_cmd.run(
            _make_args(
                src_dir=str(source),
                wiki_dir="docs/llm_wiki",
                format="json",
                source_adapter=True,
                allow_external_src=True,
            )
        )

        data = json.loads(capsys.readouterr().out)
        assert data["src_dir"] == str(source)
        assert (workspace / "docs" / "llm_wiki" / "modules" / "app.md").exists()

    def test_managed_configured_external_bootstrap_uses_trusted_source_extractor(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys,
    ) -> None:
        workspace = tmp_path / "workspace"
        source = tmp_path / "external-source"
        workspace.mkdir()
        source.mkdir()
        (source / "app.jscustom").write_text("run\n", encoding="utf-8")
        profile = source / "config" / "sources.json"
        profile.parent.mkdir()
        profile.write_text(
            json.dumps(
                {
                    "schema_version": "llm-wiki-source-selection/v1",
                    "include": ["app.jscustom"],
                    "exclude": [],
                }
            ),
            encoding="utf-8",
        )
        _write_toy_extractor_plugin(source)
        monkeypatch.chdir(workspace)

        bootstrap_cmd.run(
            _make_args(
                src_dir=str(source),
                wiki_dir="wiki",
                allow_external_src=True,
                source_selection="config/sources.json",
            )
        )
        capsys.readouterr()

        wiki = workspace / "wiki"
        assert (wiki / "modules" / "app.md").exists()
        knowledge = load_knowledge_state(wiki).knowledge
        assert knowledge is not None
        assert [
            (component.component_id, component.version)
            for component in knowledge.bundle.producer.plugins
        ] == [("bootstrap-toy-extractor", "0.1.0")]
        log = (wiki / "log.md").read_text(encoding="utf-8")
        assert (
            f"- Source snapshot digest: "
            f"`{knowledge.bundle.snapshot.source_snapshot_hash}`"
        ) in log
        assert "bootstrap-toy-extractor/toy" in (
            wiki / ".llm-wiki-knowledge.json"
        ).read_text(encoding="utf-8")

    def test_managed_unconfigured_external_bootstrap_keeps_legacy_ambient_extractor(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys,
    ) -> None:
        workspace = tmp_path / "workspace"
        source = tmp_path / "external-source"
        workspace.mkdir()
        source.mkdir()
        (source / "app.jscustom").write_text("run\n", encoding="utf-8")
        _write_toy_extractor_plugin(workspace)
        monkeypatch.chdir(workspace)

        bootstrap_cmd.run(
            _make_args(
                src_dir=str(source),
                wiki_dir="wiki",
                allow_external_src=True,
            )
        )
        capsys.readouterr()

        wiki = workspace / "wiki"
        assert (wiki / "modules" / "app.md").exists()
        knowledge = load_knowledge_state(wiki).knowledge
        assert knowledge is not None
        assert [
            (component.component_id, component.version)
            for component in knowledge.bundle.producer.plugins
        ] == [("bootstrap-toy-extractor", "0.1.0")]


class TestGenerateFlowMd:
    def test_renders_entry_modules_and_diagram(self):
        flow = {
            "entry": {
                "id": "api-run",
                "category": "api",
                "file": "pkg/api.py",
                "symbol": "run",
                "label": "run",
            },
            "steps": [
                {"depth": 0, "file": "pkg/api.py", "symbol": "run", "kind": "entry"},
                {
                    "depth": 1,
                    "file": "pkg/helper.py",
                    "symbol": "work",
                    "kind": "internal",
                },
                {"depth": 1, "file": None, "symbol": "getcwd", "kind": "external"},
            ],
            "modules_touched": ["pkg/api.py", "pkg/helper.py"],
            "truncated": True,
        }
        data_flow = {
            "steps": [
                {
                    "index": 1,
                    "symbol": "run",
                    "file": "pkg/api.py",
                    "kind": "entry",
                    "inputs": [{"kind": "param", "name": "payload", "type": "dict"}],
                    "returns": [{"kind": "name", "value": "result", "line": 4}],
                },
                {
                    "index": 2,
                    "symbol": "work",
                    "file": "pkg/helper.py",
                    "kind": "internal",
                },
            ],
            "transfers": [
                {
                    "from": "run",
                    "to": "work",
                    "from_step": 1,
                    "to_step": 2,
                    "line": 4,
                    "call": "work(payload)",
                    "kind": "internal",
                }
            ],
            "boundaries": [
                {
                    "step": "run",
                    "kind": "filesystem_write",
                    "target": "path.write_text",
                    "line": 5,
                }
            ],
            "gaps": [
                {
                    "kind": "unresolved_call",
                    "step": "run",
                    "target": "client.publish",
                    "line": 6,
                }
            ],
        }
        md = bootstrap_cmd._generate_flow_md(
            flow, {"pkg/api.py": "api", "pkg/helper.py": "helper"}, data_flow=data_flow
        )
        assert md.startswith("# run")
        assert "**Entry point:** `run` (`api`)" in md
        assert "[api](../modules/api.md)" in md
        assert "[helper](../modules/helper.md)" in md
        assert "sequenceDiagram" in md
        assert md.index("## Data flow") < md.index("## Behavior")
        assert "flowchart LR" in md
        assert 's1 -->|"work(payload)"| s2' in md
        assert 'click s1 "../modules/api.md"' in md
        assert 'click s2 "../modules/helper.md"' in md
        assert "| filesystem_write | `path.write_text` | `run` | 5 |" in md
        assert "| run | work | 4 | `work(payload)` |" in md
        assert "client.publish" in md
        assert "-->>" in md  # external call rendered as a dashed arrow
        assert "truncated" in md
        assert "## Behavior" in md
        assert "This flow starts at `run` and is classified as `api`." in md
        assert "belong in Behavior" in md
        assert "placeholder" not in md.casefold()
        assert "refine" not in md.casefold()

        dense_data_flow = {
            "steps": [
                {
                    "index": index,
                    "symbol": f"step_{index}",
                    "kind": "internal",
                }
                for index in range(1, 11)
            ],
            "transfers": [
                {
                    "from": "step_1",
                    "to": f"step_{(index % 9) + 2}",
                    "from_step": 1,
                    "to_step": (index % 9) + 2,
                    "line": index + 1,
                    "call": f"call_{index}()",
                    "kind": "internal",
                }
                for index in range(50)
            ],
            "boundaries": [
                {
                    "step": "step_1",
                    "step_index": 1,
                    "kind": "filesystem_write",
                    "target": f"target_{index}",
                    "line": index + 1,
                }
                for index in range(50)
            ],
            "gaps": [],
        }
        dense = "\n".join(
            bootstrap_cmd._generate_data_flow_section(dense_data_flow, {}, {})
        )

        assert (
            "Data-flow diagram shows 56 of 100 transfer and boundary "
            "relationships; 44 omitted"
        ) in dense
        assert 's1 -->|"call_49()"|' in dense
        assert "target_5" in re.findall(
            r"```mermaid\n(.*?)\n```", dense, flags=re.DOTALL
        )[0]
        assert "| step_1 | step_6 | 50 | `call_49()` |" in dense
        assert "| filesystem_write | `target_49` | `step_1` | 50 |" in dense
        _assert_generated_diagram_budgets(dense)

        oversized_steps = {
            "steps": [
                {"index": index, "symbol": f"step_{index}", "kind": "internal"}
                for index in range(1, 42)
            ],
            "transfers": [
                {
                    "from": "step_1",
                    "to": "step_41",
                    "from_step": 1,
                    "to_step": 41,
                    "line": 42,
                    "call": "finish()",
                    "kind": "internal",
                }
            ],
            "boundaries": [],
            "gaps": [],
        }
        table_only = "\n".join(
            bootstrap_cmd._generate_data_flow_section(oversized_steps, {}, {})
        )

        assert "```mermaid" not in table_only
        assert (
            "Data-flow diagram shows 0 of 41 step nodes (41 omitted) and 0 of 1 "
            "transfer and boundary relationships (1 omitted)"
        ) in table_only
        assert "| step_1 | step_41 | 42 | `finish()` |" in table_only

        no_relationships = dict(oversized_steps)
        no_relationships["transfers"] = []
        no_relationships_table = "\n".join(
            bootstrap_cmd._generate_data_flow_section(no_relationships, {}, {})
        )

        assert "```mermaid" not in no_relationships_table
        assert (
            "Data-flow diagram shows 0 of 41 step nodes (41 omitted) and 0 of 0 "
            "transfer and boundary relationships (0 omitted)"
        ) in no_relationships_table

    def test_no_calls_uses_neutral_static_empty_state(self):
        flow = {
            "entry": {
                "id": "api-x",
                "category": "api",
                "file": "m.py",
                "symbol": "x",
                "label": "x",
            },
            "steps": [{"depth": 0, "file": "m.py", "symbol": "x", "kind": "entry"}],
            "modules_touched": ["m.py"],
            "truncated": False,
        }
        md = bootstrap_cmd._generate_flow_md(flow, {"m.py": "m"})
        assert "No outbound calls were detected by static analysis." in md
        assert "sequenceDiagram" not in md
        assert "manually" not in md.casefold()
        assert "placeholder" not in md.casefold()

    def test_async_process_main_renders_dispatch_and_related_modules(self, tmp_path):
        _write_project_team_open_style_async_main(tmp_path)
        inventory = get_inventory(str(tmp_path), deep=True)
        edges = resolve_call_edges(inventory)
        entry = [
            entry
            for entry in get_entry_points(inventory)
            if entry["id"] == "process-main"
        ][0]
        flow = build_flow(entry, edges)
        data_flow = analyze_data_flow(inventory, flow, edges)

        md = bootstrap_cmd._generate_flow_md(
            flow,
            {
                "src/main.py": "src_main",
                "src/cli/commands.py": "commands",
                "src/cli/orchestrator.py": "orchestrator",
            },
            data_flow=data_flow,
        )

        assert "No outbound calls detected" not in md
        assert "**Entry point:** `__main__` (`process`)" in md
        assert "[commands](../modules/commands.md)" in md
        assert "[orchestrator](../modules/orchestrator.md)" in md
        assert "**Related modules:**" in md
        assert "`asyncio.run(main_entry(...))`" in md
        assert "| __main__ | run | 11 | `asyncio.run(main_entry(...))` |" in md

    def test_long_module_metadata_is_bounded_with_complete_linked_details(self):
        touched_paths = [f"pkg/touched_{index:02d}.py" for index in range(18)]
        related_paths = [f"pkg/related_{index:02d}.py" for index in range(18)]
        page_map = {
            path: Path(path).stem for path in [*touched_paths, *related_paths]
        }
        flow = {
            "entry": {
                "id": "api-run",
                "category": "api",
                "file": touched_paths[0],
                "symbol": "run",
                "label": "run",
            },
            "steps": [
                {
                    "depth": 0,
                    "file": touched_paths[0],
                    "symbol": "run",
                    "kind": "entry",
                }
            ],
            "modules_touched": touched_paths,
            "related_modules": related_paths,
            "truncated": False,
        }

        md = bootstrap_cmd._generate_flow_md(flow, page_map)
        metadata_lines = [
            line
            for line in md.splitlines()
            if line.startswith(("**Modules touched:**", "**Related modules:**"))
        ]

        assert len(metadata_lines) == 2
        assert all(
            len(line) <= bootstrap_cmd._FLOW_MODULE_HEADER_CHAR_LIMIT
            for line in metadata_lines
        )
        assert "**Complete modules touched:**" in md
        assert "**Complete related modules:**" in md
        assert "touched_17.md)\n\n**Related modules:**" in md
        for path in [*touched_paths, *related_paths]:
            page = page_map[path]
            assert f"[{page}](../modules/{page}.md)" in md

    def test_call_sequence_is_bounded_for_large_flows(self):
        flow = {
            "entry": {
                "id": "api-run",
                "category": "api",
                "file": "m.py",
                "symbol": "run",
                "label": "run",
            },
            "steps": [{"depth": 0, "file": "m.py", "symbol": "run", "kind": "entry"}]
            + [
                {
                    "depth": 1,
                    "file": "m.py",
                    "symbol": f"call_{index}",
                    "kind": "internal",
                }
                for index in range(1, 41)
            ],
            "modules_touched": ["m.py"],
            "truncated": False,
        }

        md = bootstrap_cmd._generate_flow_md(flow, {"m.py": "m"})

        assert "Call sequence diagram shows 30 of 40 interactions; 10 omitted" in md
        assert "call_30" in md
        assert "call_31" not in md
        assert md.count("->>") == 30
        _assert_generated_diagram_budgets(md)

        long_flow = deepcopy(flow)
        long_flow["steps"] = [
            {"depth": 0, "file": "m.py", "symbol": "run", "kind": "entry"}
        ] + [
            {
                "depth": 1,
                "file": "m.py",
                "symbol": f"call_{index}_{'x' * 300}",
                "kind": "internal",
            }
            for index in range(1, 41)
        ]
        long_md = bootstrap_cmd._generate_flow_md(long_flow, {"m.py": "m"})
        shown = long_md.count("->>")

        assert long_md == bootstrap_cmd._generate_flow_md(long_flow, {"m.py": "m"})
        assert 0 < shown < bootstrap_cmd._FLOW_SEQUENCE_INTERACTION_LIMIT
        assert (
            f"Call sequence diagram shows {shown} of 40 interactions; "
            f"{40 - shown} omitted"
        ) in long_md
        _assert_generated_diagram_budgets(long_md)


class TestBootstrapFlows:
    def _write_project(self, tmp_path):
        (tmp_path / "api.py").write_text(
            textwrap.dedent("""\
            __all__ = ["run"]

            def run():
                return _helper()

            def _helper():
                return 1
        """)
        )

    def test_generates_flow_page_with_sequence_diagram(
        self, tmp_path, monkeypatch, capsys
    ):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))
        flow_page = tmp_path / "wiki" / "flows" / "api-run.md"
        assert flow_page.exists()
        text = flow_page.read_text(encoding="utf-8")
        assert "```mermaid" in text
        assert "sequenceDiagram" in text
        assert "_helper" in text
        assert "## Behavior" in text

    def test_plugin_detector_creates_flow_page(self, tmp_path, monkeypatch, capsys):
        _write_entrypoint_detector_plugin(
            tmp_path,
            body="""
            def detect(inventory):
                return [{
                    "category": "task",
                    "file": "tasks.py",
                    "symbol": "handle",
                    "label": "task-handler",
                }]
            """,
        )
        (tmp_path / "tasks.py").write_text("def handle():\n    return 1\n")
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))

        flow_page = tmp_path / "wiki" / "flows" / "task-task-handler.md"
        assert flow_page.exists()
        assert "# task-handler" in flow_page.read_text(encoding="utf-8")

    def test_source_root_plugins_drive_flow_detection_and_style(
        self, tmp_path, monkeypatch, capsys
    ):
        source = tmp_path / "source"
        source.mkdir()
        _write_entrypoint_detector_plugin(
            source,
            body="""
            def detect(inventory):
                return [{
                    "category": "task",
                    "file": "tasks.py",
                    "symbol": "handle",
                    "label": "source-task",
                }]
            """,
        )
        _write_diagram_style_plugin(
            source,
            body="""
            def style(context):
                if context["surface"] == "data_flow":
                    return {"direction": "RL"}
                return {}
            """,
        )
        _write_diagram_style_plugin(
            tmp_path,
            body="""
            def style(context):
                if context["surface"] == "data_flow":
                    return {"direction": "TD"}
                return {}
            """,
        )
        (source / "tasks.py").write_text(
            textwrap.dedent("""\
            def handle():
                return helper()

            def helper():
                return 1
            """),
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(_make_args(src_dir="source", wiki_dir="wiki"))

        flow_page = tmp_path / "wiki" / "flows" / "task-source-task.md"
        text = flow_page.read_text(encoding="utf-8")
        assert "# source-task" in text
        assert "```mermaid\nflowchart RL" in text

    def test_plugin_detector_failure_warns_in_text_output(
        self, tmp_path, monkeypatch, capsys
    ):
        _write_entrypoint_detector_plugin(
            tmp_path,
            body="""
            def detect(inventory):
                raise RuntimeError("bootstrap detector failed")
            """,
        )
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))

        out = capsys.readouterr().out
        assert "Warning:" in out
        assert "bootstrap detector failed" in out
        assert (tmp_path / "wiki" / "flows" / "api-run.md").exists()

    def test_json_summary_includes_plugin_detector_warnings(
        self, tmp_path, monkeypatch, capsys
    ):
        _write_entrypoint_detector_plugin(
            tmp_path,
            body="""
            def detect(inventory):
                raise RuntimeError("json detector failed")
            """,
        )
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(
            _make_args(src_dir=".", wiki_dir="wiki", format="json", source_adapter=True)
        )

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data["warnings"]) == 1
        assert "json detector failed" in data["warnings"][0]
        assert "Warning:" in captured.err
        assert "json detector failed" in captured.err

    def test_generates_flow_page_without_data_flow_when_skipped(
        self, tmp_path, monkeypatch, capsys
    ):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki", skip_data_flow=True))
        flow_page = tmp_path / "wiki" / "flows" / "api-run.md"
        assert flow_page.exists()
        text = flow_page.read_text(encoding="utf-8")
        assert "## Call sequence" in text
        assert "## Data flow" not in text
        assert "## Behavior" in text
        knowledge = json.loads(
            (tmp_path / "wiki" / ".llm-wiki-knowledge.json").read_text(
                encoding="utf-8"
            )
        )
        coverage = {
            item["analyzer"]: item
            for item in knowledge["extensions"]["llm-wiki/typed-graph-v1"][
                "coverage"
            ]
        }
        assert "data-flow-analysis-disabled" in coverage["data-flows"][
            "limitations"
        ]
        assert coverage["flows"]["observed"] >= coverage["flows"]["emitted"]

    def test_index_lists_entry_point_flows(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))
        index = (tmp_path / "wiki" / "index.md").read_text(encoding="utf-8")
        assert "## Entry-point flows" in index
        assert "[api-run](flows/api-run.md)" in index

    def test_surface_index_counts_user_flows_and_dependencies(
        self, tmp_path, monkeypatch, capsys
    ):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))

        data = json.loads(
            (tmp_path / "wiki" / SURFACE_INDEX_FILENAME).read_text(encoding="utf-8")
        )
        assert data["counts"]["by_kind"]["flows"] == 1
        assert data["counts"]["dependency_architecture"] == 2
        assert data["flows"] == [
            {
                "id": "api-run",
                "category": "api",
                "detector": "builtin",
                "entry_point": {
                    "symbol": "run",
                    "source_path": "api.py",
                    "label": "run",
                },
                "evidence": {
                    "flow": {
                        "step_count": 2,
                        "truncated": False,
                        "modules_touched": ["api.py"],
                    },
                    "data_flow": {
                        "generated": True,
                        "step_count": 2,
                        "transfer_count": 1,
                        "truncated": False,
                        "boundary_effects": [],
                        "gaps": [],
                    },
                },
                "language": "python",
            }
        ]

    def test_flow_generation_reuses_single_data_flow_context(
        self, tmp_path, monkeypatch, capsys
    ):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        calls = 0
        real_build_context = bootstrap_cmd.build_data_flow_context

        def counted_build_context(*args, **kwargs):
            nonlocal calls
            calls += 1
            return real_build_context(*args, **kwargs)

        monkeypatch.setattr(
            bootstrap_cmd, "build_data_flow_context", counted_build_context
        )

        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))

        assert calls == 1
        assert (tmp_path / "wiki" / "flows" / "api-run.md").exists()

    def test_runtime_plan_receives_graph_analyzer_observations(
        self, tmp_path, monkeypatch, capsys
    ):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "sample"\nversion = "0.1.0"\n'
            'dependencies = ["requests"]\n',
            encoding="utf-8",
        )
        constants = "\n".join(f"CONFIG_{index} = {index}" for index in range(20))
        reads = ", ".join(f"CONFIG_{index}" for index in range(20))
        (tmp_path / "api.py").write_text(
            "import requests\n\n"
            f"{constants}\n\n"
            '__all__ = ["run"]\n\n'
            "def run():\n"
            f"    values = ({reads})\n"
            '    requests.get("https://example.invalid")\n'
            "    return helper()\n\n"
            "def helper():\n"
            "    return 1\n",
            encoding="utf-8",
        )
        captured = []
        detailed_results = []
        real_build_plan = knowledge_orchestration.build_runtime_knowledge_plan
        real_analyze = bootstrap_cmd.analyze_data_flow_detailed

        def capture_plan(inputs):
            captured.append(inputs)
            return real_build_plan(inputs)

        def capture_data_flow(*args, **kwargs):
            result = real_analyze(*args, **kwargs)
            detailed_results.append(result)
            return result

        monkeypatch.setattr(
            knowledge_orchestration,
            "build_runtime_knowledge_plan",
            capture_plan,
        )
        monkeypatch.setattr(
            bootstrap_cmd,
            "analyze_data_flow_detailed",
            capture_data_flow,
        )
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))

        assert len(captured) == 1
        runtime = captured[0]
        assert runtime.call_edges["schema_version"] == "llm-wiki-call-observations/v1"
        assert runtime.call_edges["observations"]
        assert runtime.dependency_observations["observations"]
        assert next(
            observation
            for observation in runtime.dependency_observations["observations"]
            if observation["module"] == "requests"
        )["line"] == 1
        assert runtime.entrypoint_observations["observations"][0]["detector"][
            "id"
        ].startswith("builtin.")
        assert runtime.flows[0]["entry"]["id"] == "api-run"
        assert runtime.flows[0]["schema_version"] == "llm-wiki-flow-observations/v1"
        assert runtime.data_flows[0] is detailed_results[0]
        assert runtime.data_flows[0]["schema_version"].endswith("/v1")
        reads_coverage = runtime.data_flows[0]["coverage"]["effects"]["by_kind"][
            "reads"
        ]
        assert reads_coverage["observed"] == 20
        assert reads_coverage["emitted"] == 8
        assert reads_coverage["omitted"] == 12
        assert any(
            dependency["package"] == "requests" and dependency["explicit"]
            for dependency in runtime.external_dependencies
        )

    def test_runtime_keeps_call_observations_without_entrypoints(
        self, tmp_path, monkeypatch, capsys
    ):
        (tmp_path / "module.py").write_text(
            "def caller():\n    return helper()\n\n\ndef helper():\n    return 1\n",
            encoding="utf-8",
        )
        captured = []
        real_build_plan = knowledge_orchestration.build_runtime_knowledge_plan

        def capture_plan(inputs):
            captured.append(inputs)
            return real_build_plan(inputs)

        monkeypatch.setattr(
            knowledge_orchestration,
            "build_runtime_knowledge_plan",
            capture_plan,
        )
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))

        runtime = captured[0]
        assert runtime.entrypoint_observations["observations"] == []
        assert runtime.flows == []
        assert runtime.call_edges["coverage"]["observed"] == 1
        assert runtime.call_edges["observations"][0]["kind"] == "internal"

    def test_skip_flows_writes_no_flow_pages(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki", skip_flows=True))
        assert list((tmp_path / "wiki" / "flows").glob("*.md")) == []
        index = (tmp_path / "wiki" / "index.md").read_text(encoding="utf-8")
        assert "| Entry-point flows | 0 |" in index
        assert "[api-run](flows/api-run.md)" not in index

    def test_skip_flows_takes_precedence_over_skip_data_flow(
        self, tmp_path, monkeypatch, capsys
    ):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(
            _make_args(
                src_dir=".",
                wiki_dir="wiki",
                skip_flows=True,
                skip_data_flow=True,
            )
        )
        assert list((tmp_path / "wiki" / "flows").glob("*.md")) == []

    def test_json_summary_counts_flows(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(
            _make_args(src_dir=".", wiki_dir="wiki", format="json", source_adapter=True)
        )
        data = json.loads(capsys.readouterr().out)
        assert data["flows"] == 1
        assert data["flow_evidence"][0]["detector"] == "builtin"
        assert data["flow_evidence"][0]["evidence"]["flow"]["step_count"] == 2

    def test_json_summary_reports_data_flow_counts(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(
            _make_args(src_dir=".", wiki_dir="wiki", format="json", source_adapter=True)
        )
        data = json.loads(capsys.readouterr().out)
        assert data["data_flows"] == {
            "generated": True,
            "analyzed": 1,
            "boundary_effects": 0,
            "gaps": 0,
        }

    def test_json_summary_reports_skipped_data_flow(
        self, tmp_path, monkeypatch, capsys
    ):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(
            _make_args(
                src_dir=".",
                wiki_dir="wiki",
                format="json",
                source_adapter=True,
                skip_data_flow=True,
            )
        )
        data = json.loads(capsys.readouterr().out)
        assert data["flows"] == 1
        assert data["data_flows"] == {
            "generated": False,
            "analyzed": 0,
            "boundary_effects": 0,
            "gaps": 0,
        }


def _pymod(*imports, functions=None, module_calls=None):
    """A minimal deep-inventory Python entry for dependency analysis."""
    entry = {
        "language": "python",
        "imports": [{"module": m, "name": n} for m, n in imports],
        "classes": [],
        "functions": [{"name": f} for f in (functions or [])],
    }
    if module_calls:
        entry["module_calls"] = module_calls
    return entry


class TestGenerateDependenciesMd:
    def _analysis(self, tmp_path):
        inventory = {
            "pkg/a.py": _pymod(("pkg.b", "B"), ("requests", "get")),
            "pkg/b.py": _pymod(("pkg.a", "A")),
        }
        analysis = analyze_dependencies(inventory, str(tmp_path))
        return analysis, {"pkg/a.py": "a", "pkg/b.py": "b"}

    def test_renders_graph_cycles_metrics_and_external(self, tmp_path):
        analysis, page_map = self._analysis(tmp_path)
        md = bootstrap_cmd._generate_dependencies_md(analysis, page_map)
        assert md.startswith("# Dependencies")
        assert "```mermaid" in md and "flowchart TD" in md
        assert 'click n0 "modules/a.md"' in md  # node hyperlinks to its page
        assert "==>" in md  # the a⇄b cycle edges are highlighted
        assert "## Cycles" in md
        assert "[a](modules/a.md) ⇄ [b](modules/b.md)" in md
        assert "## Fan-in / Fan-out" in md
        assert "| [a](modules/a.md) |" in md
        assert "### python" in md
        assert "⚠️ **Undeclared:** `requests`" in md
        assert md.rstrip().endswith(
            "Dynamic or conditional imports and runtime-loaded integrations may "
            "not appear in the generated sections."
        )
        assert "## Notes" in md
        assert "placeholder" not in md.casefold()

        nodes = [f"pkg/m{index}.py" for index in range(12)]
        edges = [
            (source, target)
            for source in nodes
            for target in nodes
            if source != target
        ][:60]
        dense_analysis = {
            "graph": {"nodes": nodes, "edges": edges},
            "cycles": [[nodes[0], nodes[1]]],
            "metrics": {
                "metrics": {
                    node: {
                        "fan_in": sum(target == node for _source, target in edges),
                        "fan_out": sum(source == node for source, _target in edges),
                    }
                    for node in nodes
                },
                "most_depended_on": nodes,
            },
            "reconciliation": {"languages": {}},
        }
        dense_page_map = {
            node: Path(node).stem for node in dense_analysis["graph"]["nodes"]
        }
        rendered = bootstrap_cmd._render_dependency_graph_result(
            dense_analysis,
            dense_page_map,
            "module",
            {},
        )
        repeated = bootstrap_cmd._render_dependency_graph_result(
            dense_analysis,
            dense_page_map,
            "module",
            {},
        )

        assert rendered == repeated
        assert rendered.diagram is not None
        assert (
            rendered.total_edges,
            rendered.shown_edges,
            rendered.omitted_edges,
        ) == (60, 55, 5)
        aliases = {node: f"n{index}" for index, node in enumerate(nodes)}
        assert (
            f"    {aliases[nodes[0]]} ==> {aliases[nodes[1]]}"
            in rendered.diagram
        )
        assert (
            f"    {aliases[nodes[1]]} ==> {aliases[nodes[0]]}"
            in rendered.diagram
        )
        rendered_edges = [
            line
            for line in rendered.diagram.splitlines()
            if " --> " in line or " ==> " in line
        ]
        assert rendered_edges[:2] == [
            f"    {aliases[nodes[0]]} ==> {aliases[nodes[1]]}",
            f"    {aliases[nodes[1]]} ==> {aliases[nodes[0]]}",
        ]

        dense_md = bootstrap_cmd._generate_dependencies_md(
            dense_analysis,
            dense_page_map,
            detail="module",
            diagram_style={},
        )
        assert (
            "Dependency diagram shows 55 of 60 module dependency edges; "
            "5 omitted"
        ) in dense_md
        assert "| [m11](modules/m11.md) |" in dense_md
        _assert_generated_diagram_budgets(dense_md)

    def test_degrades_cleanly_without_cycles_or_external(self, tmp_path):
        inventory = {"solo.py": _pymod()}
        analysis = analyze_dependencies(inventory, str(tmp_path))
        md = bootstrap_cmd._generate_dependencies_md(analysis, {"solo.py": "solo"})
        assert "*No import cycles detected.*" in md
        assert "*No external dependencies detected.*" in md

    def test_package_detail_collapses_and_drops_links(self, tmp_path):
        analysis, page_map = self._analysis(tmp_path)
        md = bootstrap_cmd._generate_dependencies_md(
            analysis, page_map, detail="package"
        )
        assert "Collapsed to top-level packages" in md
        assert 'n0["pkg"]' in md
        assert "click" not in md  # package nodes are not per-module links

    def test_is_deterministic(self, tmp_path):
        analysis, page_map = self._analysis(tmp_path)
        assert bootstrap_cmd._generate_dependencies_md(
            analysis, page_map
        ) == bootstrap_cmd._generate_dependencies_md(analysis, page_map)


class TestGenerateLoadOrderMd:
    def test_renders_order_side_effects_and_factories(self, tmp_path):
        inventory = {
            "pkg/a.py": _pymod(
                ("pkg.b", "B"),
                functions=["create_app"],
                module_calls=[{"name": "Flask", "target": "app", "line": 1}],
            ),
            "pkg/b.py": _pymod(),
        }
        analysis = analyze_dependencies(inventory, str(tmp_path))
        md = bootstrap_cmd._generate_load_order_md(
            analysis, {"pkg/a.py": "a", "pkg/b.py": "b"}
        )
        assert md.startswith("# Load order")
        # b loads before a because a imports b
        assert md.index("[b](modules/b.md)") < md.index("[a](modules/a.md)")
        assert "## Module-level side effects" in md
        assert "`app = Flask`" in md
        assert "## Factory / wiring" in md
        assert "`create_app`" in md
        assert "## Notes" in md
        assert "This page presents a static dependency projection." in md
        assert "placeholder" not in md.casefold()

    def test_cyclic_group_marked_indeterminate(self, tmp_path):
        inventory = {"a.py": _pymod(("b", "x")), "b.py": _pymod(("a", "y"))}
        analysis = analyze_dependencies(inventory, str(tmp_path))
        md = bootstrap_cmd._generate_load_order_md(analysis, {"a.py": "a", "b.py": "b"})
        assert "Indeterminate (cyclic) groups" in md
        assert "[a](modules/a.md) ⇄ [b](modules/b.md)" in md

    def test_empty_sections_use_placeholders(self, tmp_path):
        analysis = analyze_dependencies({"solo.py": _pymod()}, str(tmp_path))
        md = bootstrap_cmd._generate_load_order_md(analysis, {"solo.py": "solo"})
        assert "*No import-time side effects detected.*" in md
        assert "*No factory or wiring functions detected.*" in md
        assert "Indeterminate (cyclic) groups" not in md

    def test_language_entry_without_imports_is_rendered_in_load_order(self, tmp_path):
        inventory = {
            "bundle/main.js": {
                "language": "javascript",
                "module_calls": [
                    {"name": "require", "target": "import_obsidian", "line": 1}
                ],
            },
            "metadata": {},
        }
        analysis = analyze_dependencies(inventory, str(tmp_path))

        md = bootstrap_cmd._generate_load_order_md(
            analysis,
            {"bundle/main.js": "bundle_main"},
        )

        assert "1. [bundle_main](modules/bundle_main.md)" in md
        assert "[metadata]" not in md
        assert "[bundle_main](modules/bundle_main.md) | `import_obsidian = require`" in md


class TestBootstrapArchitecturePages:
    def _write_project(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "s"\nversion = "0.1.0"\ndependencies = ["requests"]\n'
        )
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "a.py").write_text(
            "from pkg.b import work\nimport requests\n\n\ndef run():\n"
            "    return work()\n"
        )
        (pkg / "b.py").write_text("app = object()\n\n\ndef work():\n    return 1\n")

    def test_creates_both_pages_with_valid_mermaid(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))
        deps = (tmp_path / "wiki" / "dependencies.md").read_text(encoding="utf-8")
        load = (tmp_path / "wiki" / "load-order.md").read_text(encoding="utf-8")
        assert "```mermaid" in deps
        assert "## Load order" in load

    def test_index_has_architecture_section(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))
        index = (tmp_path / "wiki" / "index.md").read_text(encoding="utf-8")
        assert "| Dependency architecture | 2 |" in index
        assert "## Dependency Architecture" in index
        assert "[Dependencies](dependencies.md)" in index
        assert "[Load order](load-order.md)" in index

    def test_skip_dependencies_omits_pages_and_section(
        self, tmp_path, monkeypatch, capsys
    ):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(
            _make_args(src_dir=".", wiki_dir="wiki", skip_dependencies=True)
        )
        assert not (tmp_path / "wiki" / "dependencies.md").exists()
        assert not (tmp_path / "wiki" / "load-order.md").exists()
        module = (tmp_path / "wiki" / "modules" / "a.md").read_text(encoding="utf-8")
        assert "## Local dependency map" not in module
        index = (tmp_path / "wiki" / "index.md").read_text(encoding="utf-8")
        assert "| Dependency architecture | 0 |" in index
        assert "## Dependency Architecture" not in index

    def test_shallow_depth_skips_pages(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki", depth="shallow"))
        assert not (tmp_path / "wiki" / "dependencies.md").exists()
        knowledge = json.loads(
            (tmp_path / "wiki" / ".llm-wiki-knowledge.json").read_text(
                encoding="utf-8"
            )
        )
        coverage = {
            item["analyzer"]: item
            for item in knowledge["extensions"]["llm-wiki/typed-graph-v1"][
                "coverage"
            ]
        }
        for analyzer in (
            "calls",
            "dependencies",
            "entrypoints",
            "flows",
            "data-flows",
            "external-dependencies",
        ):
            assert "deep-analysis-disabled" in coverage[analyzer]["limitations"]

    def test_deep_bootstrap_documents_isolated_language_module_dependencies(
        self, tmp_path, monkeypatch, capsys
    ):
        (tmp_path / "service.js").write_text(
            "function run() { return 1; }\nmodule.exports = { run };\n",
            encoding="utf-8",
        )
        result = InventoryResult(
            {
                "service.js": {
                    "language": "javascript",
                    "classes": [],
                    "functions": [{"name": "run", "line": 1}],
                }
            },
            {"typescript": ExtractorStatus("typescript", "ok", 1)},
        )
        monkeypatch.setattr(
            bootstrap_cmd, "get_inventory_result", lambda *a, **k: result
        )
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))

        dependencies = (tmp_path / "wiki" / "dependencies.md").read_text(
            encoding="utf-8"
        )
        load_order = (tmp_path / "wiki" / "load-order.md").read_text(
            encoding="utf-8"
        )
        module = (tmp_path / "wiki" / "modules" / "service.md").read_text(
            encoding="utf-8"
        )
        index = (tmp_path / "wiki" / "index.md").read_text(encoding="utf-8")
        assert "| [service](modules/service.md) | 0 | 0 |" in dependencies
        assert "1. [service](modules/service.md)" in load_order
        assert "## Local dependency map" in module
        assert "*No internal module dependencies detected.*" in module
        assert "## Dependency Architecture" in index

    def test_json_summary_reports_dependencies(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(
            _make_args(src_dir=".", wiki_dir="wiki", format="json", source_adapter=True)
        )
        data = json.loads(capsys.readouterr().out)
        assert data["dependencies"]["generated"] is True
        assert data["dependencies"]["modules"] >= 2
        assert data["dependencies"]["undeclared"] == 0  # requests is declared
        assert data["dependency_evidence"]["metrics"]

    def test_dependency_graph_detail_package_collapses(
        self, tmp_path, monkeypatch, capsys
    ):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(
            _make_args(src_dir=".", wiki_dir="wiki", dependency_graph_detail="package")
        )
        deps = (tmp_path / "wiki" / "dependencies.md").read_text(encoding="utf-8")
        assert "Collapsed to top-level packages" in deps

    def test_auto_dependency_graph_detail_collapses_large_inventory(self, tmp_path):
        inventory = {
            f"pkg{pkg}/mod{index}.py": _pymod(
                (f"pkg{(pkg + 1) % 5}.mod{index}", "work")
            )
            for pkg in range(5)
            for index in range(40)
        }
        analysis = analyze_dependencies(inventory, str(tmp_path))
        page_map = {
            path: path.replace("/", "_").removesuffix(".py") for path in inventory
        }

        md = bootstrap_cmd._generate_dependencies_md(analysis, page_map, detail="auto")
        repeat = bootstrap_cmd._generate_dependencies_md(
            analysis, page_map, detail="auto"
        )

        assert md == repeat
        assert "Collapsed to top-level packages" in md
        assert "```mermaid" in md
        assert "pkg0" in md
        assert "pkg4" in md
        assert "click " not in md
        assert "| [pkg0_mod0](modules/pkg0_mod0.md) |" in md
        assert "| [pkg4_mod39](modules/pkg4_mod39.md) |" in md
        assert md.count("    ") < 30
        _assert_generated_diagram_budgets(md)

        explicit_module = bootstrap_cmd._generate_dependencies_md(
            analysis,
            page_map,
            detail="module",
        )
        assert "```mermaid" not in explicit_module
        assert "Dependency diagram shows 0 of" in explicit_module
        assert "module dependency edges" in explicit_module
        assert "fixed nodes, links, or style exceed" in explicit_module
        assert "| [pkg0_mod0](modules/pkg0_mod0.md) |" in explicit_module
        assert "| [pkg4_mod39](modules/pkg4_mod39.md) |" in explicit_module
        assert "Collapsed to top-level packages" not in explicit_module

    def test_dependency_pages_and_module_maps_reuse_single_dependency_analysis(
        self, tmp_path, monkeypatch, capsys
    ):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        calls = 0
        real_analyze_dependencies = bootstrap_cmd.analyze_dependencies

        def counted_analyze_dependencies(*args, **kwargs):
            nonlocal calls
            calls += 1
            return real_analyze_dependencies(*args, **kwargs)

        monkeypatch.setattr(
            bootstrap_cmd, "analyze_dependencies", counted_analyze_dependencies
        )

        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))

        assert calls == 1
        assert (tmp_path / "wiki" / "modules" / "a.md").exists()
        assert (tmp_path / "wiki" / "dependencies.md").exists()
        assert (tmp_path / "wiki" / "load-order.md").exists()
