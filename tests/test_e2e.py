"""End-to-end integration test for the full llm-wiki lifecycle.

Covers: init → bootstrap → lint → extract → bump → uninstall
Does NOT test trigger-agent (requires a real LLM agent).
"""

import json
import os
import subprocess
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import (
    init_cmd,
    bootstrap_cmd,
    lint_cmd,
    extract_cmd,
    bump_cmd,
    uninstall_cmd,
)


def _ns(**kwargs):
    return types.SimpleNamespace(**kwargs)


@pytest.fixture
def e2e_project(tmp_path):
    """Full project with git, sample code, and pyproject.toml."""
    proj = tmp_path / "myapp"
    proj.mkdir()

    subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(proj), "config", "user.email", "e2e@test.com"],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(proj), "config", "user.name", "E2E"],
        capture_output=True,
        check=True,
    )

    (proj / "models.py").write_text(
        textwrap.dedent("""\
        from pydantic import BaseModel

        class User(BaseModel):
            \"\"\"A user account.\"\"\"
            name: str
            email: str
            active: bool = True

        class Team(BaseModel):
            \"\"\"A group of users.\"\"\"
            name: str
            members: list[User] = []
    """)
    )

    (proj / "api.py").write_text(
        textwrap.dedent("""\
        from models import User, Team

        def get_user(user_id: int) -> User:
            \"\"\"Fetch a user by ID.\"\"\"
            return User(name="test", email="t@t.com")

        def create_team(name: str, owner: User) -> Team:
            \"\"\"Create a new team.\"\"\"
            return Team(name=name, members=[owner])
    """)
    )

    (proj / "pyproject.toml").write_text(
        textwrap.dedent("""\
        [project]
        name = "myapp"
        version = "0.1.0"
    """)
    )

    old_cwd = os.getcwd()
    os.chdir(proj)
    yield proj
    os.chdir(old_cwd)


class TestE2ELifecycle:
    def test_full_lifecycle(self, e2e_project, capsys, monkeypatch):
        wiki_dir = "docs/llm_wiki"

        # ── 1. Init ──────────────────────────────────────────────────
        init_cmd.run(_ns(agent="claude"))

        assert Path(wiki_dir).exists()
        assert Path(f"{wiki_dir}/index.md").exists()
        assert Path(f"{wiki_dir}/log.md").exists()
        assert Path(f"{wiki_dir}/entities").is_dir()
        assert Path(f"{wiki_dir}/modules").is_dir()
        assert Path(f"{wiki_dir}/workflows").is_dir()
        assert Path("CLAUDE.md").exists()
        assert "LLM Wiki" in Path("CLAUDE.md").read_text(encoding="utf-8")

        # ── 2. Bootstrap ─────────────────────────────────────────────
        bootstrap_cmd.run(
            _ns(
                src_dir=".",
                wiki_dir=wiki_dir,
                overwrite=False,
                depth="full",
                skip_workflows=True,
            )
        )

        assert Path(f"{wiki_dir}/entities/User.md").exists()
        assert Path(f"{wiki_dir}/entities/Team.md").exists()
        assert Path(f"{wiki_dir}/modules/models.md").exists()
        assert Path(f"{wiki_dir}/modules/api.md").exists()

        # Knowledge is an additive sidecar: canonical page identity and MCP
        # resource addresses remain defined by surface-index v1.
        assert Path(f"{wiki_dir}/.llm-wiki-knowledge.json").exists()
        surface = json.loads(
            Path(f"{wiki_dir}/.llm-wiki-surface.json").read_text(encoding="utf-8")
        )
        assert surface["schema_version"] == "llm-wiki-surface-index/v1"
        by_path = {page["canonical_path"]: page for page in surface["pages"]}
        assert (
            by_path["entities/User.md"]["id"],
            by_path["entities/User.md"]["mcp_uri"],
        ) == ("User", "llm-wiki://entities/User")
        assert (
            by_path["modules/models.md"]["id"],
            by_path["modules/models.md"]["mcp_uri"],
        ) == ("models", "llm-wiki://modules/models")

        # Index should link all entities and modules
        index = Path(f"{wiki_dir}/index.md").read_text(encoding="utf-8")
        assert "User" in index
        assert "Team" in index
        assert "models" in index
        assert "api" in index

        # Log should have bootstrap entry
        log = Path(f"{wiki_dir}/log.md").read_text(encoding="utf-8")
        assert "bootstrap" in log.lower()

        # ── 3. Lint (should pass — wiki is consistent) ───────────────
        lint_cmd.run(_ns(wiki_dir=wiki_dir, src_dir="."))
        out = capsys.readouterr().out
        assert "No broken links" in out

        # ── 4. Extract ───────────────────────────────────────────────
        inventory = extract_cmd.get_inventory(".", deep=True)
        class_names = set()
        for data in inventory.values():
            for cls in data.get("classes", []):
                class_names.add(cls["name"])
        assert "User" in class_names
        assert "Team" in class_names

        extract_payload = extract_cmd.build_extract_payload(".", deep=True).payload
        assert "python" in extract_payload["dependencies"]["external"]

        # ── 5. Add new code, detect drift ────────────────────────────
        Path("billing.py").write_text(
            textwrap.dedent("""\
            class Invoice:
                \"\"\"A billing invoice.\"\"\"
                amount: float
                paid: bool = False
        """)
        )

        # Lint should now detect undocumented class + module
        with pytest.raises(SystemExit) as exc_info:
            lint_cmd.run(_ns(wiki_dir=wiki_dir, src_dir="."))
        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert "Undocumented class" in out or "Undocumented module" in out

        # ── 6. Bump version ──────────────────────────────────────────
        bump_cmd.run(_ns(bump_type="patch", root=".", stage=False))
        out = capsys.readouterr().out
        assert "0.1.0 -> 0.1.1" in out

        content = Path("pyproject.toml").read_text(encoding="utf-8")
        assert "0.1.1" in content

        # Bump minor
        bump_cmd.run(_ns(bump_type="minor", root=".", stage=False))
        out = capsys.readouterr().out
        assert "0.1.1 -> 0.2.0" in out

        # ── 7. Uninstall (dry run) ───────────────────────────────────
        uninstall_cmd.run(
            _ns(
                wiki_dir=wiki_dir,
                remove_wiki=False,
                dry_run=True,
            )
        )
        out = capsys.readouterr().out
        assert "DRY RUN" in out
        # Everything still exists
        assert Path(wiki_dir).exists()
        assert Path("CLAUDE.md").exists()

        # ── 8. Uninstall (real) ──────────────────────────────────────
        monkeypatch.setattr("builtins.input", lambda _: "y")
        uninstall_cmd.run(
            _ns(
                wiki_dir=wiki_dir,
                remove_wiki=True,
                dry_run=False,
            )
        )

        assert not Path(wiki_dir).exists()
        # CLAUDE.md may still exist (preamble content) but wiki block should be gone
        if Path("CLAUDE.md").exists():
            assert "LLM Wiki Maintainer Constraints" not in Path("CLAUDE.md").read_text(
                encoding="utf-8"
            )


class TestE2EFlows:
    def test_bootstrap_then_strict_lint_is_clean_with_flows(
        self, tmp_path, monkeypatch
    ):
        proj = tmp_path / "flowapp"
        proj.mkdir()
        subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
        (proj / "pyproject.toml").write_text(
            textwrap.dedent("""\
            [project]
            name = "flowapp"
            version = "0.1.0"

            [project.scripts]
            flowapp = "service:main"
        """)
        )
        (proj / "service.py").write_text(
            textwrap.dedent("""\
            __all__ = ["process"]


            def process(payload, output_path, client):
                result = _normalize(payload)
                output_path.write_text(str(result))
                client.publish(result)
                return result


            def _normalize(payload):
                return payload


            def main():
                return process({}, "out.txt", object())


            if __name__ == "__main__":
                main()
        """)
        )
        monkeypatch.chdir(proj)

        bootstrap_cmd.run(
            _ns(
                src_dir=".",
                wiki_dir="docs/llm_wiki",
                overwrite=False,
                depth="full",
                skip_workflows=True,
            )
        )

        flows_dir = proj / "docs" / "llm_wiki" / "flows"
        flow_pages = {p.stem for p in flows_dir.glob("*.md")}
        assert "api-process" in flow_pages
        assert "process-flowapp" in flow_pages

        api_flow = (flows_dir / "api-process.md").read_text(encoding="utf-8")
        assert "```mermaid" in api_flow
        assert "_normalize" in api_flow  # resolved internal call appears in the diagram
        assert "## Call sequence" in api_flow
        assert "## Data flow" in api_flow
        assert "flowchart LR" in api_flow
        assert "| filesystem_write | `output_path.write_text` | `process` |" in api_flow
        assert "client.publish" in api_flow
        assert "## Behavior" in api_flow

        index = (proj / "docs" / "llm_wiki" / "index.md").read_text(encoding="utf-8")
        assert "## User Flows" in index
        assert "[api-process](flows/api-process.md)" in index

        # Strict lint on the freshly bootstrapped wiki passes with zero issues.
        report = lint_cmd.build_report("docs/llm_wiki", ".", strict=True)
        assert report.passed, [issue.message for issue in report.issues]
        assert any(
            diagnostic.category == "data_flow_gaps"
            and "client.publish" in diagnostic.message
            for diagnostic in report.diagnostics
        )


class TestE2EDependencyArchitecture:
    def test_bootstrap_lint_and_extract_cover_dependency_architecture(
        self, tmp_path, monkeypatch, capsys
    ):
        proj = tmp_path / "dependencyapp"
        proj.mkdir()
        (proj / "pyproject.toml").write_text(
            textwrap.dedent("""\
            [project]
            name = "dependencyapp"
            version = "0.1.0"
            """),
            encoding="utf-8",
        )
        (proj / "alpha.py").write_text(
            textwrap.dedent("""\
            import beta
            import httpx


            def create_app():
                return {"client": httpx.Client, "worker": beta.run}


            app = create_app()
            """),
            encoding="utf-8",
        )
        (proj / "beta.py").write_text(
            textwrap.dedent("""\
            from alpha import app


            def run():
                return app
            """),
            encoding="utf-8",
        )
        monkeypatch.chdir(proj)

        wiki_dir = "docs/llm_wiki"
        bootstrap_cmd.run(
            _ns(
                src_dir=".",
                wiki_dir=wiki_dir,
                overwrite=False,
                depth="full",
                skip_workflows=True,
            )
        )

        deps = Path(f"{wiki_dir}/dependencies.md").read_text(encoding="utf-8")
        load_order = Path(f"{wiki_dir}/load-order.md").read_text(encoding="utf-8")
        index = Path(f"{wiki_dir}/index.md").read_text(encoding="utf-8")

        assert "```mermaid" in deps
        assert "flowchart TD" in deps
        assert "[alpha](modules/alpha.md) ⇄ [beta](modules/beta.md)" in deps
        assert "⚠️ **Undeclared:** `httpx`" in deps

        assert "## Module-level side effects" in load_order
        assert "`app = create_app`" in load_order
        assert "## Indeterminate (cyclic) groups" in load_order
        assert "[alpha](modules/alpha.md) ⇄ [beta](modules/beta.md)" in load_order

        assert "## Dependency Architecture" in index
        assert "[Dependencies](dependencies.md)" in index
        assert "[Load order](load-order.md)" in index

        report = lint_cmd.build_report(wiki_dir, ".", strict=True)
        assert report.passed, [issue.message for issue in report.issues]
        assert report.issues == []
        dependency_diagnostics = {
            diagnostic.category: diagnostic for diagnostic in report.diagnostics
        }
        assert "dependency_cycles" in dependency_diagnostics
        assert "undeclared_dependencies" in dependency_diagnostics
        assert dependency_diagnostics["undeclared_dependencies"].target == "httpx"
        assert all(
            diagnostic.severity == "warning"
            for diagnostic in report.diagnostics
            if diagnostic.category
            in {"dependency_cycles", "undeclared_dependencies", "unused_dependencies"}
        )

        lint_cmd.run(_ns(wiki_dir=wiki_dir, src_dir=".", strict=True))
        out = capsys.readouterr().out
        assert "Import cycle: alpha.py ⇄ beta.py" in out
        assert "Undeclared python dependency (imported, not declared): httpx" in out
        assert "✅ Lint passed: wiki is fully consistent." in out

        extract_payload = extract_cmd.build_extract_payload(".", deep=True).payload
        python_external = extract_payload["dependencies"]["external"]["python"]
        assert set(python_external) == {"used", "undeclared", "unused"}
        assert python_external["used"]["httpx"] == ["alpha.py"]
        assert python_external["undeclared"] == ["httpx"]
