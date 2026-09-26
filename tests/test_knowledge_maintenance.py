"""Maintenance evidence cannot replace integrity or admit unrelated source."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import shlex
import shutil
import subprocess
import sys
import tarfile

import pytest
import yaml

from llm_wiki_cli.services import health_policy as hp, knowledge_maintenance as km
from llm_wiki_cli.services.health_details import CapturedHealthDetails
from tests.test_health_details import _report, _ci, _doctor


from tests.test_knowledge_health_refresh import recorded_project as recorded_project


@pytest.fixture
def preflight_project(recorded_project, tmp_path, monkeypatch):
    import llm_wiki_cli

    monkeypatch.setattr(llm_wiki_cli, "__version__", "9.8.6")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname="agent-wiki-cli"\nversion="9.8.6"\n', encoding="utf-8"
    )
    monkeypatch.setattr(
        km,
        "_git",
        lambda root, *args: (
            "" if args[0] == "status" else "a" * 40 if args[-1] == "HEAD" else "b" * 40
        ),
    )
    monkeypatch.setattr(
        km,
        "_installed",
        lambda *args: {
            "version": "9.8.6",
            "import_root": "/installed",
            "implementation_hash": "sha256:" + "e" * 64,
            "editable": False,
        },
    )
    return {
        "candidate_root": str(tmp_path),
        "candidate_sha": "a" * 40,
        "src_dir": "source",
        "wiki_dir": "wiki",
    }


def test_preflight_reuses_provider_metadata_without_source_extraction(
    preflight_project, monkeypatch
):
    from llm_wiki_cli.services import extraction_service, lint_service

    def reject(*args, **kwargs):
        pytest.fail("maintenance preflight must not extract source")

    monkeypatch.setattr(extraction_service, "get_inventory_result", reject)
    monkeypatch.setattr(lint_service, "get_inventory_result", reject)
    result = km.preflight(**preflight_project)
    assert result["status"] == "ready", result
    assert result["binding"]["concepts_total"] > 0
    assert result["binding"]["live_source_hash"].startswith("sha256:")
    assert "not source freshness" in result["limitations"][0]


def test_preflight_detects_version_only_change_before_analysis(
    preflight_project, monkeypatch
):
    import llm_wiki_cli

    monkeypatch.setattr(llm_wiki_cli, "__version__", "9.8.7")
    result = km.preflight(**preflight_project)
    assert result["status"] == "blocked"
    assert any("recorded producer" in reason for reason in result["issues"])


def test_preflight_rejects_changed_selection_and_missing_helper(
    preflight_project, monkeypatch
):
    (Path("source") / "selected.ts").write_text(
        "export const value = 1;\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        km.extractor_helpers, "get_prepared_typescript_root", lambda *args: None
    )
    result = km.preflight(**preflight_project)
    assert result["status"] == "blocked" and any(
        "selected helper" in x for x in result["issues"]
    )
    config_dir = Path("source/.llm-wiki")
    config_dir.mkdir()
    (config_dir / "source-selection.json").write_text(
        json.dumps(
            {
                "schema_version": "llm-wiki-source-selection/v1",
                "include": ["models.py"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )
    result = km.preflight(**preflight_project)
    assert result["status"] == "blocked" and any(
        "source" in x and "selection" in x for x in result["issues"]
    )


def test_preflight_generation_configuration_change_is_not_version_equivalence(
    preflight_project, monkeypatch
):
    original = km.runtime_generation_options

    def altered(**kwargs):
        return {**original(**kwargs), "preserve_semantic": False}

    monkeypatch.setattr(km, "runtime_generation_options", altered)
    result = km.preflight(**preflight_project)
    assert result["status"] == "blocked" and any(
        "generation options" in x for x in result["issues"]
    )


def test_preflight_rejects_scope_outside_the_candidate(preflight_project, tmp_path):
    preflight_project["candidate_root"] = str(tmp_path / "other")
    with pytest.raises(ValueError, match="must belong"):
        km.preflight(**preflight_project)


def test_archive_preflight_binds_original_source_and_rejects_mutation(
    preflight_project,
):
    candidate = Path(preflight_project["candidate_root"])
    archive = candidate / "frozen.tar"
    paths = [p for p in candidate.rglob("*") if p.is_file()]
    with tarfile.open(archive, "w") as stream:
        for path in paths:
            stream.add(path, arcname=path.relative_to(candidate).as_posix())
    identity = candidate / "identity.json"
    identity.write_bytes(
        raw(
            {
                "schema_version": "agent-wiki-release-identity/v1",
                "version": "9.8.6",
                "source": {
                    "sha": "a" * 40,
                    "tree": "b" * 40,
                    "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                },
            }
        )
    )
    options = {
        **preflight_project,
        "identity_path": str(identity),
        "source_archive": str(archive),
    }
    assert km.preflight(**options)["status"] == "ready"
    source = next((candidate / "source").glob("*.py"))
    source.write_bytes(source.read_bytes() + b"\n# changed after freeze\n")
    with pytest.raises(ValueError, match="differs from the frozen candidate"):
        km.preflight(**options)


@pytest.mark.parametrize(
    "failure", ["version", "wrong-import", "changed-code", "extra-code"]
)
def test_installed_candidate_identity_rejects_stale_or_wrong_code(
    tmp_path, monkeypatch, failure
):
    import types
    import llm_wiki_cli

    candidate = tmp_path / "candidate"
    source = candidate / "src/llm_wiki_cli"
    source.mkdir(parents=True)
    installed = tmp_path / "site/llm_wiki_cli"
    installed.mkdir(parents=True)
    for base in (source, installed):
        (base / "__init__.py").write_text('VERSION = "2.3.0"\n', encoding="utf-8")
    monkeypatch.setattr(llm_wiki_cli, "__file__", str(installed / "__init__.py"))
    monkeypatch.setattr(llm_wiki_cli, "__version__", "2.3.0")
    distribution = types.SimpleNamespace(
        version="2.3.0", locate_file=lambda name: tmp_path / "site" / name
    )
    monkeypatch.setattr(
        km.importlib.metadata, "distribution", lambda name: distribution
    )
    assert km._installed(candidate, "2.3.0", False)["version"] == "2.3.0"
    if failure == "version":
        distribution.version = "2.2.0"
    if failure == "wrong-import":
        monkeypatch.setattr(
            llm_wiki_cli, "__file__", str(tmp_path / "other/llm_wiki_cli/__init__.py")
        )
    if failure == "changed-code":
        (installed / "__init__.py").write_text("wrong implementation", encoding="utf-8")
    if failure == "extra-code":
        (installed / "extra.py").write_text("unexpected module", encoding="utf-8")
    with pytest.raises(ValueError):
        km._installed(candidate, "2.3.0", False)


def test_early_version_alignment_does_not_claim_freshness(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname="agent-wiki-cli"\nversion="2.3.0"\n', encoding="utf-8"
    )
    wiki = tmp_path / "docs/llm_wiki"
    wiki.mkdir(parents=True)
    (wiki / ".llm-wiki-knowledge.json").write_bytes(
        raw(
            {
                "schema_version": "llm-wiki-knowledge/v4",
                "store": {"bundle": {"producer": {"tool": {"version": "2.2.0"}}}},
            }
        )
    )
    result = RELEASE["version_check"](tmp_path, config())
    assert result["status"] == "blocked" and result["recorded_version"] == "2.2.0"
    assert result["candidate_version"] == "2.3.0"


def test_disabled_preflight_adds_no_new_qualification_failure(tmp_path):
    # The explicit rollback does not even require the additional policy inputs.
    result = RELEASE["version_check"](tmp_path, config("disabled"))
    assert result["status"] == "disabled" and result["recorded_version"] is None


ROOT = Path(__file__).parents[1]
RELEASE = runpy.run_path(str(ROOT / "release/knowledge_maintenance.py"))


def evidence(root, scenario="current"):
    report = _report(root, scenario)
    assert report.health_details is not None
    detail = report.health_details.to_payload()
    detail["scope"].update(src_dir="candidate", wiki_dir="candidate/docs/llm_wiki")
    detail["scope"]["selection"]["state"] = "legacy"
    detail["snapshot"]["live_source_hash"] = "sha256:" + "c" * 64
    report.wiki_dir, report.src_dir = "candidate/docs/llm_wiki", "candidate"
    report.health_details = CapturedHealthDetails(json.dumps(detail))
    ci = _ci(report)
    binding = {
        "candidate_sha": "a" * 40,
        "candidate_tree": "b" * 40,
        "candidate_version": "2.3.0" if scenario == "producer-changed" else "2.2.0",
        "source_archive_sha256": "sha256:" + "d" * 64,
        "concepts_total": detail["coverage"]["total"],
        "src_dir": report.src_dir,
        "wiki_dir": report.wiki_dir,
        "selection_fingerprint": detail["scope"]["selection"]["fingerprint"],
        "selection_inputs_hash": detail["scope"]["selection"]["inputs_hash"],
        **{
            key: detail["snapshot"][key]
            for key in (
                "live_source_hash",
                "knowledge_index_hash",
                "surface_index_hash",
                "evaluated_envelope_hash",
            )
        },
    }
    preflight = {
        "schema_version": hp.PREFLIGHT_SCHEMA,
        "status": "ready",
        "binding": binding,
        "installed": {
            "version": binding["candidate_version"],
            "import_root": "/installed",
            "implementation_hash": "sha256:" + "e" * 64,
            "editable": False,
        },
        "issues": [],
        "limitations": [],
        "remedy": "Review and sync.",
    }
    return report, ci, preflight, binding


def raw(value):
    return json.dumps(value, sort_keys=True).encode()


@pytest.mark.parametrize(
    "scenario,passed",
    [
        ("current", True),
        ("producer-changed", False),
        ("nonsemantic", False),
        ("source-changed", False),
        ("source-missing", False),
        ("live-basis-missing", False),
        ("unevaluated", False),
        ("partial", False),
        ("recorded-basis-missing", False),
    ],
)
def test_policy_recomputes_strict_health_without_reanalysis(tmp_path, scenario, passed):
    report, ci, preflight, binding = evidence(tmp_path, scenario)
    receipt = hp.derive_policy(raw(ci), raw(preflight), binding=binding)
    assert (receipt["status"] == "pass") is passed
    assert receipt["strict_health"] == _doctor(report)["status"]
    assert (
        hp.verify_policy(receipt, raw(ci), raw(preflight), binding=binding) == receipt
    )
    assert (
        hp.verify_policy(
            receipt,
            raw(ci),
            raw(preflight),
            binding=binding,
            validate_full_report=False,
        )
        == receipt
    )
    assert ci["knowledge_drift_gate"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("candidate_sha", "f" * 40),
        ("candidate_tree", "f" * 40),
        ("src_dir", "fixture"),
        ("wiki_dir", "fixture/wiki"),
        ("knowledge_index_hash", "sha256:" + "0" * 64),
        ("selection_fingerprint", "sha256:" + "1" * 64),
        ("live_source_hash", "sha256:" + "2" * 64),
    ],
)
def test_policy_rejects_wrong_candidate_scope_or_snapshot(tmp_path, field, value):
    _, ci, before, binding = evidence(tmp_path)
    changed = {**binding, field: value}
    with pytest.raises(ValueError):
        hp.derive_policy(raw(ci), raw(before), binding=changed)
    before["binding"] = changed
    with pytest.raises(ValueError):
        hp.derive_policy(raw(ci), raw(before), binding=binding)


@pytest.mark.parametrize(
    "field,value", [("status", "pass"), ("strict_health", "healthy"), ("reasons", [])]
)
def test_copied_healthy_verdict_cannot_hide_drift(tmp_path, field, value):
    _, ci, before, binding = evidence(tmp_path, "producer-changed")
    receipt = hp.derive_policy(raw(ci), raw(before), binding=binding)
    receipt[field] = value
    with pytest.raises(ValueError):
        hp.verify_policy(
            receipt, raw(ci), raw(before), binding=binding, validate_full_report=False
        )


def test_policy_input_hashes_and_json_types_are_binding(tmp_path):
    _, ci, before, binding = evidence(tmp_path)
    receipt = hp.derive_policy(raw(ci), raw(before), binding=binding)
    with pytest.raises(ValueError):
        hp.verify_policy(receipt, raw(ci) + b"\n", raw(before), binding=binding)
    bad = deepcopy(ci)
    bad["knowledge_health"]["health_details"]["coverage"]["evaluated"] = True
    with pytest.raises(ValueError):
        hp.derive_policy(
            raw(bad), raw(before), binding=binding, validate_full_report=False
        )
    with pytest.raises(ValueError, match="duplicate"):
        hp.strict_json(b'{"status":"pass","status":"fail"}')


def test_policy_command_accepts_normalized_wiki_alias_on_native_paths(tmp_path):
    _, ci, before, binding = evidence(tmp_path / "fixture")
    normalized = str(Path("candidate/docs/llm_wiki"))
    ci["wiki_dir"] = normalized
    ci["knowledge_health"]["wiki_dir"] = normalized
    ci["knowledge_health"]["health_details"]["scope"]["wiki_dir"] = normalized
    binding["wiki_dir"] = normalized
    report = tmp_path / "ci.json"
    preflight = tmp_path / "preflight.json"
    report.write_bytes(raw(ci))
    preflight.write_bytes(raw(before))
    output = tmp_path / "policy.json"
    assert (
        km.main(
            [
                "derive",
                "--report",
                str(report),
                "--preflight",
                str(preflight),
                "--candidate-sha",
                binding["candidate_sha"],
                "--candidate-tree",
                binding["candidate_tree"],
                "--src-dir",
                "candidate",
                "--wiki-dir",
                "./candidate/docs/llm_wiki/",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert json.loads(output.read_text())["binding"]["wiki_dir"] == normalized


def test_preflight_failure_and_output_failure_remain_blocking_for_policy(tmp_path):
    _, ci, before, binding = evidence(tmp_path)
    before.update(status="blocked", issues=["wrong installed candidate"])
    assert hp.derive_policy(raw(ci), raw(before), binding=binding)["status"] == "fail"
    before.update(status="ready", issues=[])
    ci["runtime"]["report"] = {
        "path": "report.md",
        "explicit": True,
        "status": "failed",
        "error": "disk full",
    }
    ci["command_exit_code"] = 2
    assert hp.derive_policy(raw(ci), raw(before), binding=binding)["status"] == "fail"


def config(mode="shadow"):
    value = json.loads((ROOT / "release/knowledge-maintenance.json").read_text())
    value["mode"] = mode
    if mode == "required":
        value["activation"] = {
            "candidate_sha": "1" * 40,
            "run_id": 123,
            "attempt": 1,
            "comparison_sha256": "2" * 64,
            "implementation_sha256": hashlib.sha256(
                (ROOT / RELEASE["LEAF_PATH"]).read_bytes()
            ).hexdigest(),
        }
    return value


def test_required_mode_requires_reviewed_activation_and_unchanged_policy():
    value = config("required")
    assert RELEASE["policy"](raw(value))["mode"] == "required"
    value["activation"]["implementation_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="changed since"):
        RELEASE["policy"](raw(value))
    value["activation"] = None
    with pytest.raises(ValueError, match="activation"):
        RELEASE["policy"](raw(value))


@pytest.mark.parametrize("mode", ["shadow", "required", "disabled"])
def test_release_admission_and_explicit_rollback(tmp_path, mode):
    report, ci, before, binding = evidence(tmp_path / "wiki")
    directory = tmp_path / "evidence"
    directory.mkdir()
    receipt = hp.derive_policy(raw(ci), raw(before), binding=binding)
    for name, value in [
        ("ci-report.json", ci),
        ("preflight.json", before),
        ("policy.json", receipt),
        ("doctor.json", _doctor(report)),
    ]:
        (directory / name).write_bytes(raw(value))
    identity = {
        "source": {
            "sha": binding["candidate_sha"],
            "tree": binding["candidate_tree"],
            "archive_sha256": "d" * 64,
        },
        "version": binding["candidate_version"],
    }
    result = RELEASE["admit"](directory, identity, config(mode))
    assert result["status"] == ("disabled" if mode == "disabled" else "pass"), result
    (directory / "policy.json").unlink()
    result = RELEASE["admit"](directory, identity, config(mode))
    assert result["status"] == ("disabled" if mode == "disabled" else "fail")


def test_shadow_requires_original_standalone_parity(tmp_path):
    report, ci, before, binding = evidence(tmp_path / "wiki")
    directory = tmp_path / "evidence"
    directory.mkdir()
    for name, value in [
        ("ci-report.json", ci),
        ("preflight.json", before),
        ("policy.json", hp.derive_policy(raw(ci), raw(before), binding=binding)),
    ]:
        (directory / name).write_bytes(raw(value))
    identity = {
        "source": {
            "sha": binding["candidate_sha"],
            "tree": binding["candidate_tree"],
            "archive_sha256": "d" * 64,
        },
        "version": binding["candidate_version"],
    }
    assert RELEASE["admit"](directory, identity, config())["status"] == "fail"
    doctor = _doctor(report)
    doctor["wiki_dir"] = "fixture/wiki"
    (directory / "doctor.json").write_bytes(raw(doctor))
    assert RELEASE["admit"](directory, identity, config())["status"] == "fail"


@pytest.mark.parametrize("mode", ["shadow", "required"])
@pytest.mark.parametrize("available", [True, False], ids=["published-artifact", "missing-artifact"])
def test_workflow_consumer_uses_the_actual_action_upload(tmp_path, mode, available):
    workflow = yaml.safe_load((ROOT / ".github/workflows/release-qualification.yml").read_text())
    producer = next(step for step in workflow["jobs"]["action"]["steps"] if step.get("name") == "Upload gate evidence")
    consumer = workflow["jobs"]["knowledge-maintenance"]["steps"]
    download = next(step for step in consumer if step.get("with", {}).get("path") == "incoming/action")
    verify = next(step for step in consumer if step.get("name") == "Verify captured policy and shadow parity")
    report, ci, before, binding = evidence(tmp_path / "fixture")
    published = tmp_path / "published/maintenance"
    published.mkdir(parents=True)
    for name, payload in (
        ("ci-report.json", ci), ("preflight.json", before),
        ("policy.json", hp.derive_policy(raw(ci), raw(before), binding=binding)),
        ("doctor.json", _doctor(report)),
    ):
        (published / name).write_bytes(raw(payload))
    # Artifact lookup uses the producer's real name; independent matching
    # expectations must not repeat a wrong literal on the consumer side.
    assert download["with"]["name"] == producer["with"]["name"]
    catalog = {producer["with"]["name"]: published.parent} if available else {}
    selected = catalog.get(download["with"]["name"])
    if selected is not None:
        shutil.copytree(selected, tmp_path / download["with"]["path"])
    tools = tmp_path / "incoming/tools"
    for relative in ("release/knowledge_maintenance.py", RELEASE["LEAF_PATH"]):
        target = tools / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    (tools / RELEASE["POLICY_PATH"]).write_bytes(raw(config(mode)))
    (tmp_path / "expected-identity.json").write_bytes(raw({
        "version": binding["candidate_version"],
        "source": {"sha": binding["candidate_sha"], "tree": binding["candidate_tree"],
                   "archive_sha256": binding["source_archive_sha256"].removeprefix("sha256:")},
    }))
    command = shlex.split(verify["run"])
    assert command[0] == "python"
    command[0] = sys.executable
    result = subprocess.run(command, cwd=tmp_path, stdin=subprocess.DEVNULL,
                            env={**os.environ, "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.md")},
                            capture_output=True, text=True, check=False, timeout=30)
    assert result.returncode == (1 if not available and mode == "required" else 0), result.stderr
    receipt = json.loads((tmp_path / "verification.json").read_text())
    assert receipt["status"] == ("pass" if available else "fail")
    assert receipt["mode"] == mode and receipt["candidate_sha"] == binding["candidate_sha"]
    assert bool(receipt["evidence_sha256"]) is available


@pytest.fixture
def maintenance_bundle(tmp_path):
    _, ci, before, binding = evidence(tmp_path / "fixture")
    bundle = tmp_path / "bundle"
    source = bundle / "evidence/RD-00/source"
    source.mkdir(parents=True)
    archive = source / "candidate-source.tar"
    with tarfile.open(archive, "w") as stream:
        for name, content in (
            (RELEASE["POLICY_PATH"], raw(config("required"))),
            (RELEASE["LEAF_PATH"], (ROOT / RELEASE["LEAF_PATH"]).read_bytes()),
        ):
            entry = tarfile.TarInfo(name)
            entry.size = len(content)
            stream.addfile(entry, io.BytesIO(content))
    archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    binding["source_archive_sha256"] = "sha256:" + archive_hash
    identity = {
        "source": {
            "sha": binding["candidate_sha"],
            "tree": binding["candidate_tree"],
            "archive_sha256": archive_hash,
        },
        "version": binding["candidate_version"],
    }
    (source / "identity.json").write_bytes(raw(identity))
    directory = bundle / "evidence/RD-10/action/maintenance"
    directory.mkdir(parents=True)
    for name, value in (
        ("ci-report.json", ci),
        ("preflight.json", before),
        ("policy.json", hp.derive_policy(raw(ci), raw(before), binding=binding)),
    ):
        (directory / name).write_bytes(raw(value))
    result = RELEASE["admit"](directory, identity, config("required"))
    assert result["status"] == "pass", result
    verification = bundle / "evidence/RD-10/maintenance/verification.json"
    verification.parent.mkdir()
    verification.write_bytes(raw(result))
    return bundle, result


@pytest.mark.parametrize(
    "mutation",
    ["none", "missing-producer", "copied-producer", "missing-input", "changed-input"],
)
def test_bundle_rechecks_required_inputs_and_separate_producer(
    maintenance_bundle, mutation
):
    bundle, result = maintenance_bundle
    verification = bundle / "evidence/RD-10/maintenance/verification.json"
    report = bundle / "evidence/RD-10/action/maintenance/ci-report.json"
    if mutation == "missing-producer":
        verification.unlink()
    if mutation == "copied-producer":
        result["candidate_tree"] = "f" * 40
        verification.write_bytes(raw(result))
    if mutation == "missing-input":
        report.unlink()
    if mutation == "changed-input":
        report.write_bytes(report.read_bytes() + b"\n")
    if mutation == "none":
        assert RELEASE["bundle_policy"](bundle) == result
    else:
        with pytest.raises(ValueError):
            RELEASE["bundle_policy"](bundle)


@pytest.mark.parametrize("conclusion", [None, "failure", "cancelled", "skipped"])
def test_hosted_admission_requires_successful_maintenance_producer(
    tmp_path, conclusion, monkeypatch
):
    from release import hosted_evidence as hosted
    from tests.hosted_evidence_fixtures import HostedEvidence

    source = tmp_path / "evidence/RD-00/source"
    source.mkdir(parents=True)
    with tarfile.open(source / "candidate-source.tar", "w") as archive:
        content = raw(config("required"))
        member = tarfile.TarInfo(RELEASE["POLICY_PATH"])
        member.size = len(content)
        archive.addfile(member, io.BytesIO(content))
    identity = {"repository": "example/repository", "source": {"sha": "a" * 40}}
    client = HostedEvidence(identity, 123, source)
    if conclusion is not None:
        client.jobs.append(
            {
                **client.jobs[0],
                "id": 999,
                "name": "Repository knowledge maintenance",
                "conclusion": conclusion,
            }
        )
    monkeypatch.setattr(hosted, "GitHub", client.client)
    expected = (
        "missing or ambiguous hosted producer"
        if conclusion is None
        else "hosted producer did not succeed"
    )
    with pytest.raises(hosted.EvidenceError, match=expected):
        hosted.verify(tmp_path, identity, client.context, 123)


def test_historical_coverage_is_exact_and_v3_rendering_is_bounded(tmp_path):
    from llm_wiki_cli.services.ci_report import validate_doctor_payload
    from llm_wiki_cli.services.doctor_service import _render_doctor_payload
    from llm_wiki_cli.services.health_summary import detailed_health_rows

    report, _, _, _ = evidence(tmp_path, "producer-changed")
    doctor = _doctor(report)
    detail = doctor["health_details"]
    detail["coverage"].update(
        total=1418, modeled=800, unmodeled=618, evaluated=800, comparison_attempted=800
    )
    detail["coverage"]["outcomes"]["basis-incompatible"] = 800
    doctor["freshness"].update(concepts=1418, disclosure="evaluated (1418 concepts)")
    for section in ("freshness", "drift"):
        doctor[section]["counts_by_state"].update(
            unknown=618, **{"basis-incompatible": 800}
        )
    doctor["drift"].update(indeterminate=800, diagnostic_count=800)
    for group in detail["reasons"]:
        group["concepts"] = 618 if group["code"] == "freshness-not-modeled" else 800
        group["omitted"] = group["concepts"] - len(group["examples"])
    validate_doctor_payload(doctor, expected_strict=True)
    renderer = runpy.run_path(
        str(ROOT / "integrations/github-action/render_summary.py")
    )
    text = renderer["render_summary"](
        doctor, evidence_artifact="actual-repository-evidence"
    )
    console = _render_doctor_payload(doctor)
    for rendered in (text, console):
        assert "modeled=800" in rendered and "unmodeled=618" in rendered
        assert "producer-tool-version-changed=800" in rendered
        assert "2.2.0" in rendered and "2.3.0" in rendered
    assert "actual-repository-evidence" in text
    # Presentation clips hostile captured content without mutating retained data.
    detail["basis"]["live"]["tool"]["version"] = "`|\n\u202e" + "z" * 10000
    snapshot = deepcopy(doctor)
    text = renderer["render_summary"](
        doctor, evidence_artifact="actual-repository-evidence"
    )
    assert len(text.encode()) <= 8192 and len(text.splitlines()) <= 40
    assert "[truncated]" in text and r"\x60\| \u202e" in text
    assert doctor == snapshot
    assert dict(detailed_health_rows(doctor))["Producer"].endswith("z" * 10000)


def test_summary_reports_actual_versions_counts_and_legacy_limits(tmp_path):
    from llm_wiki_cli.services.health_summary import detailed_health_rows

    report, ci, _, _ = evidence(tmp_path, "producer-changed")
    rows = dict(detailed_health_rows(ci["knowledge_health"]))
    assert "modeled=3" in rows["Coverage"] and "unmodeled=3" in rows["Coverage"]
    assert "2.2.0" in rows["Producer"] and "2.3.0" in rows["Producer"]
    assert "producer-tool-version-changed=3" in rows["Primary causes (concepts)"]
    assert "llm-wiki sync" in rows["Next action"]
    assert rows["Affected examples"].startswith("llm-wiki://")
    legacy = _doctor(report, schema="v1")
    assert "unavailable" in dict(detailed_health_rows(legacy))["Coverage detail"]


def test_stdlib_admission_import_does_not_load_candidate_package(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "isolated_leaf", ROOT / RELEASE["LEAF_PATH"]
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _, ci, before, binding = evidence(tmp_path)
    receipt = hp.derive_policy(raw(ci), raw(before), binding=binding)
    assert (
        module.verify_policy(
            receipt, raw(ci), raw(before), binding=binding, validate_full_report=False
        )["status"]
        == "pass"
    )
