"""Shared fixtures for llm_wiki_cli tests."""
import os
import subprocess
import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory with git init and sample Python files."""
    proj = tmp_path / "project"
    proj.mkdir()

    # git init
    subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(proj), "config", "user.email", "test@test.com"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(proj), "config", "user.name", "Test"], capture_output=True, check=True)

    # sample Python files
    (proj / "models.py").write_text(textwrap.dedent("""\
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
    """))

    (proj / "main.py").write_text(textwrap.dedent("""\
        from models import User, Item

        def create_user(name: str, email: str) -> User:
            \"\"\"Create a new user.\"\"\"
            return User(name=name, email=email)

        def list_items(user: User) -> list[Item]:
            \"\"\"List items for a user.\"\"\"
            return []
    """))

    (proj / "utils.py").write_text(textwrap.dedent("""\
        import os
        from pathlib import Path

        def get_data_dir() -> Path:
            return Path(os.environ.get("DATA_DIR", "."))
    """))

    # pyproject.toml for version tests
    (proj / "pyproject.toml").write_text(textwrap.dedent("""\
        [project]
        name = "sample"
        version = "0.1.0"
    """))

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

    (wiki / "index.md").write_text(textwrap.dedent("""\
        # LLM Wiki Index

        ## Entities

        - [User](entities/User.md)
        - [Item](entities/Item.md)

        ## Modules

        - [models](modules/models.md)
        - [main](modules/main.md)

        ## Workflows
    """))

    (wiki / "log.md").write_text("# Architectural Log\n\n")

    (wiki / "entities" / "User.md").write_text("# User\n\n**Location:** `models.py:3`\n")
    (wiki / "entities" / "Item.md").write_text("# Item\n\n**Location:** `models.py:9`\n")
    (wiki / "modules" / "models.md").write_text("# models Module\n\n**Path:** `models.py`\n")
    (wiki / "modules" / "main.md").write_text("# main Module\n\n**Path:** `main.py`\n")

    return wiki
