"""Execute documented source and native routes against owned disposable projects."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import shlex
import sys

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.mcp_server import McpWikiService
from llm_wiki_cli.services.schema import SchemaRenderProfile, build_schema_content

REPOSITORY = Path(__file__).resolve().parents[1]
WORKFLOW = (REPOSITORY / "docs/native-agent-workflow.md").read_text(encoding="utf-8")
CONTEXT_ROUTE = (
    REPOSITORY / "src/llm_wiki_cli/skills/wiki-reference/references/context-query.md"
).read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    return text.split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]


def blocks(text: str, language: str) -> list[str]:
    return re.findall(rf"```{language}\n(.*?)\n[ \t]*```", text, flags=re.DOTALL)


def command(text: str, prefix: str) -> list[str]:
    lines = [
        line
        for block in blocks(text, "bash")
        for line in block.splitlines()
        if line.startswith(prefix)
    ]
    assert len(lines) == 1, (prefix, lines)
    return shlex.split(lines[0])[1:]


def run_cli(monkeypatch, capsys, argv: list[str]) -> tuple[int, str, str]:
    monkeypatch.setattr(sys, "argv", ["llm-wiki", *argv])
    try:
        cli.main()
        code = 0
    except SystemExit as exc:
        assert type(exc.code) is int
        code = exc.code
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def tree(path: Path) -> dict[str, bytes]:
    return {
        p.relative_to(path).as_posix(): p.read_bytes()
        for p in path.rglob("*")
        if p.is_file() and not p.is_symlink()
    }


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source_section = section(WORKFLOW, "Source-only task without a wiki")
    Path("src").mkdir()
    Path("src/app.py").write_text(blocks(source_section, "python")[0] + "\n")
    request = json.loads(blocks(source_section, "json")[0])
    Path("source-task.json").write_text(json.dumps(request))
    native_section = section(WORKFLOW, "Native task with current storage")
    native_request = json.loads(blocks(native_section, "json")[0])
    Path("native-task.json").write_text(json.dumps(native_request))
    return tmp_path, request, native_request


def test_source_only_documented_python_cli_and_installed_skill_no_wiki(
    workspace, monkeypatch, capsys
):
    root, request, _ = workspace
    before = tree(root)
    source_section = section(WORKFLOW, "Source-only task without a wiki")
    code, text, error = run_cli(
        monkeypatch, capsys, command(source_section, "llm-wiki task-context ")
    )
    assert code == 0 and error == ""
    payload = api.validate_task_context(text, request)
    assert payload["state"] == "covered"
    assert payload["storage"]["status"] == "off"
    assert payload["facts"][0]["observation"]["selector"] == "app.py:limit#1"
    namespace: dict = {}
    exec(
        compile(blocks(source_section, "python")[1], "documented-api", "exec"),
        namespace,
    )
    capsys.readouterr()
    assert namespace["result"].rendered == text
    assert namespace["payload"] == payload
    installed = section(CONTEXT_ROUTE, "Explicit task adoption routes")
    skill_request = json.loads(blocks(installed, "json")[0])
    skill_result = api.build_task_context(skill_request, src_dir="src", wiki_dir="wiki")
    skill_payload = api.validate_task_context(skill_result.rendered, skill_request)
    assert skill_payload["coverage"][0]["satisfied"]
    assert not Path("wiki").exists() and tree(root) == before


def test_flat_native_rejection_preserves_request_and_all_bytes(
    workspace, monkeypatch, capsys
):
    root, _, request = workspace
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    capsys.readouterr()
    before = tree(root)
    frozen = deepcopy(request)
    with pytest.raises(api.InvalidRequestError, match="explicit sharded or packed"):
        api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    native_section = section(WORKFLOW, "Native task with current storage")
    code, _, error = run_cli(
        monkeypatch, capsys, command(native_section, "llm-wiki task-context ")
    )
    assert code == 2 and json.loads(error)["error"]["code"] == "invalid-request"
    assert request == frozen and tree(root) == before


def test_documented_upgrade_selects_current_storage_and_retains_preimages(
    workspace, monkeypatch, capsys
):
    _, _, request = workspace
    code, _, _ = run_cli(monkeypatch, capsys, ["init", "--agent", "generic", "--wiki-dir", "wiki"])
    assert code == 0
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    capsys.readouterr()
    before = tree(Path("wiki"))
    source_before = tree(Path("src"))
    native_section = section(WORKFLOW, "Native task with current storage")
    code, text, _ = run_cli(monkeypatch, capsys, command(native_section, "llm-wiki upgrade "))
    assert code == 0
    recovery = Path(next(line.split("Native upgrade recovery: ", 1)[1]
                         for line in text.splitlines() if line.startswith("Native upgrade recovery: ")))
    assert all((recovery / "adoption/before" / name).read_bytes() == raw
               for name, raw in before.items() if name.endswith(".md"))
    code, text, _ = run_cli(monkeypatch, capsys, command(native_section, "llm-wiki knowledge storage-check "))
    assert code == 0 and json.loads(text)["ok"]
    assert json.loads(text)["format"] == "packed-v4-deflate"
    assert json.loads(Path("wiki/.llm-wiki-manifest.json").read_bytes())["version"] == 8
    after = tree(Path("wiki"))
    assert {name: raw for name, raw in after.items() if name.endswith(".md")} == {
        name: raw for name, raw in before.items() if name.endswith(".md")}
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    assert api.validate_task_context(result.rendered, request)["coverage"][0]["satisfied"]
    assert tree(Path("src")) == source_before
    code, text, _ = run_cli(monkeypatch, capsys, command(native_section, "llm-wiki upgrade "))
    assert code == 0 and "Native upgrade recovery:" not in text
    assert tree(Path("wiki")) == after


def bootstrap_native(monkeypatch, capsys):
    native_section = section(WORKFLOW, "Native task with current storage")
    code, _, _ = run_cli(
        monkeypatch, capsys, command(native_section, "llm-wiki bootstrap ")
    )
    assert code == 0


def test_new_native_bootstrap_is_explicit_snapshot_and_required_behavior_stays_gap(
    workspace, monkeypatch, capsys
):
    root, _, request = workspace
    bootstrap_native(monkeypatch, capsys)
    before = tree(root)
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    payload = api.validate_task_context(result.rendered, request)
    assert payload["coverage"][0]["satisfied"]
    assert payload["source_capture"] is None
    assert payload["storage"]["whole_store_validated"] is False
    request["requirements"].append(
        {"id": "behavior", "facet": "behavior", "selector": "app.py:limit"}
    )
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    payload = api.validate_task_context(result.rendered, request)
    coverage = {row["requirement_id"]: row for row in payload["coverage"]}
    assert coverage["concept"]["satisfied"] and not coverage["behavior"]["satisfied"]
    assert coverage["behavior"]["reason"] == "host-behavioral-verification-required"
    assert payload["state"] == "incomplete"
    assert request["options"]["knowledge_mode"] == "required"
    assert tree(root) == before


@pytest.mark.parametrize("damage", ["absent", "corrupt", "unsupported"])
def test_required_native_damage_never_seeds_or_downgrades(
    workspace, monkeypatch, capsys, damage
):
    root, source_request, request = workspace
    if damage != "absent":
        bootstrap_native(monkeypatch, capsys)
        path = Path("wiki/.llm-wiki-knowledge.json")
        if damage == "corrupt":
            path.write_text("{broken")
        else:
            data = json.loads(path.read_text())
            data["schema_version"] = "llm-wiki-knowledge/v999"
            path.write_text(json.dumps(data))
    before = tree(root)
    frozen = deepcopy(request)
    with pytest.raises(api.LlmWikiApiError):
        api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    independent = api.build_task_context(source_request, src_dir="src", wiki_dir="wiki")
    assert (
        api.validate_task_context(independent.rendered, source_request)["storage"][
            "status"
        ]
        == "off"
    )
    assert request == frozen and tree(root) == before


def test_missing_maintenance_owner_blocks_seeding_then_complete_recovery(
    workspace, monkeypatch, capsys
):
    _, _, request = workspace
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    capsys.readouterr()
    adopted = api.adopt_maintenance("src", "wiki", recovery_dir="maintenance-recovery")
    before = tree(Path("wiki"))
    Path("wiki/.llm-wiki-manifest.json").unlink()
    damaged = tree(Path("wiki"))
    code, _, _ = run_cli(
        monkeypatch, capsys, ["sync", "--src-dir", "src", "--wiki-dir", "wiki"]
    )
    assert code != 0 and tree(Path("wiki")) == damaged
    with pytest.raises(api.LlmWikiApiError):
        api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    assert tree(Path("wiki")) == damaged
    native_section = section(WORKFLOW, "Native task with current storage")
    recovery = command(native_section, "llm-wiki maintenance recover ")
    recovery[-1] = adopted["adoption_id"]
    code, text, _ = run_cli(monkeypatch, capsys, recovery)
    assert code == 0 and json.loads(text)["restored"]
    assert tree(Path("wiki")) == before


def test_optional_compact_recipe_exact_receipt_and_too_small_view(
    workspace, monkeypatch, capsys
):
    root, request, _ = workspace
    compact_section = section(WORKFLOW, "Optional compact delivery")
    argv = command(compact_section, "llm-wiki task-context ")
    code, view_text, error = run_cli(monkeypatch, capsys, argv)
    assert code == 0 and error == ""
    canonical = Path("receipts/source-context.json").read_text()
    options = {
        "budget_tokens": 32000,
    }
    expanded = api.expand_compact_task_context(
        view_text, canonical, request, view_options=options
    )
    payload = api.validate_task_context(canonical, request)
    assert (
        expanded["facts"] == payload["facts"]
        and expanded["coverage"] == payload["coverage"]
    )
    namespace = {"api": api, "request": request}
    exec(
        compile(blocks(compact_section, "python")[0], "documented-compact-api", "exec"),
        namespace,
    )
    assert namespace["view"].rendered == view_text
    assert not Path("wiki").exists()
    Path("views").mkdir()
    Path("views/context.json").write_text("retain previous view")
    argv[argv.index("--view-budget-tokens") + 1] = "1"
    argv += ["--output", "views/context.json"]
    code, text, error = run_cli(monkeypatch, capsys, argv)
    assert code == 3 and text == "" and "cannot-fit-compact" in error
    assert Path("views/context.json").read_text() == "retain previous view"
    assert Path("receipts/source-context.json").read_text() == canonical
    assert (root / "src/app.py").exists()


def test_expanded_generated_source_route_is_an_executable_request(workspace):
    _, _, _ = workspace
    rendered = build_schema_content(
        "generic", "wiki", render_profile=SchemaRenderProfile.EXPANDED_INLINE
    )
    recipes = blocks(rendered, "json")
    request = next(
        json.loads(text) for text in recipes if '"requirements"' in text
    )
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    assert api.validate_task_context(result.rendered, request)["coverage"][0][
        "satisfied"
    ]
    assert not Path("wiki").exists()


@pytest.mark.parametrize("native", [False, True])
def test_documented_requests_have_same_read_only_mcp_and_python_evidence(
    workspace, monkeypatch, capsys, native
):
    root, source_request, native_request = workspace
    if native:
        bootstrap_native(monkeypatch, capsys)
    request = native_request if native else source_request
    before = tree(root)
    service = McpWikiService(src_dir="src", wiki_dir="wiki")
    text = service.build_task_context(request)
    canonical = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    assert text == canonical.rendered
    payload = api.validate_task_context(text, request)
    assert payload["coverage"][0]["satisfied"]
    assert tree(root) == before
