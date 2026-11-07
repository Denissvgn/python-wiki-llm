"""Exercise isolated provider and consumer policy boundaries of the impact action."""

from __future__ import annotations

import ast
from fnmatch import fnmatchcase
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap
import venv

import pytest
import yaml


ROOT = Path(__file__).parents[1]
ACTION_PATH = ROOT / "integrations/wiki-impact/action.yml"


def test_root_pilot_maps_both_upgrade_topics_and_leaves_cli_discovery_open():
    from llm_wiki_cli.services.publication_config import load_publication_config

    config = load_publication_config(ROOT)
    assert config["architecture"] == {
        "baseline": "existing-wiki",
        "root": "docs/llm_wiki",
    }
    assert config["target"] == {"kind": "github-wiki", "repository": "self"}
    assert config["enforcement"] == "advisory" and config["publish"] is False
    assert {(topic["wiki_page"], topic["anchor"]) for topic in config["topics"]} == {
        ("Command-Reference.md", "upgrade"),
        ("Migration-and-Upgrades.md", "upgrade-framework-artifacts"),
        ("Command-Reference.md", "command-reference"),
    }
    expected = {"flows/cli-upgrade.md", "workflows/upgrade_current_knowledge.md"}
    for topic in config["topics"]:
        if topic["id"] == "command-reference.commands":
            assert topic["depends_on"] == [{"reference": "llm-wiki", "command": []}]
            continue
        assert topic["owner"] == "maintainers" and topic["edit_at"] == "wiki"
        assert {
            dependency["architecture_page"]
            for dependency in topic["depends_on"]
            if "architecture_page" in dependency
        } == expected
        assert {"reference": "llm-wiki", "command": ["upgrade"]} in topic["depends_on"]
        assert all((ROOT / "docs/llm_wiki" / path).is_file() for path in expected)
    patterns = [exclusion["pattern"] for exclusion in config["exclusions"]]
    assert all(exclusion["reason"] for exclusion in config["exclusions"])
    assert any(
        fnmatchcase("workflows/upgrade_current_knowledge.md", pattern)
        for pattern in patterns
    )
    assert not any(
        fnmatchcase("flows/cli-new-command.md", pattern) for pattern in patterns
    )


def test_root_workflow_is_manual_read_only_and_uses_the_local_provider():
    path = ROOT / ".github/workflows/sibling-wiki-impact.yml"
    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert set(workflow["on"]) == {"workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read"}
    job = workflow["jobs"]["report"]
    assert job["permissions"] == {"contents": "read"}
    checkout = next(
        step
        for step in job["steps"]
        if step.get("uses", "").startswith("actions/checkout@")
    )
    assert checkout["with"]["ref"] == "${{ github.sha }}"
    assert checkout["with"]["persist-credentials"] is False
    action = next(
        step
        for step in job["steps"]
        if step.get("uses") == "./integrations/wiki-impact"
    )
    assert action["with"] == {
        "config": ".llm-wiki/publication.json",
        "baseline": "${{ inputs.baseline }}",
        "reviews": "${{ inputs.reviews }}",
        "target-dir": "sibling-wiki",
        "fail-on": "error",
    }
    clone = next(step for step in job["steps"] if "run" in step)
    assert clone["env"]["REPOSITORY"] == "${{ github.repository }}"
    assert clone["env"]["ACCEPTED_BASELINE"] == "${{ inputs.baseline }}"
    assert clone["env"]["ACCEPTED_REVIEWS"] == "${{ inputs.reviews }}"
    assert "${{" not in clone["run"]
    assert '"${SERVER_URL}/${REPOSITORY}.wiki.git" sibling-wiki' in clone["run"]
    assert "snapshot evidence" in job["name"]
    assert "secrets." not in path.read_text(encoding="utf-8")


def test_consumer_example_reads_accepted_state_from_an_exact_base_checkout():
    readme = (ACTION_PATH.parent / "README.md").read_text(encoding="utf-8")
    example = readme.split("```yaml\n", 1)[1].split("```", 1)[0]
    workflow = yaml.safe_load(example)
    steps = workflow["jobs"]["impact"]["steps"]
    checkouts = [
        step for step in steps if step.get("uses", "").startswith("actions/checkout@")
    ]
    assert checkouts[0]["with"]["path"] == "consumer"
    accepted = checkouts[1]["with"]
    assert accepted["ref"] == "${{ github.event.pull_request.base.sha || github.sha }}"
    assert accepted["path"] == "accepted-state"
    assert all(step["with"]["persist-credentials"] is False for step in checkouts)
    action = next(
        step for step in steps if "/integrations/wiki-impact@" in step.get("uses", "")
    )
    assert action["with"]["working-directory"] == "consumer"
    assert (
        action["with"]["baseline"]
        == "${{ github.workspace }}/accepted-state/.llm-wiki/publication-baseline.json"
    )
    assert (
        action["with"]["reviews"]
        == "${{ github.workspace }}/accepted-state/.llm-wiki/publication-reviews.json"
    )


def _script(step_id: str) -> str:
    action = yaml.safe_load(ACTION_PATH.read_text(encoding="utf-8"))
    step = next(step for step in action["runs"]["steps"] if step.get("id") == step_id)
    return step["run"].split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]


def _run(
    script: str,
    *,
    cwd: Path,
    environment: dict[str, str],
    executable: Path | None = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(executable or sys.executable), "-I", "-c", script],
        cwd=cwd,
        env={**os.environ, **environment},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def _report(*, complete=True, review=False) -> dict:
    from llm_wiki_cli.services.knowledge_evidence import hash_json

    findings = []
    coverage = {"total": 0, "mapped": 0, "excluded": 0, "unmapped": 0}
    if not complete:
        finding = {
            "kind": "topic",
            "subject": "accounts",
            "status": "incomplete",
            "reasons": [{"kind": "target-unresolved-anchor"}],
            "owner": "maintainers",
            "wiki_page": "Accounts.md",
            "anchor": "accounts",
            "edit_at": "wiki",
            "target": {"state": "unresolved-anchor", "hash": None},
            "review_basis": hash_json("review basis"),
        }
        findings.append({**finding, "id": hash_json(finding)})
    elif review:
        finding = {
            "kind": "coverage",
            "subject": "guides/accounts.md",
            "status": "unmapped",
            "reasons": [
                {
                    "kind": "architecture-page-unmapped",
                    "action": "Map or exclude the page",
                }
            ],
        }
        findings.append({**finding, "id": hash_json(finding)})
        coverage.update(total=1, unmapped=1)
    report = {
        "schema_version": "llm-wiki-publication-impact/v1",
        "complete": complete,
        "review_required": review,
        "changed": True,
        "ready": complete and not review,
        "findings": findings,
        "coverage": coverage,
        "basis": {
            "baseline": hash_json("baseline"),
            "candidate": hash_json("candidate"),
        },
        "config_hash": hash_json("configuration"),
        "enforcement": "advisory",
        "limitations": [],
    }
    return {**report, "report_id": hash_json(report)}


@pytest.mark.parametrize(
    "native_exit,complete,review,fail_on,expected",
    [
        (0, True, False, "error", 0),
        (0, True, True, "error", 0),
        (0, True, True, "review-required", 1),
        (1, True, True, "error", 1),
        (1, True, True, "review-required", 1),
        (2, False, True, "error", 2),
        (0, False, True, "error", 2),
    ],
)
def test_report_policy_keeps_required_failures_and_incomplete_evidence_blocking(
    tmp_path,
    native_exit,
    complete,
    review,
    fail_on,
    expected,
):
    report = _report(complete=complete, review=review)
    (tmp_path / "impact.json").write_text(json.dumps(report), encoding="utf-8")
    (tmp_path / "impact.md").write_text(
        "Public sections to review.\n", encoding="utf-8"
    )
    outputs = tmp_path / "outputs"
    summary = tmp_path / "summary"
    result = _run(
        _script("result"),
        cwd=tmp_path,
        environment={
            "IMPACT_EVIDENCE": str(tmp_path),
            "IMPACT_EXIT": str(native_exit),
            "INPUT_FAIL_ON": fail_on,
            "GITHUB_OUTPUT": str(outputs),
            "GITHUB_STEP_SUMMARY": str(summary),
        },
    )
    assert result.returncode == expected, result.stderr
    values = dict(line.split("=", 1) for line in outputs.read_text().splitlines())
    assert values == {
        name: str(report[name]).lower()
        for name in ("complete", "review_required", "changed", "ready")
    }
    assert "Public sections to review." in summary.read_text()


def test_review_required_threshold_rejects_an_unready_report_without_pending_findings(
    tmp_path,
):
    from llm_wiki_cli.services.knowledge_evidence import hash_json

    report = _report()
    report["ready"] = False
    report["report_id"] = hash_json(
        {key: value for key, value in report.items() if key != "report_id"}
    )
    (tmp_path / "impact.json").write_text(json.dumps(report), encoding="utf-8")
    result = _run(
        _script("result"),
        cwd=tmp_path,
        environment={
            "IMPACT_EVIDENCE": str(tmp_path),
            "IMPACT_EXIT": "0",
            "INPUT_FAIL_ON": "review-required",
            "GITHUB_OUTPUT": str(tmp_path / "outputs"),
            "GITHUB_STEP_SUMMARY": str(tmp_path / "summary"),
        },
    )
    assert result.returncode == 1


@pytest.mark.parametrize(
    "corruption",
    [
        "missing",
        "boolean",
        "contradiction",
        "duplicate",
        "schema",
        "resealed-coverage",
        "commitment",
        "invalid-exit",
    ],
)
def test_invalid_or_unavailable_report_cannot_emit_ready_output(tmp_path, corruption):
    report = _report()
    native_exit = "0"
    if corruption == "boolean":
        report["complete"] = "true"
    elif corruption == "contradiction":
        report["review_required"] = True
    elif corruption == "schema":
        report["schema_version"] = "unknown/v1"
    elif corruption == "resealed-coverage":
        from llm_wiki_cli.services.knowledge_evidence import hash_json

        report["coverage"]["total"] = 1
        report["report_id"] = hash_json(
            {key: value for key, value in report.items() if key != "report_id"}
        )
    elif corruption == "commitment":
        report["report_id"] = "sha256:" + "c" * 64
    elif corruption == "invalid-exit":
        native_exit = "137"
    if corruption != "missing":
        raw = json.dumps(report)
        if corruption == "duplicate":
            raw = '{"complete":false,' + raw.removeprefix("{")
        (tmp_path / "impact.json").write_text(raw, encoding="utf-8")
    outputs = tmp_path / "outputs"
    result = _run(
        _script("result"),
        cwd=tmp_path,
        environment={
            "IMPACT_EVIDENCE": str(tmp_path),
            "IMPACT_EXIT": native_exit,
            "INPUT_FAIL_ON": "error",
            "GITHUB_OUTPUT": str(outputs),
            "GITHUB_STEP_SUMMARY": str(tmp_path / "summary"),
        },
    )
    assert result.returncode == 2
    assert not outputs.exists()


def _installed_fixture(tmp_path: Path):
    environment = tmp_path / ".venv"
    venv.EnvBuilder(with_pip=False).create(environment)
    executable = environment / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    site = Path(
        subprocess.check_output(
            [
                str(executable),
                "-I",
                "-c",
                "import sysconfig;print(sysconfig.get_paths()['purelib'])",
            ],
            text=True,
        ).strip()
    )
    provider = tmp_path / "provider"
    source = provider / "src/llm_wiki_cli"
    source.mkdir(parents=True)
    (provider / "pyproject.toml").write_text(
        '[project]\nversion="1.0.0"\n', encoding="utf-8"
    )
    (source / "__init__.py").write_text('__version__ = "1.0.0"\n', encoding="utf-8")
    (source / "cli.py").write_text("# Installed provider CLI.\n", encoding="utf-8")
    package = site / "llm_wiki_cli"
    shutil.copytree(source, package)
    metadata = site / "agent_wiki_cli-1.0.0.dist-info"
    metadata.mkdir()
    (metadata / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: agent-wiki-cli\nVersion: 1.0.0\n",
        encoding="utf-8",
    )
    consumer = tmp_path / "consumer"
    consumer.mkdir()
    return executable, provider, source, package, metadata, consumer


def test_impact_invocation_uses_installed_provider_and_consumer_paths_without_shell_expansion(
    tmp_path,
):
    executable, _, _, package, _, consumer = _installed_fixture(tmp_path)
    shadow = consumer / "llm_wiki_cli"
    shadow.mkdir()
    (shadow / "__init__.py").write_text(
        'raise RuntimeError("consumer shadow selected")\n', encoding="utf-8"
    )
    (package / "cli.py").write_text(
        textwrap.dedent("""
        import json
        import os
        from pathlib import Path
        import sys
        arguments = sys.argv[1:]
        output = Path(arguments[arguments.index('--output') + 1])
        output.write_text(json.dumps({'cwd': os.getcwd(), 'arguments': arguments,
                                      'interpreter': sys.executable}))
        print('Consumer impact summary.')
        raise SystemExit(1)
    """),
        encoding="utf-8",
    )
    evidence = tmp_path / "evidence with spaces"
    evidence.mkdir()
    outputs = tmp_path / "outputs"
    config = ".llm-wiki/config $(touch unexpected).json"
    result = _run(
        _script("impact"),
        cwd=tmp_path,
        executable=executable,
        environment={
            "IMPACT_CONSUMER": str(consumer),
            "IMPACT_EVIDENCE": str(evidence),
            "INPUT_CONFIG": config,
            "INPUT_BASELINE": "accepted baseline.json",
            "INPUT_REVIEWS": "reviews.json",
            "INPUT_TARGET_DIR": "public wiki",
            "GITHUB_OUTPUT": str(outputs),
            "PYTHONPATH": str(consumer),
            "PYTHONHOME": str(consumer),
            "VIRTUAL_ENV": str(consumer / "application-environment"),
        },
    )
    assert result.returncode == 0, result.stderr
    assert outputs.read_text().strip() == "exit-code=1"
    observed = json.loads((evidence / "impact.json").read_text())
    assert Path(observed["cwd"]) == consumer
    assert Path(observed["interpreter"]) == executable
    assert observed["arguments"] == [
        "docs",
        "impact",
        "--config",
        config,
        "--output",
        str(evidence / "impact.json"),
        "--format",
        "markdown",
        "--baseline",
        "accepted baseline.json",
        "--reviews",
        "reviews.json",
        "--target-dir",
        "public wiki",
    ]
    assert not (consumer / "unexpected").exists()
    assert (evidence / "impact.md").read_text() == "Consumer impact summary.\n"


@pytest.mark.parametrize(
    "mutation", ["none", "installed-bytes", "omitted-module", "version"]
)
def test_provider_verification_ignores_consumer_shadow_and_rejects_wrong_installation(
    tmp_path, mutation
):
    executable, provider, source, package, metadata, consumer = _installed_fixture(
        tmp_path
    )
    shadow = consumer / "llm_wiki_cli"
    shadow.mkdir()
    (shadow / "__init__.py").write_text(
        'raise RuntimeError("consumer shadow selected")\n', encoding="utf-8"
    )
    if mutation == "installed-bytes":
        (package / "cli.py").write_text(
            "# Another installed revision.\n", encoding="utf-8"
        )
    elif mutation == "omitted-module":
        (source / "new_module.py").write_text(
            "# Missing from installation.\n", encoding="utf-8"
        )
    elif mutation == "version":
        (metadata / "METADATA").write_text(
            "Metadata-Version: 2.1\nName: agent-wiki-cli\nVersion: 0.1.0\n",
            encoding="utf-8",
        )
    tree = ast.parse(_script("provider"))
    script = next(
        node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)
        and any(
            isinstance(target, ast.Name) and target.id == "verify"
            for target in node.targets
        )
    )
    receipt = tmp_path / "provider.json"
    assert isinstance(script, str)
    result = subprocess.run(
        [
            str(executable),
            "-I",
            "-c",
            textwrap.dedent(script),
            str(provider),
            str(receipt),
        ],
        cwd=consumer,
        env={**os.environ, "PYTHONPATH": str(consumer)},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if mutation == "none":
        assert result.returncode == 0, result.stderr
        observed = json.loads(receipt.read_text())
        assert observed["installed"] is True
        assert observed["version"] == "1.0.0"
        assert Path(observed["package_origin"]) == package
    else:
        assert result.returncode != 0
        assert not receipt.exists()
