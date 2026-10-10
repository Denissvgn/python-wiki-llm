"""Disposable owned projects and explicit workflow actions, never target execution on reads."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
from typing import Any

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage

POLICY_SOURCE = '''from pathlib import Path
import os

if os.environ.get("AGENT_WIKI_OWNED_ORACLE") != "window-fixture":
    Path("source-execution-tripwire").write_text("unexpected target execution")

class Window:
    """Clip a configured window of records."""
    def clip(self, values: list[int], limit: int = 3) -> list[int]:
        return values[:limit] if limit > 0 else []

def public_clip(values):
    return Window().clip(values)
'''
CLIENT_SOURCE = '''from policy import Window as LocalWindow

def direct_clip(values):
    return LocalWindow().clip(values)

def assigned_clip(values):
    window = LocalWindow()
    return window.clip(values)

def dynamic_clip(factory, values):
    return factory().clip(values)
'''
STABLE_SOURCE = '''class Stable:
    """Keep an independent unchanged calculation."""
    def unchanged(self, value: int = 9) -> int:
        return value + 10
'''
SCOPE_SOURCE = '''class Repeated:
    def touch(self, value):
        return value + 1

class Repeated:
    def touch(self, value):
        return value + 2
'''
SOURCE_FILES = {"policy.py": POLICY_SOURCE, "client.py": CLIENT_SOURCE,
                "stable.py": STABLE_SOURCE, "scope.py": SCOPE_SOURCE}
INITIAL_PROSE = "Keeps the first limit values. Non-positive limits produce an empty list. The default limit is 3."
BODY_PROSE = "Keeps the last limit values. Non-positive limits produce an empty list. The default limit is 3."
DEFAULT_PROSE = "Keeps the first limit values. Non-positive limits produce an empty list. The default limit is 2."
VIEW = {"schema_version": "llm-wiki-task-view-request/v1", "budget_tokens": 32000}


def policy_source(change="before"):
    if change == "before":
        return POLICY_SOURCE
    if change == "body":
        return POLICY_SOURCE.replace("values[:limit]", "values[max(0, len(values) - limit):]")
    if change == "default":
        return POLICY_SOURCE.replace("limit: int = 3", "limit: int = 2")
    raise ValueError("Unknown controlled source change")


@dataclass(frozen=True)
class WorkflowProject:
    root: Path
    variant: str

    @property
    def source(self):
        return self.root / "src"

    @property
    def wiki(self):
        return self.root / "wiki"

    @property
    def options(self) -> dict[str, Any]:
        return {"src_dir": str(self.source), "wiki_dir": str(self.wiki)}

    @property
    def context_options(self) -> dict[str, Any]:
        return {**self.options, "policy": api.WorkflowPolicy(read_scope="full-inventory")}

    def tree(self):
        return {path.relative_to(self.root).as_posix(): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file()
                and "__pycache__" not in path.parts and path.suffix != ".pyc"}


def sync_workflow(project):
    with patch.object(sys, "argv", ["llm-wiki", "sync", "--src-dir", str(project.source),
                                    "--wiki-dir", str(project.wiki), "--jobs", "1", "--no-plugins"]):
        cli.main()


def write_description(project, text, page="entities/Window.md"):
    from tests.test_knowledge_commands import _write_reviewed_description
    _write_reviewed_description(project.wiki / page, text)


def prepare_workflow(root: Path, variant: str) -> WorkflowProject:
    if variant not in {"source-only", "native-absent", "legacy", "adopted-flat", "sharded", "packed"}:
        raise ValueError("Unknown controlled storage variant")
    project = WorkflowProject(root.resolve(), variant)
    project.source.mkdir()
    for name, source in SOURCE_FILES.items():
        (project.source / name).write_bytes(source.encode("utf-8"))
    if variant not in {"source-only", "native-absent"}:
        profile = project.source / ".llm-wiki/source-selection.json"
        profile.parent.mkdir()
        profile.write_bytes((json.dumps({"schema_version": "llm-wiki-source-selection/v1",
                                      "include": list(SOURCE_FILES), "exclude": []}) + "\n").encode("utf-8"))
        api.bootstrap_wiki(str(project.source), str(project.wiki))
        write_description(project, INITIAL_PROSE)
        sync_workflow(project)
        if variant != "legacy":
            api.adopt_maintenance(**project.options, recovery_dir=root / "maintenance-recovery")
        if variant in {"sharded", "packed"}:
            migrate_knowledge_storage(project.wiki,
                to="sharded-v2" if variant == "sharded" else "packed-v4-deflate",
                recovery_dir=root / "storage-recovery")
            migrate_knowledge_storage(project.wiki, to="indexed-v8", recovery_dir=root / "manifest-recovery")
    elif variant == "native-absent":
        (project.wiki / "guides").mkdir(parents=True)
        (project.wiki / "guides/orientation.md").write_bytes(("# Window clipping\n\nInspect policy.py:Window.clip.\n").encode("utf-8"))
    return project


def mutate_source(project, change="body"):
    (project.source / "policy.py").write_bytes((policy_source(change)).encode("utf-8"))


def run_behavior_oracle(project, change="before"):
    """Execute ONLY the byte-admitted owned fixture in an explicit isolated phase."""
    expected = {**SOURCE_FILES, "policy.py": policy_source(change)}
    actual = {path.relative_to(project.source).as_posix(): path.read_bytes()
              for path in project.source.rglob("*.py")}
    assert actual == {name: source.encode("utf-8") for name, source in expected.items()}
    interpreter = Path(sys.executable)
    assert interpreter.is_file()
    code = '''import json, runpy, sys
window = runpy.run_path(sys.argv[1])["Window"]()
values = [0, 1, 2, 3, 4]
print(json.dumps({"default": window.clip(values), "limits": {str(n): window.clip(values, n) for n in [3, 1, 0, -1, 9]}}))
'''
    completed = subprocess.run([str(interpreter), "-I", "-c", code, str(project.source / "policy.py")],
        cwd=project.root, env={**os.environ, "AGENT_WIKI_OWNED_ORACLE": "window-fixture",
                              "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, text=True, check=True, timeout=10)
    assert not (project.root / "source-execution-tripwire").exists()
    return json.loads(completed.stdout)


def task_request(native=False, schema="v2") -> dict[str, Any]:
    value: dict[str, Any] = {"schema_version": "llm-wiki-task-request/" + schema,
        "task_ref": "owned-window-change",
        "anchors": [{"kind": "source", "value": "policy.py"}],
        "requirements": [
            {"id": "decisive", "facet": "source-contract", "selector": "policy.py:Window.clip"},
            {"id": "callers", "facet": "callers", "selector": "policy.py:Window.clip"},
            {"id": "missing", "facet": "source-contract", "selector": "policy.py:not_present"},
            {"id": "ambiguous", "facet": "source-contract", "selector": "scope.py:Repeated.touch"},
            {"id": "behavior", "facet": "behavior", "selector": "policy.py:Window.clip"}],
        "options": {"knowledge_mode": "required" if native else "off", "budget_tokens": 32000,
                    "read_scope": "full-inventory", "max_read_rounds": 8}}
    if native:
        value["requirements"].extend([
            {"id": "concept", "facet": "concept", "selector": "entities/Window.md"},
            {"id": "prose", "facet": "semantic-section", "selector": "entities/Window.md"}])
        if schema == "v2":
            value["storage_options"] = {"selection": "required-facets-v1"}
    return value


def compact_payload(project, request):
    result = api.build_compact_task_context(request, view_options=VIEW, **project.context_options)
    assert result.ok
    canonical = api.validate_task_context(result.canonical_text, request, policy=project.context_options["policy"])
    expanded = api.expand_compact_task_context(result.rendered, result.canonical_text, request,
                                              view_options=VIEW, policy=project.context_options["policy"])
    return result, canonical, expanded


def record_workflow_trace(project, scenario, observation):
    """Persist test evidence only when an explicit local harness output is supplied."""
    destination = os.environ.get("AGENT_WIKI_WORKFLOW_TRACE_DIR")
    if destination is None:
        return
    output = Path(destination).resolve()
    assert not output.is_relative_to(project.root), "Evidence output must stay outside the observed workspace"
    output.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": "owned-workflow-trace/v1", "scenario": scenario,
        "variant": project.variant, "model_productivity_measured": False,
        "source_hashes": {path.relative_to(project.source).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in sorted(project.source.rglob("*.py"))},
        "observations": observation}
    (output / f"{scenario}-{project.variant}.json").write_bytes((json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
