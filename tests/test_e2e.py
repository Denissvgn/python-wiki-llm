"""End-to-end integration test for the full llm-wiki lifecycle.

Covers: init → bootstrap → lint → extract → bump → uninstall
Does NOT test trigger-agent (requires a real LLM agent).
"""
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
    subprocess.run(["git", "-C", str(proj), "config", "user.email", "e2e@test.com"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(proj), "config", "user.name", "E2E"], capture_output=True, check=True)

    (proj / "models.py").write_text(textwrap.dedent("""\
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
    """))

    (proj / "api.py").write_text(textwrap.dedent("""\
        from models import User, Team

        def get_user(user_id: int) -> User:
            \"\"\"Fetch a user by ID.\"\"\"
            return User(name="test", email="t@t.com")

        def create_team(name: str, owner: User) -> Team:
            \"\"\"Create a new team.\"\"\"
            return Team(name=name, members=[owner])
    """))

    (proj / "pyproject.toml").write_text(textwrap.dedent("""\
        [project]
        name = "myapp"
        version = "0.1.0"
    """))

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
        bootstrap_cmd.run(_ns(
            src_dir=".", wiki_dir=wiki_dir,
            overwrite=False, depth="full", skip_workflows=True,
        ))

        assert Path(f"{wiki_dir}/entities/User.md").exists()
        assert Path(f"{wiki_dir}/entities/Team.md").exists()
        assert Path(f"{wiki_dir}/modules/models.md").exists()
        assert Path(f"{wiki_dir}/modules/api.md").exists()

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

        # ── 5. Add new code, detect drift ────────────────────────────
        Path("billing.py").write_text(textwrap.dedent("""\
            class Invoice:
                \"\"\"A billing invoice.\"\"\"
                amount: float
                paid: bool = False
        """))

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
        uninstall_cmd.run(_ns(
            wiki_dir=wiki_dir, remove_wiki=False, dry_run=True,
        ))
        out = capsys.readouterr().out
        assert "DRY RUN" in out
        # Everything still exists
        assert Path(wiki_dir).exists()
        assert Path("CLAUDE.md").exists()

        # ── 8. Uninstall (real) ──────────────────────────────────────
        monkeypatch.setattr("builtins.input", lambda _: "y")
        uninstall_cmd.run(_ns(
            wiki_dir=wiki_dir, remove_wiki=True, dry_run=False,
        ))

        assert not Path(wiki_dir).exists()
        # CLAUDE.md may still exist (preamble content) but wiki block should be gone
        if Path("CLAUDE.md").exists():
            assert "LLM Wiki Maintainer Constraints" not in Path("CLAUDE.md").read_text(encoding="utf-8")
