"""Discriminating real caller selection/provenance and dispatch contracts."""

import importlib.util
import json
from pathlib import Path
import subprocess

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "real_action_fixture", ROOT / "tests/provider_conformance/real_action_fixture.py"
)
assert spec and spec.loader
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


def test_real_callers_are_pinned_and_generated_sources_stay_excluded():
    specs = fixture.specs()
    assert specs["fastapi"]["commit"] == "cb740b656d7a0a6c5e12c7bf8e50343ec94ee9c7"
    assert specs["cobra"]["commit"] == "adbc8813901bba65827259daa8e22ff94ec1f30e"
    fastapi = specs["fastapi"]
    assert fastapi["selection"]["include"] == ["backend/app", "frontend/src"]
    assert "frontend/src/routeTree.gen.ts" in fastapi["selection"]["exclude"]
    assert "frontend/src/client/types.gen.ts" in fastapi["selection"]["exclude"]
    assert fastapi["helper_languages"] == ["typescript"]
    assert specs["cobra"]["helper_languages"] == ["go"]


def test_helper_plan_cannot_substitute_for_real_selected_declarations():
    expected = {"backend/app/models.py": {"classes": ["Item"]},
                "frontend/src/utils.ts": {"functions": ["getInitials"]}}
    only_python = {"backend/app/models.py": {"classes": [{"name": "Item"}]}}
    with pytest.raises(ValueError, match="frontend/src/utils.ts/functions"):
        fixture.check_declarations(only_python, expected)
    both = {**only_python, "frontend/src/utils.ts": {"functions": [{"name": "getInitials"}]}}
    fixture.check_declarations(both, expected)


def test_receiver_method_must_be_observed_in_selected_go_class():
    expected = {"command.go": {"classes": ["Command"], "methods": {"Command": ["Execute"]}}}
    wrong_owner = {"command.go": {"classes": [{"name": "Command", "methods": []},
                                              {"name": "Other", "methods": [{"name": "Execute"}]}],
                                 "functions": [{"name": "Execute"}]}}
    with pytest.raises(ValueError, match="command.go/methods"):
        fixture.check_declarations(wrong_owner, expected)


@pytest.mark.parametrize("case", ["wrong-path", "editable", "wrong-version"])
def test_runtime_cannot_borrow_another_provider_source(tmp_path, case):
    provider = tmp_path / "provider"
    value = {"version": "2.5.0", "direct_url": {"url": provider.as_uri(), "dir_info": {}}}
    fixture.validate_origin(value, provider)
    if case == "wrong-path":
        value["direct_url"]["url"] = (tmp_path / "another-source").as_uri()
    elif case == "editable":
        value["direct_url"]["dir_info"]["editable"] = True
    else:
        value["version"] = "2.4.0"
    with pytest.raises(ValueError, match="pinned provider source install"):
        fixture.validate_origin(value, provider)


def test_private_and_source_preimages_detect_private_changes_without_execution(tmp_path):
    (tmp_path / "source").mkdir()
    (tmp_path / "wiki").mkdir()
    (tmp_path / "private").mkdir()
    (tmp_path / "source/app.py").write_text("raise RuntimeError('not executed')\n")
    (tmp_path / "wiki/index.md").write_text("# Index\n")
    private = tmp_path / "private/notes.md"
    private.write_text("private sentinel")
    before = fixture.hashes(tmp_path)
    private.write_text("changed private sentinel")
    assert fixture.hashes(tmp_path) != before


@pytest.mark.parametrize("changed", [False, True])
def test_independent_corrupt_case_keeps_frozen_source(tmp_path, monkeypatch, changed):
    for name in ("source", "wiki", "private", "evidence"):
        (tmp_path / name).mkdir()
    source = tmp_path / "source/caller.go"
    source.write_text("package caller\n")
    surface = tmp_path / "wiki/.llm-wiki-surface.json"
    surface.write_text("{}")
    (tmp_path / "evidence/initial.json").write_text(json.dumps(fixture.hashes(tmp_path)))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(fixture, "require_provider", lambda *args: None)
    monkeypatch.setattr(fixture, "git", lambda *args: "")
    calls = []
    def controlled(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 1 if "ci-check" in command else 0,
                                           b'{"ok":false}', b"")
    monkeypatch.setattr(fixture.subprocess, "run", controlled)
    argv = ["mutate", "--project", "cobra", "--provider", str(tmp_path / "provider"),
            "--evidence", str(tmp_path / "evidence"), "--case", "corrupt",
            "--helper-cache", str(tmp_path / "cache")]
    if changed:
        source.write_text("package changed\n")
        with pytest.raises(ValueError, match="start with frozen source"):
            fixture.main(argv)
        assert surface.read_text() == "{}" and calls == []
    else:
        fixture.main(argv)
        assert source.read_text() == "package caller\n" and surface.read_text() == "{broken"
        assert any("ci-check" in c and "--no-report" in c for c in calls)


def test_dispatch_extends_owner_without_repeating_synthetic_jobs():
    value = yaml.safe_load((ROOT / ".github/workflows/action-selftest.yml").read_text())
    triggers = value.get("on", value.get(True))
    assert triggers["workflow_dispatch"]["inputs"]["provider-ref"]["default"] == fixture.PROVIDER_SHA
    jobs = value["jobs"]
    for name in ("repository-fixture", "foreign-caller"):
        assert jobs[name]["if"] == "${{ github.event_name != 'workflow_dispatch' }}"
    job = jobs["real-caller"]
    assert job["if"] == "${{ github.event_name == 'workflow_dispatch' }}"
    assert job["runs-on"] == "ubuntu-24.04" and job["strategy"]["max-parallel"] == 2
    matrix = job["strategy"]["matrix"]
    assert matrix["project"] == ["fastapi", "cobra"] and matrix["integration"] == ["context", "integrity"]
    assert matrix["state"] == ["clean", "drift", "corrupt"]
    assert {row["source-sha"] for row in matrix["include"]} == {s["commit"] for s in fixture.specs().values()}
    steps = job["steps"]
    uses = [s for s in steps if s.get("uses", "").startswith("./.provider/integrations/")]
    assert len(uses) == 2 and all(s["continue-on-error"] is True for s in uses)
    checks = [s for s in steps if s.get("name", "").startswith("Verify real caller")]
    assert len(checks) == 1 and all(not s.get("continue-on-error", False) for s in checks)
    bootstrap = next(s for s in steps if s.get("name") == "Prepare the matching locked caller toolchain")
    assert '"${RUNNER_TEMP}/real-bootstrap-toolchains"' in bootstrap["run"]
    assert '"${RUNNER_TEMP}/llm-wiki-toolchains"' not in bootstrap["run"]
    assert steps[-1]["if"] == "${{ always() }}"
    assert "github.run_id" in steps[-1]["with"]["name"]
