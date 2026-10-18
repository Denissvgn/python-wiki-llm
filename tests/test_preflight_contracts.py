"""Fail-closed early release mappings and independently checked agent variants."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import pytest

from release import preflight_contracts as p

ROOT = Path(__file__).parents[1]


@pytest.fixture
def repository(tmp_path):
    value = json.loads((ROOT / p.REGISTRY).read_bytes())
    paths = {
        p.REGISTRY,
        p.WORKFLOW,
        "src/llm_wiki_cli/config.py",
        "release/knowledge_maintenance.py",
    }
    paths.update(row["owner"] for row in value["jobs"])
    paths.update(
        row[key]
        for row in value["maintenance_dependencies"]
        for key in ("path", "owner")
    )
    paths.update(
        selector.split("::")[0] for group in p.GROUPS.values() for selector in group
    )
    paths.update(
        selector.split("::")[0]
        for row in value["incident_cases"]
        for selector in row["selectors"]
    )
    for name in paths:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    return tmp_path


def change_registry(root, edit):
    path = root / p.REGISTRY
    value = json.loads(path.read_bytes())
    edit(value)
    path.write_text(json.dumps(value))


def test_real_declarations_map_all_jobs_and_maintenance_without_writes(repository):
    before = {
        x.relative_to(repository): x.read_bytes()
        for x in repository.rglob("*")
        if x.is_file()
    }
    assert p.validate_workflow_contracts(repository) == []
    value = p.qualification_contract(repository)
    assert len(value["jobs"]) == 25
    assert len(value["incident_cases"]) == 31
    assert {x["id"] for x in value["jobs"]} == set(
        p.workflow_declarations(repository)[1]
    )
    assert all(x["owner"] and x["expected_evidence"] for x in value["jobs"])
    assert value["authority"] == "local-nonpromoting"
    # Independent guards that exposed failures outside the original early set.
    assert {
        "tests/test_architecture_layers.py",
        "tests/test_api_exception_taxonomy.py",
    } <= set(value["groups"]["inventory"])
    assert {
        "tests/test_agent_instruction_decisions.py",
        "tests/test_skill_policy_routes.py",
        "tests/test_helper_preparation.py",
        "tests/test_instruction_ownership.py",
        "tests/test_schema.py",
        "tests/test_schema_context_baselines.py",
        "tests/test_skill_ownership_boundaries.py",
    } <= set(value["groups"]["defaults"])
    assert "tests/test_native_knowledge_semantics_docs.py" in value["groups"]["packet"]
    assert {"tests/test_package_validation.py", "tests/test_package_metadata.py"} <= set(value["groups"]["release"])
    assert {
        x.relative_to(repository): x.read_bytes()
        for x in repository.rglob("*")
        if x.is_file()
    } == before


@pytest.mark.parametrize(
    "mutation,expected",
    [
        (
            lambda s: s + "\n  surprise:\n    runs-on: ubuntu-24.04\n    steps: []\n",
            "unmapped qualification producer",
        ),
        (
            lambda s: s.replace("  freeze:\n", "  not-freeze:\n", 1),
            "unmapped qualification producer",
        ),
        (
            lambda s: s.replace("needs.freeze.result == 'success'", "true", 1),
            "declaration changed",
        ),
        (
            lambda s: s.replace(
                "python -I release/knowledge_maintenance.py check-version",
                "true # bypassed",
                1,
            ),
            "declaration changed",
        ),
        (lambda s: s.replace('  CI: "1"', '  CI: "0"', 1), "global conditions changed"),
    ],
)
def test_new_producer_condition_command_or_global_mode_refuses(
    repository, mutation, expected
):
    path = repository / p.WORKFLOW
    path.write_text(mutation(path.read_text()))
    assert any(expected in error for error in p.validate_workflow_contracts(repository))


@pytest.mark.parametrize(
    "edit,expected",
    [
        (lambda v: v["jobs"][0].update(owner=""), "no maintained command owner"),
        (
            lambda v: v["jobs"][0].update(capabilities=["unmodeled-native-host"]),
            "unknown capability",
        ),
        (lambda v: v["jobs"][0].update(condition="true"), "condition metadata differs"),
        (lambda v: v["jobs"][0].update(needs=["nonexistent"]), "unmapped dependency"),
        (lambda v: v["jobs"][0].update(gates=["RD-99"]), "unknown release gate"),
        (
            lambda v: v["jobs"][0].update(normal_required=False),
            "mandatory normal qualification",
        ),
        (
            lambda v: v["jobs"][0].update(environments=["windows-2025"]),
            "environment metadata differs",
        ),
        (lambda v: v["jobs"][0].update(timeout_minutes=1), "timeout metadata differs"),
        (lambda v: v["groups"].pop("defaults"), "group declarations differ"),
        (
            lambda v: v["incident_cases"].pop(),
            "missing, extra or duplicate dispositions",
        ),
        (
            lambda v: v["incident_cases"][0].update(
                selectors=["tests/test_current_install_defaults.py::test_invented_pass"]
            ),
            "missing incident regression owner",
        ),
        (
            lambda v: v["maintenance_dependencies"].append(
                v["maintenance_dependencies"][0]
            ),
            "duplicate maintenance dependency",
        ),
    ],
)
def test_missing_owner_coverage_or_unknown_metadata_refuses(repository, edit, expected):
    change_registry(repository, edit)
    assert any(expected in error for error in p.validate_workflow_contracts(repository))


def test_new_policy_dependency_requires_mapping(repository):
    path = repository / "release/knowledge_maintenance.py"
    text = path.read_text().replace(
        "POLICY_INPUTS = (LEAF_PATH,",
        'POLICY_INPUTS = ("new-policy-input.py", LEAF_PATH,',
    )
    path.write_text(text)
    assert any(
        "unmapped maintenance policy inputs" in error
        for error in p.validate_workflow_contracts(repository)
    )


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":NaN}', b"[]", b"{"])
def test_malformed_registry_never_admitted(repository, raw):
    (repository / p.REGISTRY).write_bytes(raw)
    assert p.validate_workflow_contracts(repository)


def junit_agents(repository, path, *, omit=None, skipped=None, duplicate=None):
    suite = ET.Element("testsuite")
    for agent in p.supported_agents(repository):
        for fallback in ("False", "True"):
            names = [
                f"test_all_agents_init_and_upgrade_install_current_defaults[{fallback}-{agent}]"
            ]
            names += [
                f"test_default_workflow_installation_and_upgrade_preserve_project_policy[{flavor}-{fallback}-{agent}]"
                for flavor in ("posix-input", "windows-input")
            ]
            names.append(
                "test_installed_recovery_recipes_work_after_init_and_upgrade"
                f"[{'inline' if fallback == 'True' else 'skills'}-{agent}]"
            )
            for name in names:
                if name == omit:
                    continue
                case = ET.SubElement(suite, "testcase", name=name)
                if name == skipped:
                    ET.SubElement(case, "skipped", message="unavailable")
                if name == duplicate:
                    ET.SubElement(suite, "testcase", name=name)
    path.write_bytes(ET.tostring(suite))


@pytest.mark.parametrize("fault", [None, "omit", "skipped", "duplicate", "new-agent"])
def test_agent_matrix_independently_requires_every_member_and_fallback(
    repository, tmp_path, fault
):
    path = tmp_path / "matrix.xml"
    name = "test_all_agents_init_and_upgrade_install_current_defaults[True-generic]"
    junit_agents(
        repository,
        path,
        **({fault: name} if fault in {"omit", "skipped", "duplicate"} else {}),
    )
    if fault == "new-agent":
        config = repository / "src/llm_wiki_cli/config.py"
        config.write_text(
            config.read_text().replace(
                "AGENT_CHOICES = [", 'AGENT_CHOICES = ["future-agent", '
            )
        )
    errors = p.audit_agent_variants(repository, path)
    assert bool(errors) is (fault is not None)


@pytest.mark.parametrize(
    "agent", ["claude", "cursor", "copilot", "aider", "opencode", "generic"]
)
@pytest.mark.parametrize("mode", ["skills", "inline"])
@pytest.mark.parametrize("fault", ["omit", "skipped", "failure", "duplicate"])
def test_recovery_matrix_requires_every_successful_recipe_variant(
    repository, tmp_path, agent, mode, fault
):
    path = tmp_path / "matrix.xml"
    name = f"test_installed_recovery_recipes_work_after_init_and_upgrade[{mode}-{agent}]"
    junit_agents(repository, path)
    assert p.audit_agent_variants(repository, path) == []
    tree = ET.parse(path)
    suite = tree.getroot()
    case = next(case for case in suite if case.get("name") == name)
    if fault == "omit":
        suite.remove(case)
    elif fault == "duplicate":
        ET.SubElement(suite, "testcase", name=name)
    else:
        ET.SubElement(case, fault, message="must not qualify")
    tree.write(path)
    assert p.audit_agent_variants(repository, path) == [
        f"agent/fallback variant must pass exactly once: {name}"
    ]


def test_recovery_incidents_retain_their_discriminating_owners(repository):
    value = p.qualification_contract(repository)
    incidents = {row["id"]: row["selectors"] for row in value["incident_cases"]}
    expected = {
        "generator-refresh-review-convergence": ["tests/test_sync_guard_diagnostics.py"],
        "scoped-evidence-repair-atomicity": ["tests/test_scoped_sync_repair.py"],
        "captured-evidence-diagnosis-recovery": [
            "tests/test_captured_evidence_diagnostics.py",
            "tests/test_normalization_diagnostics.py",
            "tests/test_evidence_explanation_query.py",
            "tests/test_evidence_recovery_guidance.py",
        ],
    }
    for incident, selectors in expected.items():
        assert incidents[incident] == selectors
        for selector in selectors:
            group = "defaults" if "recovery_guidance" in selector else "incidents"
            assert selector in value["groups"][group]


def test_shared_driver_runs_only_named_commands_serially_and_retains_all_failures(
    repository, tmp_path, monkeypatch
):
    launcher = tmp_path / "venv/bin/python"
    launcher.parent.mkdir(parents=True)
    launcher.write_bytes(b"launcher spelling preserved")
    output = tmp_path / "attempt"
    calls = []
    monkeypatch.setenv("PYTEST_ADDOPTS", "--ignore=tests")
    monkeypatch.setenv("PYTHONPATH", "/untrusted")

    def run(command, **kwargs):
        calls.append(command)
        assert (
            "PYTEST_ADDOPTS" not in kwargs["env"] and "PYTHONPATH" not in kwargs["env"]
        )
        path = Path(
            next(
                arg.split("=", 1)[1] for arg in command if arg.startswith("--junitxml=")
            )
        )
        suite = ET.Element("testsuite")
        case = ET.SubElement(suite, "testcase", name="independent-case")
        if len(calls) == 1:
            ET.SubElement(case, "failure", message="actionable failure")
        else:
            ET.SubElement(case, "skipped", message="requires native owner")
        path.write_bytes(ET.tostring(suite))
        return SimpleNamespace(returncode=1 if len(calls) == 1 else 0)

    monkeypatch.setattr(p.subprocess, "run", run)
    result = p.run_contract_groups(
        repository, ["inventory", "packet"], output, python=str(launcher)
    )
    assert result["state"] == "failed"
    assert [row["state"] for row in result["groups"]] == ["failed", "blocked"]
    assert result["groups"][1]["skips"] == [{
        "class_name": "", "name": "independent-case", "reason": "requires native owner",
    }]
    assert all(command[0] == str(launcher) for command in calls)
    assert (output / "results.json").is_file() and len(calls) == 2
    before = launcher.read_bytes()
    with pytest.raises(p.ContractError, match="fresh operation-owned"):
        p.run_contract_groups(repository, ["inventory"], output, python=str(launcher))
    with pytest.raises(p.ContractError, match="known, unique"):
        p.run_contract_groups(
            repository,
            ["receipt-supplied-command"],
            tmp_path / "other",
            python=str(launcher),
        )
    assert launcher.read_bytes() == before


@pytest.mark.parametrize("host_platform", ["linux", "win32"])
def test_early_selection_excludes_only_the_intrinsically_macos_case(host_platform):
    rows = p.inapplicable_cases("defaults", host_platform)
    assert rows == [{
        "node_id": "tests/test_wiki_reference_skill.py::TestReferenceSkillProvisioning::test_root_owned_platform_alias_preserves_install_and_export",
        "reason": "root-owned /var alias contract is macOS-only",
        "owner_lane": "core-macos-3.14",
    }]
    assert p.inapplicable_cases("defaults", "darwin") == []
    assert all(p.inapplicable_cases(group, host_platform) == [] for group in p.GROUPS if group != "defaults")


def test_ci_uses_shared_driver_without_replacing_full_producers():
    workflow = (ROOT / p.WORKFLOW).read_text()
    ci = (ROOT / ".github/workflows/ci.yml").read_text()
    assert "${{ runner.temp }}/preflight-contracts/" in ci
    assert (
        "release/preflight_contracts.py check --repo ." in workflow
        and "release/preflight_contracts.py check --repo ." in ci
    )
    assert (
        "--repo . --group inventory --group defaults" in workflow
        and "--repo . --group inventory --group defaults" in ci
    )
    assert "Run strict core suite with canonical coverage" in workflow
    assert "verify-qualification-completion" in workflow
    assert "qualified-release/" in workflow
    assert "release/preflight-contracts.json \\\n" in workflow
