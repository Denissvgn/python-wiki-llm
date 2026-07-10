"""Shared fixtures for llm_wiki_cli tests."""

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import textwrap

import pytest

# True when git is on PATH; used to skip/stub git-dependent steps
_GIT_AVAILABLE = shutil.which("git") is not None


@dataclass(frozen=True)
class NavigationWikiLayout:
    """Fixture contract for legacy/current wiki navigation smoke tests."""

    name: str
    src_dir: Path
    wiki_dir: Path
    inventory: dict
    docker_inventory: dict
    expected_counts: dict[str, int]
    expected_uris: set[str]
    absent_uris: set[str]
    expected_mirror_paths: set[str]
    absent_mirror_paths: set[str]


def _write_navigation_page(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")


def _navigation_inventory() -> dict:
    return {
        "models.py": {
            "language": "python",
            "module_docstring": "Navigation fixture module.",
            "classes": [{"name": "User", "line": 1}],
            "functions": [{"name": "run", "line": 5}],
            "all_exports": ["run"],
        }
    }


def _write_legacy_navigation_wiki(root: Path) -> NavigationWikiLayout:
    src_dir = root / "legacy_project"
    wiki = src_dir / "docs" / "llm_wiki"
    src_dir.mkdir(parents=True)
    _write_navigation_page(
        src_dir / "models.py",
        """
        class User:
            pass

        def run():
            return User()
        """,
    )
    for subdir in ["entities", "modules", "workflows"]:
        (wiki / subdir).mkdir(parents=True, exist_ok=True)
    _write_navigation_page(
        wiki / "index.md",
        """
        # LLM Wiki Index

        ## Entities

        - [User](entities/User.md)

        ## Modules

        - [models](modules/models.md)

        ## Workflows

        - [signup](workflows/signup.md)

        ## Log

        - [Architectural log](log.md)
        """,
    )
    _write_navigation_page(wiki / "log.md", "# Architectural Log\n\nLegacy log.\n")
    _write_navigation_page(
        wiki / "entities" / "User.md",
        "# User\n\nLegacy navigation entity.\n\n**Location:** `models.py:1`\n",
    )
    _write_navigation_page(
        wiki / "modules" / "models.md",
        "# models Module\n\nLegacy navigation module.\n\n**Path:** `models.py`\n",
    )
    _write_navigation_page(
        wiki / "workflows" / "signup.md",
        "# signup\n\nLegacy workflow links to [models](../modules/models.md).\n",
    )
    return NavigationWikiLayout(
        name="legacy",
        src_dir=src_dir,
        wiki_dir=wiki,
        inventory=_navigation_inventory(),
        docker_inventory={},
        expected_counts={
            "index": 1,
            "log": 1,
            "entities": 1,
            "modules": 1,
            "workflows": 1,
            "guides": 0,
            "flows": 0,
            "infrastructure": 0,
            "dependencies": 0,
            "load-order": 0,
            "api-contracts": 0,
            "architecture_pages": 0,
        },
        expected_uris={
            "llm-wiki://index",
            "llm-wiki://log",
            "llm-wiki://entities/User",
            "llm-wiki://modules/models",
            "llm-wiki://workflows/signup",
        },
        absent_uris={
            "llm-wiki://flows/api-run",
            "llm-wiki://infrastructure/Dockerfile",
            "llm-wiki://dependencies",
            "llm-wiki://load-order",
        },
        expected_mirror_paths={
            "LLM Wiki/Index.md",
            "LLM Wiki/Log.md",
            "LLM Wiki/Entities/User.md",
            "LLM Wiki/Modules/models.md",
            "LLM Wiki/Workflows/signup.md",
        },
        absent_mirror_paths={
            "LLM Wiki/Flows/api-run.md",
            "LLM Wiki/Infrastructure/Dockerfile.md",
            "LLM Wiki/Dependencies.md",
            "LLM Wiki/Load order.md",
        },
    )


def _write_current_navigation_wiki(root: Path) -> NavigationWikiLayout:
    src_dir = root / "current_project"
    wiki = src_dir / "docs" / "llm_wiki"
    src_dir.mkdir(parents=True)
    _write_navigation_page(
        src_dir / "models.py",
        """
        __all__ = ["run"]

        class User:
            pass

        def run():
            return User()
        """,
    )
    (src_dir / "Dockerfile").write_text("FROM python:3.11\n", encoding="utf-8")
    for subdir in ["entities", "modules", "workflows", "flows", "infrastructure"]:
        (wiki / subdir).mkdir(parents=True, exist_ok=True)
    _write_navigation_page(
        wiki / "index.md",
        """
        # LLM Wiki Index

        ## Entities

        - [User](entities/User.md)

        ## Modules

        - [models](modules/models.md)

        ## Workflows

        - [signup](workflows/signup.md)

        ## User Flows

        - [api-run](flows/api-run.md)

        ## Infrastructure

        - [Dockerfile](infrastructure/Dockerfile.md)

        ## Dependency Architecture

        - [Dependencies](dependencies.md)
        - [Load order](load-order.md)

        ## Log

        - [Architectural log](log.md)
        """,
    )
    _write_navigation_page(wiki / "log.md", "# Architectural Log\n\nCurrent log.\n")
    _write_navigation_page(
        wiki / "entities" / "User.md",
        "# User\n\nCurrent navigation entity.\n\n**Location:** `models.py:3`\n",
    )
    _write_navigation_page(
        wiki / "modules" / "models.md",
        "# models Module\n\nCurrent navigation module.\n\n**Path:** `models.py`\n",
    )
    _write_navigation_page(
        wiki / "workflows" / "signup.md",
        "# signup\n\nCurrent workflow links to [models](../modules/models.md).\n",
    )
    _write_navigation_page(
        wiki / "flows" / "api-run.md",
        "# api-run\n\nCurrent user flow links to [models](../modules/models.md).\n",
    )
    _write_navigation_page(
        wiki / "infrastructure" / "Dockerfile.md",
        "# Dockerfile\n\nCurrent infrastructure links to [models](../modules/models.md).\n",
    )
    _write_navigation_page(
        wiki / "dependencies.md",
        "# Dependencies\n\nCurrent dependency graph links to [models](modules/models.md).\n",
    )
    _write_navigation_page(
        wiki / "load-order.md",
        "# Load order\n\nCurrent load order links to [models](modules/models.md).\n",
    )
    return NavigationWikiLayout(
        name="current",
        src_dir=src_dir,
        wiki_dir=wiki,
        inventory=_navigation_inventory(),
        docker_inventory={"Dockerfile": {"type": "dockerfile"}},
        expected_counts={
            "index": 1,
            "log": 1,
            "entities": 1,
            "modules": 1,
            "workflows": 1,
            "guides": 0,
            "flows": 1,
            "infrastructure": 1,
            "dependencies": 1,
            "load-order": 1,
            "api-contracts": 0,
            "architecture_pages": 2,
        },
        expected_uris={
            "llm-wiki://index",
            "llm-wiki://log",
            "llm-wiki://entities/User",
            "llm-wiki://modules/models",
            "llm-wiki://workflows/signup",
            "llm-wiki://flows/api-run",
            "llm-wiki://infrastructure/Dockerfile",
            "llm-wiki://dependencies",
            "llm-wiki://load-order",
        },
        absent_uris=set(),
        expected_mirror_paths={
            "LLM Wiki/Index.md",
            "LLM Wiki/Log.md",
            "LLM Wiki/Entities/User.md",
            "LLM Wiki/Modules/models.md",
            "LLM Wiki/Workflows/signup.md",
            "LLM Wiki/Flows/api-run.md",
            "LLM Wiki/Infrastructure/Dockerfile.md",
            "LLM Wiki/Dependencies.md",
            "LLM Wiki/Load order.md",
        },
        absent_mirror_paths=set(),
    )


@pytest.fixture(autouse=True)
def _restore_cwd():
    """Safety net: restore CWD after every test, even if it fails mid-chdir."""
    old = os.getcwd()
    yield
    os.chdir(old)


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory with git init and sample Python files."""
    proj = tmp_path / "project"
    proj.mkdir()

    # git init — optional; create a stub .git dir if git is unavailable so that
    # tests relying on the path (e.g. circuit breaker state files) still work.
    if _GIT_AVAILABLE:
        subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", str(proj), "config", "user.email", "test@test.com"],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(proj), "config", "user.name", "Test"],
            capture_output=True,
            check=True,
        )
    else:
        (proj / ".git").mkdir(exist_ok=True)

    # sample Python files
    (proj / "models.py").write_text(
        textwrap.dedent("""\
        from pydantic import BaseModel

        class User(BaseModel):
            \"\"\"A user in the system.\"\"\"
            name: str
            email: str
            age: int = 0

        class Item(BaseModel):
            \"\"\"An item belonging to a user.\"\"\"
            title: str
            owner: User
            price: float = 0.0
    """)
    )

    (proj / "main.py").write_text(
        textwrap.dedent("""\
        from models import User, Item

        def create_user(name: str, email: str) -> User:
            \"\"\"Create a new user.\"\"\"
            return User(name=name, email=email)

        def list_items(user: User) -> list[Item]:
            \"\"\"List items for a user.\"\"\"
            return []
    """)
    )

    (proj / "utils.py").write_text(
        textwrap.dedent("""\
        import os
        from pathlib import Path

        def get_data_dir() -> Path:
            return Path(os.environ.get("DATA_DIR", "."))
    """)
    )

    # pyproject.toml for version tests
    (proj / "pyproject.toml").write_text(
        textwrap.dedent("""\
        [project]
        name = "sample"
        version = "0.1.0"
    """)
    )

    old_cwd = os.getcwd()
    os.chdir(proj)
    yield proj
    os.chdir(old_cwd)


@pytest.fixture
def tmp_wiki(tmp_path):
    """Create a pre-populated wiki directory."""
    wiki = tmp_path / "docs" / "llm_wiki"
    for subdir in ["entities", "modules", "workflows"]:
        (wiki / subdir).mkdir(parents=True)

    (wiki / "index.md").write_text(
        textwrap.dedent("""\
        # LLM Wiki Index

        ## Entities

        - [User](entities/User.md)
        - [Item](entities/Item.md)

        ## Modules

        - [models](modules/models.md)
        - [main](modules/main.md)

        ## Workflows
    """)
    )

    (wiki / "log.md").write_text("# Architectural Log\n\n")

    (wiki / "entities" / "User.md").write_text(
        "# User\n\n**Location:** `models.py:3`\n"
    )
    (wiki / "entities" / "Item.md").write_text(
        "# Item\n\n**Location:** `models.py:9`\n"
    )
    (wiki / "modules" / "models.md").write_text(
        "# models Module\n\n**Path:** `models.py`\n"
    )
    (wiki / "modules" / "main.md").write_text("# main Module\n\n**Path:** `main.py`\n")

    return wiki


@pytest.fixture
def legacy_navigation_wiki(tmp_path):
    return _write_legacy_navigation_wiki(tmp_path)


@pytest.fixture
def current_navigation_wiki(tmp_path):
    return _write_current_navigation_wiki(tmp_path)


@pytest.fixture(params=["legacy", "current"])
def navigation_wiki(request, tmp_path):
    if request.param == "legacy":
        return _write_legacy_navigation_wiki(tmp_path)
    return _write_current_navigation_wiki(tmp_path)
