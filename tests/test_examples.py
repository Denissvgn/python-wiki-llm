"""Run public tutorial commands on isolated copies of their project inputs."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from markdown_it import MarkdownIt

from llm_wiki_cli.services.entrypoints import get_detailed_entry_points
from llm_wiki_cli.services.extraction_service import get_inventory_result, resolve_call_edges
from llm_wiki_cli.services.extractor_helpers import get_prepared_binary
from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions
from llm_wiki_cli.services.token_counting import EstimatedCounter

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
GO_BINARY = get_prepared_binary("go", ROOT)
GO_SKIP_REASON = "Prepared Go helper not available — Go example requires the toolchain owner"
_IGNORE_PROJECT_OUTPUTS = shutil.ignore_patterns(
    "wiki", "output", "vendor", ".helpers", ".llm-wiki", "AGENTS.md",
    ".venv", ".pytest_cache", "__pycache__", "*.pyc",
)


def _snapshot(root: Path, *, project_inputs: bool = False) -> dict[str, tuple[bytes, int]]:
    result = {}
    for directory, directories, files in os.walk(root):
        ignored = _IGNORE_PROJECT_OUTPUTS(directory, [*directories, *files]) if project_inputs else set()
        directories[:] = sorted(name for name in directories if name not in ignored)
        for name in sorted(files):
            if name not in ignored:
                path = Path(directory) / name
                result[path.relative_to(root).as_posix()] = (path.read_bytes(), path.stat().st_mtime_ns)
    return result


@pytest.fixture
def project_copy(tmp_path):
    originals = {}

    def copy(name):
        source = EXAMPLES / name / "project"
        originals[source] = _snapshot(source, project_inputs=True)
        target = tmp_path / name
        shutil.copytree(source, target, ignore=_IGNORE_PROJECT_OUTPUTS)
        return target

    yield copy

    for source, before in originals.items():
        assert _snapshot(source, project_inputs=True) == before, f"tutorial inputs were modified: {source}"


def _cli(project: Path, *args: str) -> str:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    environment.pop("LLM_WIKI_CACHE_DIR", None)
    result = subprocess.run(
        [sys.executable, "-m", "llm_wiki_cli.cli", *args], cwd=project,
        env=environment, capture_output=True, text=True, encoding="utf-8", timeout=90,
    )
    assert result.returncode == 0, (args, result.stdout, result.stderr)
    return result.stdout


def _documented(project: Path, name: str, heading: str) -> list[str]:
    readme = (EXAMPLES / name / "README.md").read_text(encoding="utf-8")
    tokens = MarkdownIt().parse(readme)
    active = False
    commands = []
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h2":
            active = tokens[index + 1].content == heading
        if active and token.type == "fence" and token.info == "sh":
            commands.extend(shlex.split(line) for line in token.content.splitlines() if line.strip())
    assert commands, heading
    assert all(command[0] == "llm-wiki" for command in commands)
    return [_cli(project, *command[1:]) for command in commands]


def _assert_first_sync_stable(project: Path, name: str) -> None:
    # Capture immediately after bootstrap; a warming sync could mask mutations.
    before = _snapshot(project / "wiki")
    _documented(project, name, "Repeat safely")
    assert _snapshot(project / "wiki") == before


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new), encoding="utf-8")


def _inventory(project: Path) -> dict:
    return json.loads((project / "output/inventory.json").read_text(encoding="utf-8"))


def test_existing_local_outputs_do_not_pollute_fresh_tutorial_copies(tmp_path, monkeypatch, project_copy):
    examples = tmp_path / "existing-examples"
    source = examples / "python-basic/project"
    shutil.copytree(EXAMPLES / "python-basic/project", source, ignore=_IGNORE_PROJECT_OUTPUTS)
    shutil.copy2(EXAMPLES / "python-basic/README.md", source.parent / "README.md")
    for relative in (
        "wiki/stale.md", "output/result.txt", ".helpers/cache.bin", "vendor/plugin.py",
        ".llm-wiki/plugins.lock.json", ".venv/cache", "__pycache__/app.pyc", "AGENTS.md",
    ):
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("existing local output", encoding="utf-8")
    before = _snapshot(source)
    monkeypatch.setattr(sys.modules[__name__], "EXAMPLES", examples)

    project = project_copy("python-basic")

    assert _snapshot(project) == _snapshot(source, project_inputs=True)
    _documented(project, "python-basic", "Generate the wiki")
    assert (project / "wiki/index.md").is_file()
    assert _snapshot(source) == before


def test_python_basic_tutorial(project_copy):
    name = "python-basic"
    project = project_copy(name)
    _documented(project, name, "Generate the wiki")
    entity = project / "wiki/entities/Task.md"
    assert "title" in entity.read_text(encoding="utf-8")
    assert (project / "wiki/modules/service.md").is_file()
    assert list((project / "wiki/flows").glob("process-*.md"))
    _assert_first_sync_stable(project, name)
    note = "Keep task titles in the user's original spelling."
    _replace(entity, "A title and completion state for one task.", f"A title and completion state for one task.\n\n{note}")
    _replace(project / "models.py", "    done: bool = False", "    done: bool = False\n    priority: int = 1")
    _documented(project, name, "Sync a source change")
    updated = entity.read_text(encoding="utf-8")
    assert "priority" in updated and note in updated
    search, context = _documented(project, name, "Search and context")
    assert "Task" in search and "Task" in context
    response = json.loads(context)
    accounting = response["accounting"]
    assert EstimatedCounter().count(context.rstrip("\n")) <= accounting["used_tokens"]
    assert EstimatedCounter().count(context) <= accounting["budget_tokens"]
    assert accounting["used_tokens"] <= accounting["budget_tokens"] == 1200
    assert not (project / "output/task.txt").exists()


def _assert_production_contract(project: Path, suffix: str) -> None:
    payload = _inventory(project)
    assert "tests/test_app.py" in payload["inventory"]
    contracts = payload["api_contracts"]
    assert len(contracts["applications"]) == 1
    assert {(operation["method"], operation["path"]) for operation in contracts["operations"]} == {
        ("GET", f"/api/{suffix}"), ("GET", f"/preview/{suffix}")
    }
    markdown = (project / "wiki/api-contracts.md").read_text(encoding="utf-8")
    assert "/test-app/" not in markdown and "/test-only/" not in markdown
    assert "list_books" in markdown
    links = re.findall(r"\]\((flows/[^)#]+\.md)(?:#[^)]*)?\)", markdown)
    assert links
    assert all((project / "wiki" / link).is_file() for link in links)


def test_fastapi_contracts_tutorial(project_copy):
    name = "fastapi-contracts"
    project = project_copy(name)
    _documented(project, name, "Generate the wiki")
    _assert_production_contract(project, "books")
    _assert_first_sync_stable(project, name)
    note = "Preview is a second production mount, not a temporary test application."
    _replace(project / "wiki/api-contracts.md", "## Notes\n", f"## Notes\n\n{note}\n")
    _replace(project / "routes.py", '"/books"', '"/reading-list"')
    _documented(project, name, "Sync a source change")
    _assert_production_contract(project, "reading-list")
    assert note in (project / "wiki/api-contracts.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("symbol, renamed", [
    ("handle_task", "task_handler"),
    ("HANDLE_TASK", "Task_Handler"),
])
def test_plugin_hooks_tutorial(project_copy, symbol, renamed):
    name = "plugin-hooks"
    project = project_copy(name)
    _replace(project / "tasks.py", "def handle_task(", f"def {symbol}(")
    _documented(project, name, "Generate the wiki")
    flow = project / "wiki/flows/task-task-handler.md"
    markdown = flow.read_text(encoding="utf-8")
    assert f's1["1. {symbol}"]' in markdown
    assert "classDef entry fill:#2E7D32,stroke:#2E7D32" in markdown
    assert "class s1 entry" in markdown and "save_result" in markdown
    _assert_first_sync_stable(project, name)
    _replace(project / "tasks.py", f"def {symbol}(", f"def {renamed}(")
    _documented(project, name, "Sync a source change")
    updated = flow.read_text(encoding="utf-8")
    assert f's1["1. {renamed}"]' in updated and "class s1 entry" in updated
    assert not (project / "output/result.txt").exists()


@pytest.mark.skipif(GO_BINARY is None, reason=GO_SKIP_REASON)
def test_go_http_tutorial(project_copy, monkeypatch):
    assert GO_BINARY is not None
    name = "go-http"
    project = project_copy(name)
    helper = Path(GO_BINARY)
    target = project / ".helpers/llm-wiki-extractors/go" / helper.parent.name
    shutil.copytree(helper.parent, target)
    manifest = json.loads((helper.parent.parent / "current.json").read_text(encoding="utf-8"))
    manifest["path"] = str(target / helper.name)
    (target.parent / "current.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert get_prepared_binary("go", project, str(project / ".helpers")) is not None
    monkeypatch.chdir(project)
    _documented(project, name, "Generate the wiki")
    inventory = _inventory(project)["inventory"]
    detailed = get_detailed_entry_points(inventory, root=project)
    observations = detailed["observations"]
    observed = {
        (item["entry"]["category"], item["entry"]["file"], item["entry"]["symbol"])
        for item in observations
    }
    assert ("process", "cmd/server/main.go", "main") in observed
    assert ("http", "cmd/server/handlers.go", "health") in observed
    handler = next(item for item in observations if item["entry"]["category"] == "http")
    line = next(index for index, text in enumerate((project / "cmd/server/main.go").read_text().splitlines(), 1) if "mux.HandleFunc(" in text)
    assert handler["detector"]["source_location"] == {"source_path": "cmd/server/main.go", "line": line}
    edges = resolve_call_edges(inventory)
    assert any(edge["from"]["symbol"] == "health" and edge["to"] == {"file": "internal/store/store.go", "symbol": "Status"} for edge in edges)
    assert any(edge["to"] == {"file": "internal/store/store.go", "symbol": "Store.status"} for edge in edges)
    _assert_first_sync_stable(project, name)
    options = InventoryCacheOptions(enabled=True, cache_dir=str(project / ".helpers/inventory"))
    kwargs = {"deep": True, "helper_cache_dir": str(project / ".helpers")}
    get_inventory_result(project, cache_options=options, **kwargs)
    store = project / "internal/store/store.go"
    _replace(store, "status()", "message()")
    _documented(project, name, "Sync a source change")
    assert "message" in (project / "wiki/entities/Store.md").read_text(encoding="utf-8")
    assert "Store.message" in (project / "wiki/flows/http-health.md").read_text(encoding="utf-8")
    warm = get_inventory_result(project, cache_options=options, **kwargs).inventory
    assert warm == get_inventory_result(project, **kwargs).inventory
    assert any(edge["to"] == {"file": "internal/store/store.go", "symbol": "Store.message"} for edge in resolve_call_edges(warm))
    _replace(store, 'func (s Store) message() string {\n\treturn "ready"\n}\n', "")
    warm = get_inventory_result(project, cache_options=options, **kwargs).inventory
    assert warm == get_inventory_result(project, **kwargs).inventory
    assert not any(method["name"] == "message" for cls in warm["internal/store/store.go"]["classes"] for method in cls.get("methods", []))
    calls = [edge for edge in resolve_call_edges(warm) if edge["to"] and edge["to"]["symbol"] == "Store.message"]
    assert calls and all(edge["kind"] == "unresolved" for edge in calls)


def test_example_readme_local_links_resolve():
    for readme in EXAMPLES.rglob("README.md"):
        for link in re.findall(r"\]\(([^)]+)\)", readme.read_text(encoding="utf-8")):
            if "://" in link or link.startswith("#"):
                continue
            assert (readme.parent / link.split("#", 1)[0]).exists(), (readme, link)
