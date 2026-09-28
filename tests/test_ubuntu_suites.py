"""Ubuntu collection, evidence lineage and shadow/cutover safety controls."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest
import yaml

from release import qualification as q
from release import ubuntu_suites as suites

ROOT = Path(__file__).resolve().parents[1]
HARNESS = "b" * 64


def write(path, value):
    q.write_json(path, value)
    return value


def contract():
    return {
        "schema_version": "agent-wiki-ubuntu-suites/v1",
        "profile": suites.PROFILE,
        "pytest_flags": suites.FLAGS,
        "gates": {
            "slow": ["tests/test_cases.py::test_param"],
            "determinism": ["tests/test_cases.py::TestCase::test_method"],
            "security-ubuntu-24.04": ["tests/test_security.py"],
            "product-ubuntu-24.04": ["tests/test_cases.py"],
        },
    }


def xml(path, nodes, *, skipped=None):
    suite = ET.Element("testsuite")
    for node in nodes:
        file, _, tail = node.partition("::")
        # Split class only before the parameter ID, which can contain ::.
        base, bracket, param = tail.partition("[")
        cls, separator, method = base.rpartition("::")
        case = ET.SubElement(
            suite,
            "testcase",
            classname=file[:-3].replace("/", ".") + ("." + cls if separator else ""),
            name=(method if separator else base) + ("[" + param if bracket else ""),
        )
        if skipped == node:
            ET.SubElement(case, "skipped", message="owned skip reason")
    ET.ElementTree(suite).write(path, encoding="utf-8")


@pytest.fixture
def evidence(tmp_path):
    root = tmp_path / "union"
    root.mkdir()
    reg = tmp_path / "registry.json"
    write(reg, contract())
    identity = write(
        root / "identity.json",
        {
            "schema_version": q.IDENTITY_SCHEMA,
            "repository": "owned/repo",
            "source": {
                "sha": "a" * 40,
                "tree": "c" * 40,
                "archive_sha256": "d" * 64,
                "commit_epoch": 1,
            },
            "version": "1.0.0",
            "tag": "v1.0.0",
            "mode": "candidate",
        },
    )
    nodes = [
        "tests/test_cases.py::test_param[a*?]",
        "tests/test_cases.py::test_param[a::b/[x]]",
        "tests/test_cases.py::TestCase::test_method[one]",
        "tests/test_cases.py::test_param_extra",
        "tests/test_security.py::test_unique",
    ]
    inventory = suites.resolve(nodes, contract())
    write(root / "inventory.json", inventory)
    write(root / "observed.json", inventory)
    write(root / "started.json", inventory["union"])
    write(root / "registry.json", contract())
    xml(root / "union.xml", inventory["union"], skipped=nodes[-1])
    execution = {
        "schema_version": suites.SCHEMA,
        "purpose": "shadow",
        "complete": True,
        "mode": "union",
        "identity": identity,
        "identity_sha256": q.sha256_file(root / "identity.json"),
        "harness_sha256": HARNESS,
        "registry_sha256": q.sha256_file(reg),
        "environment": {
            "profile": suites.PROFILE,
            "python": "3.13.7",
            "machine": "x86_64",
            "runner_image": "owned-fixture",
            "packages": {
                "agent-wiki-cli": "1.0.0",
                "pytest": "8.4.2",
                "pytest-cov": "7.0.0",
            },
        },
        "runs": {
            "collection": {"exit_code": 0, "seconds": 1.0},
            "union": {"exit_code": 0, "seconds": 2.0},
        },
        "setup_seconds": 1.0,
        "execution_seconds": 3.0,
        "files": {p.name: q.sha256_file(p) for p in root.iterdir()},
    }
    write(root / "execution.json", execution)
    for lane in suites.LANES:
        suites.projection(root, lane, root / "identity.json", inventory, execution)
    write(root / "projection-timing.json", {"seconds": 0.1})
    return root, reg, identity


def reseal(root):
    """Adversarial producer updates digests, so semantics must still be checked."""
    execution = q.load_json(root / "execution.json")
    execution["files"] = {
        name: q.sha256_file(root / name) for name in execution["files"]
    }
    write(root / "execution.json", execution)
    inventory = q.load_json(root / "inventory.json")
    for lane in suites.LANES:
        suites.projection(root, lane, root / "identity.json", inventory, execution)


def test_registry_preserves_the_legacy_selectors_and_freezes_all_helpers():
    import shlex

    value = suites.registry(ROOT / "release/ubuntu-suites.json")
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/release-qualification.yml").read_text()
    )
    # The remaining platform consumers still select the original complete
    # security/product suites. Ubuntu uses the same registry for both modes.
    jobs = workflow["jobs"]
    security = next(
        step["run"]
        for step in jobs["security-behavior"]["steps"]
        if "python -m pytest" in step.get("run", "")
    )
    assert [
        token
        for token in shlex.split(security.replace("\\\n", " "))
        if token.startswith("tests/")
    ] == value["gates"]["security-ubuntu-24.04"]
    for gate in ["security", "product"]:
        command = next(
            step["run"]
            for step in jobs["core-windows"]["steps"]
            if f"--target-lane {gate}-windows-2025" in step.get("run", "")
        )
        tokens = shlex.split(command.replace("\\\n", " "))
        selected = [
            tokens[i + 1] for i, token in enumerate(tokens) if token == "--selector"
        ]
        assert selected == value["gates"][f"{gate}-ubuntu-24.04"]
    assert value["gates"]["slow"] == [
        "tests/test_knowledge_hardening.py::test_representative_knowledge_generation_stays_deterministic_and_within_budget"
    ]
    assert len(value["gates"]["determinism"]) == 10
    assert (
        len(
            [
                s
                for s in value["gates"]["determinism"]
                if s.startswith("tests/test_context.py::")
            ]
        )
        == 2
    )
    freeze = next(
        s["run"]
        for s in workflow["jobs"]["freeze"]["steps"]
        if s.get("id") == "harness"
    )
    assert all(
        "release/" + name in freeze
        for name in [
            "ubuntu_suites.py",
            "ubuntu_shadow.py",
            "hosted_evidence.py",
            "ubuntu-suites.json",
            "qualification.py",
        ]
    )


@pytest.mark.parametrize(
    "selector",
    [
        "../tests/test_a.py",
        "tests/../test_a.py",
        "tests//test_a.py",
        "tests/test_a.py::",
        "tests/test_a.py::TestCase",
        "tests/test_a.py::test_x[",
        "tests/test_*.py::test_x",
        "tests/test_a.py::test_x\n",
        "tests/test_a.py::test_*",
    ],
)
def test_unsafe_or_ambiguous_selectors_fail(selector):
    with pytest.raises(q.QualificationError, match="selector"):
        q._canonical_junit_selector(selector)


@pytest.mark.parametrize(
    "parameter",
    ["a*?", "a::b/[x]", "../other", "", "two words", "[one][two]", r"C:\path"],
)
def test_parameter_ids_are_literal_in_exact_and_family_selection(parameter):
    base = "tests/test_cases.py::TestCase::test_method"
    node = f"{base}[{parameter}]"
    assert q._canonical_junit_selector(node) == node
    assert q._selector_matches(base, node)
    assert q._selector_matches(node, node)
    assert not q._selector_matches(node, f"{base}[different]")
    assert not q._selector_matches(base, base + "_extra")


def test_inventory_deduplicates_membership_and_retains_unique_nonproduct_nodes(
    evidence,
):
    root, _, _ = evidence
    value = q.load_json(root / "inventory.json")
    assert len(value["union"]) == 5
    assert sum(map(len, value["gates"].values())) == 8
    assert value["membership"]["tests/test_security.py::test_unique"] == [
        "security-ubuntu-24.04"
    ]
    assert value == suites.resolve(list(reversed(value["collected"])), contract())
    with pytest.raises(suites.q.QualificationError, match="duplicate"):
        suites.resolve(value["collected"] * 2, contract())
    with pytest.raises(suites.q.QualificationError, match="no collected"):
        suites.resolve(
            [n for n in value["collected"] if "security" not in n], contract()
        )


def test_union_roundtrip_retains_literal_nodes_and_skip_reason(evidence):
    root, reg, identity = evidence
    suites.validate_execution(root, identity, HARNESS, reg)
    receipt = q.load_json(root / "slow-projection.json")
    assert receipt["selected_node_ids"] == [
        "tests/test_cases.py::test_param[a*?]",
        "tests/test_cases.py::test_param[a::b/[x]]",
    ]
    assert suites.outcomes(root / "security-ubuntu-24.04.xml")[
        "tests/test_security.py::test_unique"
    ] == {"outcome": "skipped", "reason": "owned skip reason"}


@pytest.mark.parametrize(
    "mutation",
    [
        "candidate",
        "harness",
        "registry",
        "environment",
        "xml",
        "duplicate-xml",
        "missing-xml",
        "failure-xml",
        "partial",
        "process-failure",
        "missing-run",
        "observed",
        "double-start",
        "missing-start",
        "inventory-widened",
        "projection",
        "receipt",
        "receipt-source",
        "receipt-count",
        "receipt-nodes",
        "receipt-environment",
        "missing-projection",
    ],
)
def test_substituted_or_incomplete_evidence_cannot_pass(evidence, mutation):
    root, reg, identity = evidence
    execution = q.load_json(root / "execution.json")
    if mutation == "candidate":
        identity = deepcopy(identity)
        identity["source"]["sha"] = "f" * 40
    elif mutation == "harness":
        execution["harness_sha256"] = "f" * 64
    elif mutation == "registry":
        changed = contract()
        changed["gates"]["slow"] = ["tests/test_cases.py"]
        write(reg, changed)
    elif mutation == "environment":
        execution["environment"]["packages"]["mcp"] = "1.0"
    elif mutation == "partial":
        execution["complete"] = False
    elif mutation == "process-failure":
        execution["runs"]["union"]["exit_code"] = 1
    elif mutation == "missing-run":
        del execution["runs"]["union"]
    write(root / "execution.json", execution)
    if mutation in {"xml", "duplicate-xml", "missing-xml", "failure-xml"}:
        tree = ET.parse(root / "union.xml")
        cases = list(tree.getroot())
        if mutation == "xml":
            cases[0].set("name", "test_substituted")
        elif mutation == "duplicate-xml":
            tree.getroot().append(deepcopy(cases[0]))
        elif mutation == "missing-xml":
            tree.getroot().remove(cases[0])
        else:
            ET.SubElement(cases[0], "failure")
        tree.write(root / "union.xml")
        # Rehash source to require node/outcome checks, not just digest checks.
        execution["files"]["union.xml"] = q.sha256_file(root / "union.xml")
        write(root / "execution.json", execution)
    elif mutation in {"double-start", "missing-start"}:
        starts = q.load_json(root / "started.json")
        write(
            root / "started.json",
            starts + starts[:1] if mutation == "double-start" else starts[1:],
        )
        reseal(root)
    elif mutation in {"observed", "inventory-widened"}:
        name = "observed.json" if mutation == "observed" else "inventory.json"
        value = q.load_json(root / name)
        value["gates"]["slow"].append("tests/test_cases.py::test_param_extra")
        write(root / name, value)
        reseal(root)
    elif mutation == "projection":
        (root / "slow.xml").write_text((root / "product-ubuntu-24.04.xml").read_text())
    elif mutation.startswith("receipt"):
        path = root / "slow-projection.json"
        receipt = q.load_json(path)
        if mutation == "receipt":
            receipt = q.load_json(root / "determinism-projection.json")
        elif mutation == "receipt-source":
            receipt["source_junit_sha256"] = "f" * 64
        elif mutation == "receipt-count":
            receipt["counts"]["source"] += 1
        elif mutation == "receipt-nodes":
            receipt["selected_node_ids"].append("tests/test_cases.py::test_param_extra")
        else:
            receipt["lineage"]["environment_sha256"] = "f" * 64
        write(path, receipt)
    elif mutation == "missing-projection":
        (root / "slow.xml").unlink()
    with pytest.raises((suites.q.QualificationError, OSError)):
        suites.validate_execution(root, identity, HARNESS, reg)


def legacy_for(root, reg, identity):
    original = q.load_json(root / "execution.json")
    groups = [
        ("slow", "determinism"),
        ("security-ubuntu-24.04",),
        ("product-ubuntu-24.04",),
    ]
    result = []
    for number, lanes in enumerate(groups):
        directory = root.parent / f"legacy-{number}"
        directory.mkdir()
        for name in (
            "identity.json",
            "registry.json",
            *(lane + ".xml" for lane in lanes),
        ):
            (directory / name).write_bytes((root / name).read_bytes())
        receipt = deepcopy(original)
        receipt.update(
            mode="legacy",
            runs={lane: {"exit_code": 0, "seconds": 1.0} for lane in lanes},
            files={p.name: q.sha256_file(p) for p in directory.iterdir()},
        )
        write(directory / "execution.json", receipt)
        result.append(directory)
    allowlist = root.parent / "allowlist.json"
    write(allowlist, {"schema_version": q.ALLOWLIST_SCHEMA, "entries": []})
    return argparse.Namespace(
        identity=root / "identity.json",
        union=root,
        legacy=result,
        harness_sha256=HARNESS,
        registry=reg,
        allowlist=allowlist,
        output=root.parent / "comparison.json",
    )


def test_shadow_comparison_is_complete_but_never_qualifying(evidence):
    root, reg, identity = evidence
    args = legacy_for(root, reg, identity)
    assert suites.compare(args) == 0
    result = q.load_json(args.output)
    assert result["qualifying"] is False
    assert result["unique_nodes"] == 5 and result["legacy_executions"] == 8
    assert len(result["legacy_execution_sha256"]) == 3


def test_historical_execution_remains_auditable_but_cannot_qualify(evidence):
    root, reg, identity = evidence
    receipt = q.load_json(root / "execution.json")
    receipt["schema_version"] = suites.LEGACY_SCHEMA
    receipt.pop("purpose")
    write(root / "execution.json", receipt)
    reseal(root)
    suites.validate_execution(root, identity, HARNESS, reg, purpose="shadow")
    with pytest.raises(suites.q.QualificationError, match="purpose differs"):
        suites.validate_execution(root, identity, HARNESS, reg, purpose="qualification")


def test_qualifying_execution_cannot_be_used_in_a_shadow_comparison(evidence):
    root, reg, identity = evidence
    args = legacy_for(root, reg, identity)
    receipt = q.load_json(root / "execution.json")
    receipt["purpose"] = "qualification"
    write(root / "execution.json", receipt)
    reseal(root)
    suites.validate_execution(root, identity, HARNESS, reg, purpose="qualification")
    with pytest.raises(suites.q.QualificationError, match="purpose differs"):
        suites.compare(args)


@pytest.mark.parametrize("purpose", [None, [], {}, False, "", "qualifying"])
def test_malformed_execution_purpose_cannot_qualify(evidence, purpose):
    root, reg, identity = evidence
    receipt = q.load_json(root / "execution.json")
    receipt["purpose"] = purpose
    write(root / "execution.json", receipt)
    with pytest.raises(suites.q.QualificationError, match="purpose"):
        suites.validate_execution(root, identity, HARNESS, reg, purpose="qualification")


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "package-drift",
        "skip-reason",
        "unexpected-skip",
        "missing-test",
        "owner-skip",
    ],
)
def test_shadow_rejects_inequivalence_and_missing_ownership(evidence, mutation):
    root, reg, identity = evidence
    args = legacy_for(root, reg, identity)
    if mutation == "missing":
        args.legacy.pop()
    elif mutation == "duplicate":
        args.legacy.append(args.legacy[0])
    elif mutation == "package-drift":
        receipt = q.load_json(args.legacy[0] / "execution.json")
        receipt["environment"]["packages"]["pytest"] = "9.0.0"
        write(args.legacy[0] / "execution.json", receipt)
    elif mutation == "owner-skip":
        write(
            args.allowlist,
            {
                "schema_version": q.ALLOWLIST_SCHEMA,
                "entries": [
                    {
                        "lane": "core-windows-3.13",
                        "node_id": "tests/test_security.py::test_unique",
                        "reason": "platform",
                        "owner_lane": "security-ubuntu-24.04",
                    }
                ],
            },
        )
    else:
        directory = args.legacy[1] if mutation == "skip-reason" else args.legacy[0]
        lane = "security-ubuntu-24.04" if mutation == "skip-reason" else "slow"
        tree = ET.parse(directory / f"{lane}.xml")
        case = next(tree.getroot().iter("testcase"))
        if mutation == "skip-reason":
            skip = case.find("skipped")
            assert skip is not None
            skip.set("message", "changed reason")
        elif mutation == "unexpected-skip":
            ET.SubElement(case, "skipped", message="lost coverage")
        else:
            case.set("name", "test_other")
        tree.write(directory / f"{lane}.xml")
        receipt = q.load_json(directory / "execution.json")
        receipt["files"][lane + ".xml"] = q.sha256_file(directory / f"{lane}.xml")
        write(directory / "execution.json", receipt)
    with pytest.raises(suites.q.QualificationError):
        suites.compare(args)
    diagnostic = q.load_json(args.output)
    assert diagnostic["passed"] is False and diagnostic["qualifying"] is False
    assert diagnostic["errors"]


def test_real_pytest_collection_and_execution_preserve_parameter_families(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tests / "test_cases.py").write_text("""import pytest
@pytest.mark.parametrize("value", [1, 2], ids=["a*?", "a::b/[x]"])
def test_param(value):
    assert value
class TestCase:
    def test_method(self):
        assert True
def test_param_extra():
    assert True
""")
    (tests / "test_security.py").write_text("def test_unique():\n    assert True\n")
    reg = tmp_path / "registry.json"
    write(reg, contract())
    command = [
        sys.executable,
        "-I",
        str(ROOT / "release/ubuntu_suites.py"),
        "worker",
        "--registry",
        str(reg),
    ]
    inventory = tmp_path / "inventory.json"
    run = subprocess.run(
        command + ["--collect", "--observed", str(inventory)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    observed = tmp_path / "observed.json"
    started = tmp_path / "started.json"
    junit = tmp_path / "union.xml"
    run = subprocess.run(
        command
        + [
            "--inventory",
            str(inventory),
            "--observed",
            str(observed),
            "--started",
            str(started),
            "--junit",
            str(junit),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    expected = q.load_json(inventory)
    assert len(expected["union"]) == 5
    assert q.load_json(observed) == expected
    assert sorted(q.load_json(started)) == expected["union"]
    assert sorted(suites.outcomes(junit)) == expected["union"]
    # A future file matched by a registry glob is collected automatically.
    updated = contract()
    updated["gates"]["product-ubuntu-24.04"] = ["tests/test_*.py"]
    write(reg, updated)
    (tests / "test_new.py").write_text("def test_added():\n    assert True\n")
    run = subprocess.run(
        command + ["--collect", "--observed", str(observed)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "tests/test_new.py::test_added" in q.load_json(observed)["union"]
    run = subprocess.run(
        command
        + [
            "--inventory",
            str(inventory),
            "--observed",
            str(observed),
            "--started",
            str(started),
            "--junit",
            str(junit),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert run.returncode != 0
    assert "differs from frozen inventory" in run.stdout + run.stderr


@pytest.mark.parametrize("status", ["failure", "cancelled", "skipped", "", "unknown"])
def test_owner_consumer_rejects_unsuccessful_union_even_with_good_xml(evidence, status):
    root, reg, identity = evidence
    args = argparse.Namespace(
        identity=root / "identity.json",
        allowlist=root.parent / "allowlist.json",
        owner_result=[],
        owner_junit=[],
        ubuntu_union=root,
        ubuntu_union_result=status,
        harness_sha256=HARNESS,
    )
    write(args.allowlist, {"schema_version": q.ALLOWLIST_SCHEMA, "entries": []})
    with pytest.raises(q.QualificationError, match="producer did not pass"):
        q.verify_owner_lanes(args)


def test_bundle_consumers_reject_shadow_even_if_all_gate_statuses_claim_pass(evidence):
    root, _, _ = evidence
    with pytest.raises(q.QualificationError, match="shadow evidence"):
        q.build_bundle(argparse.Namespace(evidence=[f"RD-03:union={root}"]))
    with pytest.raises(q.QualificationError, match="shadow evidence"):
        q._reject_shadow_evidence(root)


def test_existing_execution_directory_is_never_reused(evidence):
    root, _, _ = evidence
    with pytest.raises(suites.q.QualificationError, match="stale evidence"):
        suites.execute(argparse.Namespace(root=root.parent, output=root))


def test_shadow_workflow_uses_one_runner_and_preserves_platform_consumers():
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/release-qualification.yml").read_text()
    )
    trigger = workflow.get("on", workflow.get(True))
    assert (
        trigger["workflow_dispatch"]["inputs"]["ubuntu-suite-shadow"]["default"]
        is False
    )
    jobs = workflow["jobs"]
    shadow = jobs["ubuntu-shadow"]
    assert shadow["runs-on"] == "ubuntu-24.04" and shadow["needs"] == "freeze"
    text = "\n".join(str(step) for step in shadow["steps"])
    assert "ubuntu_shadow.py" in text and "--harness-sha256" in text
    assert "python-version" in text and "3.13" in text
    assert "[dev,tokens]" not in text and "[dev,mcp]" not in text
    assert "!inputs.ubuntu-suite-shadow" in jobs["ubuntu-suites"]["if"]
    assert not {"slow", "product", "shadow-security-macos"} & jobs.keys()
    assert jobs["security-behavior"]["strategy"]["matrix"]["os"] == ["macos-15"]
    assert "inputs.ubuntu-suite-shadow" not in jobs["security-behavior"]["if"]
    assert "ubuntu-union" not in jobs and "ubuntu-comparison" not in jobs
    artifacts = {
        step["with"]["name"]: step
        for step in shadow["steps"]
        if str(step.get("uses", "")).startswith("actions/upload-artifact@")
    }
    assert set(artifacts) == {
        "evidence-rd-03",
        "evidence-rd-04-ubuntu-24.04",
        "evidence-rd-05-ubuntu-24.04",
        "evidence-ubuntu-union",
        "ubuntu-shadow-comparison",
    }
    assert all("always()" in step["if"] for step in artifacts.values())
    assert artifacts["ubuntu-shadow-comparison"]["with"]["path"].endswith(
        "/diagnostics"
    )
    assert artifacts["ubuntu-shadow-comparison"]["with"]["if-no-files-found"] == "error"
    owners = jobs["owner-lanes"]
    assert {"ubuntu-shadow", "security-behavior"} <= set(owners["needs"])
    shadow_owner = next(
        step["run"]
        for step in owners["steps"]
        if step.get("name") == "Verify shadow union owners against hosted lane results"
    )
    for lane in suites.LANES:
        assert (
            f'--owner-junit "{lane}=incoming/owner-evidence/evidence-ubuntu-union/{lane}.xml"'
            in shadow_owner
        )
        assert (
            f'--owner-result "{lane}=${{{{ needs.ubuntu-shadow.result }}}}"'
            in shadow_owner
        )
    assert (
        '--owner-result "security-macos-15=${{ needs.security-behavior.result }}"'
        in shadow_owner
    )
    assert (
        '--owner-result "security-windows-2025=${{ needs.core-windows.result }}"'
        in shadow_owner
    )
    assert (
        "--ubuntu-union-result" in shadow_owner and "--harness-sha256" in shadow_owner
    )
    for job_name in ["bundle", "decision"]:
        assert "!inputs.ubuntu-suite-shadow" in jobs[job_name]["if"]
    assert "${{ inputs.ubuntu-suite-shadow }}" in workflow["concurrency"]["group"]


@pytest.mark.parametrize("ubuntu", ["success", "failure", "skipped", "cancelled", ""])
@pytest.mark.parametrize("macos", ["success", "failure", "skipped", "cancelled", ""])
@pytest.mark.parametrize("windows", ["success", "failure", "skipped", "cancelled", ""])
def test_multiplatform_gate_requires_every_obligation(tmp_path, ubuntu, macos, windows):
    args = argparse.Namespace(
        gate=[f"RD-04={ubuntu}"],
        gate_dependency=[f"RD-04={macos}", f"RD-04={windows}"],
        candidate_sha="a" * 40,
        candidate_version="1.0.0",
        output=tmp_path / "decision.json",
        allow_non_go_exit_zero=True,
    )
    q.aggregate(args)
    result = q.load_json(args.output)["gates"]["RD-04"]
    expected = (
        "FAIL"
        if "failure" in (ubuntu, macos, windows)
        else "PASS"
        if (ubuntu, macos, windows) == ("success",) * 3
        else "BLOCKED"
    )
    assert result == expected


def test_gate_dependency_must_reference_an_explicit_gate(tmp_path):
    with pytest.raises(q.QualificationError, match="dependency"):
        q.aggregate(
            argparse.Namespace(
                gate=["RD-03=success"], gate_dependency=["RD-04=success"]
            )
        )


@pytest.fixture
def production_evidence(evidence):
    root, reg, identity = evidence
    frozen_registry = ROOT / "release/ubuntu-suites.json"
    value = suites.registry(frozen_registry)
    nodes = set()
    for selectors in value["gates"].values():
        for selector in selectors:
            node = selector.replace("*", "example").replace("?", "x")
            nodes.add(node if "::" in node else node + "::test_example")
    inventory = suites.resolve(sorted(nodes), value)
    write(root / "registry.json", value)
    for name in ["inventory.json", "observed.json"]:
        write(root / name, inventory)
    write(root / "started.json", inventory["union"])
    xml(root / "union.xml", inventory["union"])
    execution = q.load_json(root / "execution.json")
    execution["registry_sha256"] = q.sha256_file(frozen_registry)
    write(root / "execution.json", execution)
    reseal(root)
    return root, identity


def test_owner_consumer_validates_real_frozen_registry_and_all_projection_paths(
    production_evidence,
):
    root, identity = production_evidence
    allowlist = root.parent / "allowlist.json"
    inventory = q.load_json(root / "inventory.json")
    owned_node = inventory["gates"]["slow"][0]
    write(
        allowlist,
        {
            "schema_version": q.ALLOWLIST_SCHEMA,
            "entries": [
                {
                    "lane": "core-windows-3.13",
                    "node_id": owned_node,
                    "reason": "platform",
                    "owner_lane": "slow",
                }
            ],
        },
    )
    args = argparse.Namespace(
        identity=root / "identity.json",
        allowlist=allowlist,
        owner_result=[f"{lane}=success" for lane in suites.LANES],
        owner_junit=[f"{lane}={root / (lane + '.xml')}" for lane in suites.LANES],
        ubuntu_union=root,
        ubuntu_union_result="success",
        harness_sha256=HARNESS,
        output=root.parent / "owner.json",
    )
    assert q.verify_owner_lanes(args) == 0
    receipt = q.load_json(args.output)
    assert receipt["owner_results"]["slow"]["verified_node_ids"] == [owned_node]
    assert receipt["ubuntu_union"]["execution_sha256"] == q.sha256_file(
        root / "execution.json"
    )
    # Matching XML bytes at a different path are not the validated projection.
    replacement = root.parent / "replacement.xml"
    replacement.write_bytes((root / "slow.xml").read_bytes())
    args.owner_junit[0] = f"slow={replacement}"
    with pytest.raises(q.QualificationError, match="substituted"):
        q.verify_owner_lanes(args)
    args.owner_junit[0] = f"slow={root / 'slow.xml'}"
    (root / "slow-projection.json").write_text("{}")
    with pytest.raises(q.QualificationError, match="lineage"):
        q.verify_owner_lanes(args)


def test_union_process_failure_preserves_diagnostics_and_emits_no_projections(
    tmp_path, monkeypatch
):
    reg = tmp_path / "registry.json"
    write(reg, contract())
    args = argparse.Namespace(
        root=tmp_path,
        output=tmp_path / "failed",
        mode="union",
        registry=reg,
        setup_started=0,
    )
    monkeypatch.setattr(suites, "context", lambda _: {"identity": {"owned": True}})

    def failure(command, root, log):
        log.write_text("owned collection failure")
        return {"exit_code": 2, "seconds": 0.01}

    monkeypatch.setattr(suites, "invoke", failure)
    assert suites.execute(args) == 1
    assert (args.output / "collection.log").read_text() == "owned collection failure"
    receipt = q.load_json(args.output / "execution.json")
    assert receipt["complete"] is False
    assert receipt["runs"]["collection"]["exit_code"] == 2
    assert not list(args.output.glob("*-projection.json"))


def test_timeout_retains_partial_log_and_nonpassing_exit(tmp_path, monkeypatch):
    def timeout(command, **kwargs):
        assert (
            kwargs["stdin"] == subprocess.DEVNULL
            and kwargs["timeout"] == suites.TIMEOUT
        )
        kwargs["stdout"].write(b"partial diagnostic")
        raise subprocess.TimeoutExpired(command, suites.TIMEOUT)

    monkeypatch.setattr(suites.subprocess, "run", timeout)
    log = tmp_path / "timeout.log"
    result = suites.invoke([sys.executable, "-c", "pass"], tmp_path, log)
    assert result["exit_code"] == 124
    assert log.read_text() == "partial diagnostic"


def test_legacy_shadow_receipts_cannot_be_used_as_qualifying_evidence(evidence):
    root, reg, identity = evidence
    args = legacy_for(root, reg, identity)
    for legacy in args.legacy:
        with pytest.raises(q.QualificationError, match="shadow evidence"):
            q.build_bundle(argparse.Namespace(evidence=[f"RD-03:legacy={legacy}"]))


def test_source_union_projection_is_rejected_even_if_execution_receipt_is_removed(
    evidence,
):
    root, _, _ = evidence
    (root / "execution.json").unlink()
    with pytest.raises(q.QualificationError, match="shadow evidence"):
        q._reject_shadow_evidence(root)


@pytest.mark.parametrize(
    "mutation",
    ["counter-map", "unexpected-run-field", "unexpected-field", "boolean-exit"],
)
def test_rehashed_malformed_execution_shapes_are_rejected(evidence, mutation):
    root, reg, identity = evidence
    execution = q.load_json(root / "execution.json")
    if mutation == "counter-map":
        write(
            root / "started.json",
            {node: 1 for node in q.load_json(root / "started.json")},
        )
    elif mutation == "unexpected-run-field":
        execution["runs"]["union"]["cancelled"] = True
    elif mutation == "unexpected-field":
        execution["qualifying"] = True
    else:
        execution["runs"]["union"]["exit_code"] = False
    write(root / "execution.json", execution)
    reseal(root)
    with pytest.raises(suites.q.QualificationError):
        suites.validate_execution(root, identity, HARNESS, reg)


def test_runner_image_drift_leaves_a_failed_diagnostic_with_exact_differences(evidence):
    root, reg, identity = evidence
    args = legacy_for(root, reg, identity)
    path = args.legacy[0] / "execution.json"
    receipt = q.load_json(path)
    receipt["environment"]["runner_image"] = "different-image"
    write(path, receipt)
    with pytest.raises(suites.q.QualificationError, match="environments differ"):
        suites.compare(args)
    diagnostic = q.load_json(args.output)
    assert diagnostic["passed"] is False and diagnostic["complete"] is False
    assert diagnostic["stage"] == "environment-comparison"
    assert diagnostic["environment_differences"] == {
        args.legacy[0].name: {
            "runner_image": {"union": "owned-fixture", "legacy": "different-image"}
        }
    }
    with pytest.raises(q.QualificationError, match="shadow evidence"):
        q._reject_shadow_evidence(args.output)


@pytest.mark.parametrize("status", ["failure", "cancelled", "skipped", "unknown"])
def test_failed_producer_cannot_be_hidden_by_passing_receipts(evidence, status):
    root, reg, identity = evidence
    args = legacy_for(root, reg, identity)
    args.producer_result = [
        f"{name}={status if name == 'union' else 'success'}"
        for name in suites.SHADOW_PRODUCERS
    ]
    with pytest.raises(suites.q.QualificationError, match="producers"):
        suites.compare(args)
    receipt = q.load_json(args.output)
    assert (
        receipt["stage"] == "producer-status"
        and receipt["producer_results"]["union"] == status
    )
    assert receipt["passed"] is False


def test_missing_or_corrupt_evidence_still_produces_comparison_diagnostics(evidence):
    root, reg, identity = evidence
    args = legacy_for(root, reg, identity)
    (root / "union.xml").unlink()
    with pytest.raises(OSError):
        suites.compare(args)
    receipt = q.load_json(args.output)
    assert receipt["stage"] == "union-validation" and receipt["errors"]
    assert receipt["passed"] is False


def test_comparison_diagnostic_cannot_overwrite_its_inputs(evidence):
    root, reg, identity = evidence
    args = legacy_for(root, reg, identity)
    args.output = root / "execution.json"
    before = args.output.read_bytes()
    with pytest.raises(suites.q.QualificationError, match="separate"):
        suites.compare(args)
    assert args.output.read_bytes() == before


@pytest.mark.parametrize("field", ["machine", "runner_image"])
@pytest.mark.parametrize("value", [None, False, 0, [], {}, "", " \t\n"])
def test_malformed_environment_metadata_is_rejected_even_when_all_producers_agree(
    evidence, field, value
):
    root, reg, identity = evidence
    execution = q.load_json(root / "execution.json")
    execution["environment"][field] = value
    write(root / "execution.json", execution)
    reseal(root)
    args = legacy_for(root, reg, identity)
    with pytest.raises(suites.q.QualificationError, match=f"environment {field}"):
        suites.compare(args)
    assert q.load_json(args.output)["passed"] is False
