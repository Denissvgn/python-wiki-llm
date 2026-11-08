"""Exercise isolated provider and consumer policy boundaries of the impact action."""

from __future__ import annotations

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


def test_root_pilot_binds_manual_claims_and_leaves_cli_discovery_open():
    from llm_wiki_cli.services.publication_config import load_publication_config

    config = load_publication_config(ROOT)
    assert config["architecture"] == {
        "baseline": "existing-wiki",
        "root": "docs/llm_wiki",
    }
    assert config["target"] == {"kind": "github-wiki", "repository": "self"}
    assert config["enforcement"] == "advisory" and config["publish"] is False
    assert config["reference_providers"]["provider-policy"] == {
        "kind": "llm-wiki-behavior"
    }
    topics = {topic["id"]: topic for topic in config["topics"]}
    assert {
        key for key, topic in topics.items() if topic["edit_at"] == "repository"
    } == {"sibling-wiki.maintenance"}
    guide = topics["sibling-wiki.maintenance"]
    assert guide["source_document"] == "docs/sibling-wiki.md"
    assert {"reference": "llm-wiki", "command": ["docs", "wiki"]} in guide["depends_on"]
    for key, group in (
        ("home.project-facts", "package"),
        ("getting-started.initialize", "setup"),
        ("getting-started.bootstrap", "storage"),
        ("installation.python-version", "package"),
        ("installation.runtime", "package"),
        ("installation.toolchains", "setup"),
        ("plugins.bundled-skills", "skills"),
        ("core-concepts.sync", "storage"),
        ("sync.manual", "storage"),
        ("context.protocol", "task"),
        ("mcp.server", "package"),
        ("standalone.wiki-baseline", "storage"),
        ("command-reference.upgrade", "setup"),
        ("migration.upgrade-framework-artifacts", "storage"),
        ("migration.upgrade-framework-artifacts", "task"),
    ):
        assert {"reference": "provider-policy", "fact": group} in topics[key][
            "depends_on"
        ]
    assert {"source_file": "docs/sibling-wiki.md"} in topics["faq.publication-source"][
        "depends_on"
    ]
    assert {"source_file": "docs/maintenance.md"} in topics["faq.sync-freshness"][
        "depends_on"
    ]
    assert {"reference": "llm-wiki", "command": ["ci-check"]} in topics[
        "command-reference.ci-check"
    ]["depends_on"]
    assert topics["command-reference.commands"]["depends_on"] == [
        {"reference": "llm-wiki", "command": []}
    ]
    for key in ("command-reference.upgrade", "migration.upgrade-framework-artifacts"):
        assert {"reference": "llm-wiki", "command": ["upgrade"]} in topics[key][
            "depends_on"
        ]
        assert {
            "architecture_page": "workflows/upgrade_current_knowledge.md",
            "facets": ["whole"],
        } in topics[key]["depends_on"]
    for topic in topics.values():
        assert topic["owner"] == "maintainers"
        for dependency in topic["depends_on"]:
            if "architecture_page" in dependency:
                assert (
                    ROOT
                    / config["architecture"]["root"]
                    / dependency["architecture_page"]
                ).is_file()
            if "source_file" in dependency:
                assert (ROOT / dependency["source_file"]).is_file()
    patterns = [exclusion["pattern"] for exclusion in config["exclusions"]]
    assert all(exclusion["reason"] for exclusion in config["exclusions"])
    assert any(
        fnmatchcase("workflows/upgrade_current_knowledge.md", pattern)
        for pattern in patterns
    )
    assert not any(
        fnmatchcase("flows/cli-new-command.md", pattern) for pattern in patterns
    )


def test_root_workflow_reports_eligible_changes_and_observes_drift_read_only():
    path = ROOT / ".github/workflows/sibling-wiki-impact.yml"
    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert set(workflow["on"]) == {"workflow_dispatch", "push", "pull_request", "schedule", "gollum"}
    assert workflow["on"]["schedule"] and "github.event.repository.default_branch" in workflow["jobs"]["report"]["if"]
    assert workflow["permissions"] == {"contents": "read"}
    job = workflow["jobs"]["report"]
    assert job["permissions"] == {"contents": "read"}
    checkouts = [
        step
        for step in job["steps"]
        if step.get("uses", "").startswith("actions/checkout@")
    ]
    assert {s["with"]["path"] for s in checkouts} == {"consumer", ".provider"}
    assert all(s["with"]["ref"] == "${{ github.sha }}" for s in checkouts)
    assert all(s["with"]["persist-credentials"] is False for s in checkouts)
    action = next(
        step
        for step in job["steps"]
        if step.get("uses") == "./.provider/integrations/wiki-impact"
    )
    assert action["with"] == {
        "config": ".llm-wiki/publication.json",
        "working-directory": "consumer",
        "baseline": "${{ inputs.baseline || vars.SIBLING_WIKI_BASELINE }}",
        "reviews": "${{ inputs.reviews || vars.SIBLING_WIKI_REVIEWS }}",
        "accepted-state-revision": "${{ github.event.pull_request.base.sha || github.sha }}",
        "observe-drift": "${{ github.event_name != 'pull_request' }}",
        "target-dir": "sibling-wiki",
        "fail-on": "error",
    }
    clone = next(step for step in job["steps"] if "run" in step)
    assert clone["env"]["REPOSITORY"] == "${{ github.repository }}"
    assert clone["env"]["ACCEPTED_BASELINE"] == action["with"]["baseline"]
    assert clone["env"]["ACCEPTED_REVIEWS"] == action["with"]["reviews"]
    assert clone["env"]["ACCEPTED_SHA"] == action["with"]["accepted-state-revision"]
    assert "--depth" not in clone["run"] and clone["working-directory"] == "consumer"
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
            "GITHUB_EVENT_NAME": "workflow_dispatch",
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
    "mutation", ["none", "installed-bytes", "omitted-module", "omitted-data", "version"]
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
    data = Path("schemas/llm-wiki-behavior-facts-v1.schema.json")
    parser_metadata = metadata.parent / "markdown_it_py-4.0.0.dist-info"
    parser_metadata.mkdir()
    (parser_metadata / "METADATA").write_text("Metadata-Version: 2.1\nName: markdown-it-py\nVersion: 4.0.0\n", encoding="utf-8")
    (provider / "pyproject.toml").write_text(
        '[project]\nversion="1.0.0"\n[tool.setuptools.package-data]\n'
        f'llm_wiki_cli=["{data.as_posix()}"]\n', encoding="utf-8"
    )
    (source / data.parent).mkdir()
    (source / data).write_text("{}\n", encoding="utf-8")
    if mutation != "omitted-data":
        (package / data.parent).mkdir()
        shutil.copyfile(source / data, package / data)
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
    step = next(
        s for s in yaml.safe_load(ACTION_PATH.read_text())["runs"]["steps"]
        if s.get("id") == "provider"
    )
    assert '"${GITHUB_ACTION_PATH}/../wiki-candidate/provider.py" impact' in step["run"]
    assert step["env"]["PROVIDER_ACTION_REF"] == "${{ github.action_ref }}"
    assert step["env"]["PROVIDER_REPOSITORY"] == "${{ github.action_repository }}"
    receipt = tmp_path / "provider.json"
    revision = "a" * 40
    result = subprocess.run(
        [
            str(executable),
            "-I",
            str(ROOT / "integrations/wiki-candidate/provider.py"),
            "verify",
            str(provider),
            str(receipt),
            revision,
            "fixture/provider",
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
        assert observed["provider_revision"] == revision
        assert observed["action_repository"] == "fixture/provider"
        assert observed["parser_version"] == "4.0.0"
    else:
        assert result.returncode != 0
        assert not receipt.exists()
