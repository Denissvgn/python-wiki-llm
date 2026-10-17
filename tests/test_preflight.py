"""Independent local preparation admission and evidence-boundary controls.

Fixtures keep publication authority separate from local receipts, and exercise
refusals before any expensive driver can execute.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from release import preflight


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "Local verification",
            "GIT_AUTHOR_EMAIL": "local@example.invalid",
            "GIT_COMMITTER_NAME": "Local verification",
            "GIT_COMMITTER_EMAIL": "local@example.invalid",
        },
    )
    return completed.stdout.strip()


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    _git(root, "init", "--quiet")
    (root / ".gitignore").write_text("private/\n", encoding="utf-8")
    (root / "pyproject.toml").write_text(
        '[project]\nname = "agent-wiki-cli"\nversion = "9.0.0"\n',
        encoding="utf-8",
    )
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [9.0.0] - 2026-10-17\n\nA candidate.\n"
        "[Unreleased]: https://example.invalid/compare/v9.0.0...HEAD\n"
        "[9.0.0]: https://example.invalid/releases/v9.0.0\n",
        encoding="utf-8",
    )
    (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "--quiet", "-m", "Initial candidate")
    return root


def _tree(root: Path) -> dict[str, bytes]:
    return {
        file.relative_to(root).as_posix(): file.read_bytes()
        for file in root.rglob("*")
        if file.is_file() and ".git" not in file.relative_to(root).parts
    }


@pytest.mark.parametrize(
    "raw",
    [
        b"not JSON",
        b"[]",
        b'{"schema_version":"one","schema_version":"two"}',
        b'{"value":NaN}',
        b'{"value":Infinity}',
        b'{"value":-Infinity}',
    ],
    ids=["malformed", "wrong-top-level", "duplicate", "nan", "infinity", "negative-infinity"],
)
def test_document_parser_refuses_ambiguous_or_nonfinite_records(tmp_path, raw):
    path = tmp_path / "document.json"
    path.write_bytes(raw)
    with pytest.raises((ValueError, preflight.PreflightError)):
        preflight.read_document(path)
    assert path.read_bytes() == raw


def test_document_reader_does_not_follow_symlink(tmp_path):
    original = tmp_path / "original.json"
    original.write_bytes(b'{"sentinel":"preserve"}')
    link = tmp_path / "redirect.json"
    link.symlink_to(original)
    with pytest.raises((ValueError, preflight.PreflightError)):
        preflight.read_document(link)
    assert original.read_bytes() == b'{"sentinel":"preserve"}'


def test_internal_output_must_be_ignored_and_fresh(project):
    before = _tree(project)
    unignored = project / "candidate-plan.json"
    with pytest.raises((ValueError, preflight.PreflightError)):
        preflight.write_document(unignored, {"sentinel": "private"}, root=project)
    assert _tree(project) == before
    target = project / "private" / "plan.json"
    preflight.write_document(target, {"sentinel": "first"}, root=project)
    saved = target.read_bytes()
    with pytest.raises((ValueError, preflight.PreflightError)):
        preflight.write_document(target, {"sentinel": "replacement"}, root=project)
    assert target.read_bytes() == saved


@pytest.mark.parametrize("kind", ["leaf", "parent"], ids=["symlink-file", "symlink-parent"])
def test_internal_output_never_follows_redirected_destination(project, tmp_path, kind):
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    (unrelated / "plan.json").write_bytes(b"preserve\r\n")
    private = project / "private"
    if kind == "parent":
        private.symlink_to(unrelated, target_is_directory=True)
    else:
        private.mkdir()
        (private / "plan.json").symlink_to(unrelated / "plan.json")
    with pytest.raises((ValueError, preflight.PreflightError)):
        preflight.write_document(private / "plan.json", {"new": True}, root=project)
    assert (unrelated / "plan.json").read_bytes() == b"preserve\r\n"
    assert list(unrelated.iterdir()) == [unrelated / "plan.json"]


def test_output_cannot_escape_project_root(project, tmp_path):
    target = tmp_path / "private" / "escaped.json"
    with pytest.raises((ValueError, preflight.PreflightError)):
        preflight.write_document(target, {"sentinel": "private"}, root=project)
    assert not target.exists()


def test_untrusted_receipt_commands_are_data_and_cannot_execute(tmp_path, monkeypatch):
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "schema_version": "agent-wiki-local-preflight-receipt/v1",
                "status": "local-ready-hosted-required",
                "command": ["untrusted-executable", "--publish"],
                "hosted": {"result": "success", "run_id": 12345},
            }
        ),
        encoding="utf-8",
    )
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("receipt verification executed a command")

    monkeypatch.setattr(subprocess, "run", forbidden)
    with pytest.raises((ValueError, preflight.PreflightError)):
        preflight.verify_receipt(receipt)
    assert calls == []


def test_local_receipt_cannot_be_hosted_qualification_context(tmp_path, monkeypatch):
    from release import hosted_evidence

    called = []

    def forbidden(*args, **kwargs):
        called.append((args, kwargs))
        raise AssertionError("invalid local context reached remote authority")

    monkeypatch.setattr(hosted_evidence, "GitHub", forbidden)
    forged_local = {
        "schema_version": "agent-wiki-local-preflight-receipt/v1",
        "status": "local-ready-hosted-required",
        "run_attempt": 1,
        "harness_sha256": hashlib.sha256(b"local").hexdigest(),
        "suite_layout": "union",
    }
    with pytest.raises(hosted_evidence.EvidenceError, match="qualification context"):
        hosted_evidence.verify(tmp_path, {}, forged_local, 12345)
    assert called == []


@pytest.mark.parametrize("observed", ["vacant", "occupied", "unavailable"])
def test_registry_observation_is_distinct_from_release_readiness(project, monkeypatch, observed):
    from release import qualification

    actual_run = qualification._run
    calls = []

    def local_only(command, **kwargs):
        assert "ls-remote" not in command
        return actual_run(command, **kwargs)

    def registry(version):
        calls.append(version)
        if observed == "occupied":
            raise qualification.RegistryVersionExists("version already exists on registry")
        if observed == "unavailable":
            raise qualification.QualificationError("registry inspection unavailable")

    monkeypatch.setattr(qualification, "_run", local_only)
    monkeypatch.setattr(qualification, "_check_registry_unused", registry)
    before = _tree(project)
    outcome = qualification.release_eligibility(project, check_registry=True, check_remote=False)
    expected = {
        "vacant": "eligible",
        "occupied": "waiting_release_preparation",
        "unavailable": "blocked_unavailable",
    }
    assert outcome["status"] == expected[observed]
    assert calls == ["9.0.0"]
    assert _tree(project) == before


def test_released_version_is_not_silently_advanced(project, monkeypatch):
    from release import qualification

    _git(project, "tag", "v9.0.0")
    calls = []
    monkeypatch.setattr(qualification, "_check_registry_unused", lambda version: calls.append(version))
    before = _tree(project)
    outcome = qualification.release_eligibility(project, check_registry=True, check_remote=False)
    assert outcome["status"] == "waiting_release_preparation"
    assert outcome["version"] == "9.0.0"
    assert "not newer" in outcome["reason"]
    assert not calls
    assert _tree(project) == before


def test_malformed_changelog_fails_before_external_observation(project, monkeypatch):
    from release import qualification

    (project / "CHANGELOG.md").write_text("# Changelog\n## Unreleased\n", encoding="utf-8")
    calls = []
    monkeypatch.setattr(qualification, "_check_registry_unused", lambda version: calls.append(version))
    outcome = qualification.release_eligibility(project, check_registry=True, check_remote=False)
    assert outcome["status"] == "waiting_release_preparation"
    assert "dated" in outcome["reason"]
    assert not calls


@pytest.fixture
def planned_project(project, monkeypatch):
    """Keep actual Git/file binding while isolating tools and eligibility calls."""
    from release import preflight_contracts

    contract = {
        "identity": "c" * 64,
        "jobs": [
            {
                "id": "native-windows",
                "owner": "release/qualification.py",
                "normal_required": True,
                "environments": ["windows-2025"],
            },
            {
                "id": "hosted-publication",
                "owner": "release/qualification.py",
                "normal_required": True,
                "environments": ["ubuntu-24.04"],
            },
        ],
    }
    monkeypatch.setattr(preflight_contracts, "qualification_contract", lambda root: contract)
    monkeypatch.setattr(preflight, "_version", lambda command, root: {"status": "unavailable", "path": None, "version": None})
    monkeypatch.setattr(preflight, "_eligibility", lambda root, check_registry: {
        "status": "eligible", "version": "9.0.0", "scope": "local-only",
        "external": "remote-tag-and-registry-not-inspected",
    })
    for name, raw in {
        "release/requirements.txt": b"dependency==1.0\n",
        "release/transitive_fixture.py": b"EXPECTED = 1\n",
        "docs/llm_wiki/authored.md": b"# Preserve authored prose\r\n",
        ".llm-wiki/source-selection.json": b'{"include":["src"]}\n',
    }.items():
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    _git(project, "add", ".")
    _git(project, "commit", "--quiet", "-m", "Freeze transitive inputs")
    plan = preflight.create_plan(project, _git(project, "rev-parse", "HEAD"))
    target = project / "private" / "plan.json"
    preflight.write_document(target, plan, root=project)
    return project, target, plan


def test_planning_is_readonly_and_credential_values_are_not_serialized(project, monkeypatch):
    from release import preflight_contracts

    monkeypatch.setenv("GH_TOKEN", "sentinel-private-token-do-not-record")
    monkeypatch.setenv("PYPI_API_TOKEN", "sentinel-private-pypi-do-not-record")
    monkeypatch.setattr(preflight_contracts, "qualification_contract", lambda root: {"jobs": []})
    monkeypatch.setattr(preflight, "_version", lambda command, root: {"status": "unavailable", "path": None, "version": None})
    calls = []

    def offline(root, *, check_registry, check_remote):
        calls.append((check_registry, check_remote))
        assert not check_registry and not check_remote
        return {"status": "eligible", "version": "9.0.0"}

    monkeypatch.setattr(preflight.qualification, "release_eligibility", offline)
    before = _tree(project)
    plan = preflight.create_plan(project, _git(project, "rev-parse", "HEAD"))
    assert _tree(project) == before
    serialized = json.dumps(plan)
    assert "sentinel-private-token" not in serialized
    assert "sentinel-private-pypi" not in serialized
    assert calls == [(False, False)]
    assert plan["readiness"]["external"] == "remote-tag-and-registry-not-inspected"


@pytest.mark.parametrize(
    "relative",
    [
        "app.py",
        "release/requirements.txt",
        "release/transitive_fixture.py",
        "docs/llm_wiki/authored.md",
        ".llm-wiki/source-selection.json",
    ],
    ids=["source", "lock", "transitive-input", "wiki", "selection"],
)
def test_actual_input_mutations_invalidate_plan_before_driver(planned_project, monkeypatch, relative):
    from release import preflight_runner

    root, path, plan = planned_project
    changed = root / relative
    changed.write_bytes(changed.read_bytes() + b"changed\n")
    calls = []
    monkeypatch.setattr(preflight_runner, "execute_stage", lambda *a, **kw: calls.append((a, kw)))
    before = _tree(root)
    with pytest.raises(preflight.PreflightError, match="Stale plan"):
        preflight.run_plan(path, root / "private" / "work")
    assert calls == []
    assert _tree(root) == before
    assert not (root / "private" / "work").exists()
    assert plan["candidate_sha"] == _git(root, "rev-parse", "HEAD")


def test_new_untracked_transitive_input_invalidates_plan(planned_project):
    root, _, plan = planned_project
    (root / "shadow.py").write_text("import os\n", encoding="utf-8")
    with pytest.raises(preflight.PreflightError, match="Stale plan"):
        preflight.validate_plan(plan, root)


def test_new_commit_cannot_retarget_previous_plan(planned_project):
    root, _, plan = planned_project
    (root / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    _git(root, "add", "app.py")
    _git(root, "commit", "--quiet", "-m", "New candidate")
    with pytest.raises(preflight.PreflightError, match="Stale plan"):
        preflight.validate_plan(plan, root)
    assert plan["candidate_sha"] != _git(root, "rev-parse", "HEAD")


def test_plan_cannot_bind_different_checkedout_sha(planned_project):
    root, _, _ = planned_project
    with pytest.raises(preflight.PreflightError, match="SHA differs"):
        preflight.create_plan(root, "1" * 40)


def test_environment_change_requires_new_plan(planned_project, monkeypatch):
    root, _, plan = planned_project
    environment = dict(plan["binding"]["environment"])
    environment["machine"] = "changed-architecture"
    monkeypatch.setattr(preflight, "_environment", lambda root: environment)
    with pytest.raises(preflight.PreflightError, match="Stale plan"):
        preflight.validate_plan(plan, root)


@pytest.mark.parametrize("kind", ["occupied", "symlink"], ids=["unowned-work", "redirected-work"])
def test_prepare_refuses_unowned_work_before_mutation(planned_project, tmp_path, monkeypatch, kind):
    from release import preflight_runner

    root, path, _ = planned_project
    work = root / "private" / "work"
    unrelated = tmp_path / "unrelated-work"
    unrelated.mkdir()
    (unrelated / "preserve").write_bytes(b"user bytes\r\n")
    if kind == "symlink":
        work.symlink_to(unrelated, target_is_directory=True)
    else:
        work.mkdir()
        (work / "preserve").write_bytes(b"user bytes\r\n")
    calls = []
    monkeypatch.setattr(preflight_runner, "execute_stage", lambda *a, **kw: calls.append((a, kw)))
    before = _tree(root)
    with pytest.raises((OSError, ValueError, preflight.PreflightError)):
        preflight.prepare(path, work)
    assert calls == []
    assert _tree(root) == before
    assert (unrelated / "preserve").read_bytes() == b"user bytes\r\n"


def _write_resealed_receipt(path: Path, value: dict) -> None:
    unsigned = {key: item for key, item in value.items() if key != "receipt_hash"}
    raw = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    value = {**unsigned, "receipt_hash": hashlib.sha256(raw).hexdigest()}
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def local_receipt(planned_project, monkeypatch):
    """A real owned attempt with one small trusted stand-in for the driver."""
    from release import preflight_runner
    import sys

    root, plan_path, _ = planned_project
    monkeypatch.setattr(preflight_runner, "launcher_probe", lambda *a, **kw: {"status": "verified"})

    def commands(stage, repo, scratch, **kwargs):
        code = ("from pathlib import Path; "
                f"p=Path({str(scratch / 'dist-a')!r}); p.mkdir(); "
                "(p/'synthetic.whl').write_bytes(b'synthetic local bytes'); print('local fixture')")
        return [preflight_runner.Command("bounded-controller-fixture", (sys.executable, "-c", code), repo)]

    monkeypatch.setattr(preflight_runner, "stage_commands", commands)
    work = root / "private" / "work"
    result = preflight.run_plan(plan_path, work, stages=("contracts",))
    path = Path(result["receipt_path"])
    value = preflight.read_document(path)
    return root, work, path, value


def test_partial_local_run_keeps_native_hosted_and_missing_local_gates_pending(local_receipt):
    root, work, path, value = local_receipt
    assert value["status"] == "blocked"
    assert value["requested_stages"] == ["contracts"]
    assert {gate["id"] for gate in value["pending"]} >= {
        "native-windows", "hosted-publication", "static", "freeze", "host-core", "builds", "artifacts",
    }
    before = _tree(root)
    verified = preflight.verify_receipt(path)
    assert verified["status"] == "blocked"
    assert "no hosted" in verified["qualification"].lower()
    assert _tree(root) == before
    listed = preflight.status(work)
    assert len(listed["receipts"]) == 1
    assert _tree(root) == before


@pytest.mark.parametrize("mutation", ["log", "artifact", "distribution", "omitted-log", "command", "pending", "status"], ids=["changed-log", "changed-output", "changed-distribution", "omitted-log", "rehashed-command", "omitted-hosted-gate", "forged-readiness"])
def test_receipt_cannot_admit_mutated_or_omitted_evidence(local_receipt, mutation):
    root, work, path, value = local_receipt
    attempt = value["attempts"][0]
    if mutation == "log":
        Path(attempt["commands"][0]["log"]).write_bytes(b"different result\n")
    elif mutation == "artifact":
        # The attempt metadata is an independently retained output, not only
        # an in-memory result embedded in the outer receipt.
        Path(attempt["scratch"], "attempt.json").write_text("{}\n", encoding="utf-8")
    elif mutation == "distribution":
        Path(attempt["scratch"], "dist-a", "synthetic.whl").write_bytes(b"substituted distribution")
    elif mutation == "omitted-log":
        relative = Path(attempt["commands"][0]["log"]).relative_to(work).as_posix()
        del value["evidence"][relative]
        _write_resealed_receipt(path, value)
    elif mutation == "command":
        attempt["commands"][0]["argv"] = ["untrusted-executable", "--publish"]
        # An attacker can recompute local hashes. Maintained driver identity,
        # rather than a local seal alone, must reject the substituted argv.
        Path(attempt["scratch"], "attempt.json").write_text(json.dumps(attempt), encoding="utf-8")
        relative = Path(attempt["scratch"], "attempt.json").relative_to(work).as_posix()
        raw = (work / relative).read_bytes()
        value["evidence"][relative] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        _write_resealed_receipt(path, value)
    elif mutation == "pending":
        value["pending"] = [row for row in value["pending"] if row["id"] != "native-windows"]
        _write_resealed_receipt(path, value)
    else:
        value["status"] = "local-ready-hosted-required"
        _write_resealed_receipt(path, value)
    before = _tree(root)
    with pytest.raises((ValueError, preflight.PreflightError)):
        preflight.verify_receipt(path)
    assert _tree(root) == before


def test_failed_attempts_are_retained_when_diagnostic_is_repeated(local_receipt, monkeypatch):
    from release import preflight_runner
    import sys

    root, work, first_path, first = local_receipt
    saved = first_path.read_bytes()

    def failing(stage, repo, scratch, **kwargs):
        return [preflight_runner.Command("bounded-controller-fixture", (sys.executable, "-c", "print('failure'); raise SystemExit(3)"), repo)]

    monkeypatch.setattr(preflight_runner, "stage_commands", failing)
    next_result = preflight.run_plan(root / "private" / "plan.json", work, stages=("contracts",))
    assert next_result["status"] == "failed"
    assert next_result["attempts"][0]["commands"][0]["returncode"] == 3
    assert first_path.read_bytes() == saved
    assert Path(first["attempts"][0]["scratch"], "attempt.json").is_file()
    assert len(list((work / "receipts").glob("*.json"))) == 2


@pytest.mark.parametrize("field,value", [
    ("attempts", "not-a-list"),
    ("attempts", ["not-an-attempt"]),
    ("requested_stages", "contracts"),
    ("operation", {"run": True}),
    ("evidence", []),
    ("pending", {}),
], ids=["attempts-type", "attempt-row-type", "stages-type", "operation-type", "evidence-type", "pending-type"])
def test_cli_refuses_resealed_malformed_receipt_without_traceback(local_receipt, capsys, field, value):
    root, _, path, receipt = local_receipt
    receipt[field] = value
    _write_resealed_receipt(path, receipt)
    before = _tree(root)
    assert preflight.main(["verify", "--receipt", str(path)]) == 2
    diagnostic = json.loads(capsys.readouterr().err)
    assert diagnostic["ok"] is False
    assert diagnostic["error"]
    assert _tree(root) == before


def _write_resealed_plan(path: Path, value: dict) -> None:
    unsigned = {key: item for key, item in value.items() if key != "plan_hash"}
    raw = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    path.write_text(json.dumps({**unsigned, "plan_hash": hashlib.sha256(raw).hexdigest()}), encoding="utf-8")


@pytest.mark.parametrize("field,value", [
    ("root", []),
    ("binding", []),
    ("readiness", None),
    ("readiness", {}),
    ("gates", ["wrong-row"]),
    ("gates", []),
], ids=["root-type", "binding-type", "readiness-type", "missing-readiness-status", "gate-row-type", "omitted-required-gates"])
def test_cli_refuses_resealed_malformed_plan_before_claiming_work(planned_project, capsys, field, value):
    root, path, plan = planned_project
    plan[field] = value
    _write_resealed_plan(path, plan)
    work = root / "private" / "malformed-work"
    before = _tree(root)
    assert preflight.main(["run", "--plan", str(path), "--work", str(work)]) == 2
    diagnostic = json.loads(capsys.readouterr().err)
    assert diagnostic["ok"] is False
    assert _tree(root) == before
    assert not work.exists()


def test_resealed_plan_cannot_discharge_bound_native_owner(planned_project):
    root, _, plan = planned_project
    plan["gates"][0]["release_pending"] = False
    unsigned = {key: item for key, item in plan.items() if key != "plan_hash"}
    raw = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    plan["plan_hash"] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(preflight.PreflightError):
        preflight.validate_plan(plan, root)



def test_new_attempt_keeps_prior_receipt_applicable_to_its_own_evidence(local_receipt):
    root, work, first_path, _ = local_receipt
    before = first_path.read_bytes()
    second = preflight.run_plan(root / "private" / "plan.json", work, stages=("contracts",))
    assert Path(second["receipt_path"]) != first_path
    assert first_path.read_bytes() == before
    assert preflight.verify_receipt(first_path)["status"] == "blocked"
    assert preflight.verify_receipt(Path(second["receipt_path"]))["status"] == "blocked"


@pytest.mark.parametrize("timestamp", ["2000-01-01T00:00:00+00:00", "9999-01-01T00:00:00+00:00", "2026-10-17T00:00:00", "invalid"], ids=["expired", "future", "missing-timezone", "malformed"])
def test_plan_observations_must_be_recent_and_typed(planned_project, timestamp):
    root, path, plan = planned_project
    plan["created_at"] = timestamp
    _write_resealed_plan(path, plan)
    with pytest.raises(preflight.PreflightError, match="timestamp"):
        preflight.validate_plan(preflight.read_document(path), root)


def test_preparation_change_requires_fresh_plan_before_rehearsal(planned_project, monkeypatch):
    from release import preflight_runner
    import sys

    root, path, old_plan = planned_project
    monkeypatch.setattr(preflight_runner, "launcher_probe", lambda *a, **kw: {"status": "verified"})
    target = root / "release" / "requirements.txt"
    calls = []

    def preparation_commands(stage, repo, scratch, **kwargs):
        calls.append(stage)
        code = f"from pathlib import Path; Path({str(target)!r}).write_text('dependency==2.0\\n')"
        return [preflight_runner.Command("explicit-preparation-fixture", (sys.executable, "-c", code), repo)]

    monkeypatch.setattr(preflight_runner, "stage_commands", preparation_commands)
    work = root / "private" / "prepared-work"
    prepared = preflight.prepare(path, work)
    assert prepared["status"] == "blocked"
    assert calls == ["prepare"]
    calls.clear()
    with pytest.raises(preflight.PreflightError, match="Stale plan"):
        preflight.run_plan(path, work)
    assert calls == []
    assert preflight.read_document(path)["plan_hash"] == old_plan["plan_hash"]


def _review_record(sha: str) -> dict:
    from datetime import datetime, timezone

    return {
        "schema_version": "agent-wiki-local-release-review/v1",
        "candidate_sha": sha,
        "version": "9.0.0",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "issues": [
            {"number": 62, "title": "Producer import-gap evidence"},
            {"number": 63, "title": "Additional diagnostics APIs"},
        ],
        "dispositions": [
            {"number": 62, "decision": "resolved", "reason": "Bounded producer contract fixture verifies the correction."},
            {"number": 63, "decision": "deferred", "reason": "Additional APIs remain separately scoped follow-up work."},
        ],
        "semver": {
            "baseline": "8.0.0",
            "target": "9.0.0",
            "reason": "Reviewed default-wire behavior change requires a major release.",
        },
    }


def test_explicit_candidate_review_is_bound_without_granting_hosted_approval(planned_project):
    root, _, original = planned_project
    review = root / "private" / "release-review.json"
    record = _review_record(original["candidate_sha"])
    preflight.write_document(review, record, root=root)
    before = _tree(root)
    plan = preflight.create_plan(root, original["candidate_sha"], review_file=review)
    preflight.validate_plan(plan, root)
    captured = plan["readiness"]["review"]
    assert captured["status"] == "recorded"
    assert captured["record"] == record
    assert captured["sha256"] == hashlib.sha256(review.read_bytes()).hexdigest()
    assert "not independent approval" in captured["qualification"]
    assert all(row["release_pending"] for row in plan["gates"])
    assert _tree(root) == before


@pytest.mark.parametrize(
    "mutation",
    ["missing-issue", "wrong-candidate", "wrong-version", "wrong-target", "expired", "duplicate-issue", "duplicate-decision"],
)
def test_candidate_review_refuses_missing_or_inapplicable_decisions(planned_project, mutation):
    root, _, original = planned_project
    review = root / "private" / "release-review.json"
    record = _review_record(original["candidate_sha"])
    if mutation == "missing-issue":
        record["dispositions"].pop()
    elif mutation == "wrong-candidate":
        record["candidate_sha"] = "1" * 40
    elif mutation == "wrong-version":
        record["version"] = "10.0.0"
    elif mutation == "wrong-target":
        record["semver"]["target"] = "10.0.0"
    elif mutation == "expired":
        record["observed_at"] = "2000-01-01T00:00:00+00:00"
    elif mutation == "duplicate-issue":
        record["issues"].append(dict(record["issues"][0]))
    else:
        record["dispositions"].append(dict(record["dispositions"][0]))
    preflight.write_document(review, record, root=root)
    before = _tree(root)
    with pytest.raises(preflight.PreflightError):
        preflight.create_plan(root, original["candidate_sha"], review_file=review)
    assert _tree(root) == before


def test_altered_review_invalidates_original_plan_even_if_record_still_valid(planned_project):
    root, _, original = planned_project
    review = root / "private" / "release-review.json"
    record = _review_record(original["candidate_sha"])
    preflight.write_document(review, record, root=root)
    plan = preflight.create_plan(root, original["candidate_sha"], review_file=review)
    record["dispositions"][1]["reason"] = "A different post-freeze disposition."
    review.write_text(json.dumps(record), encoding="utf-8")
    before = _tree(root)
    with pytest.raises(preflight.PreflightError, match="review changed"):
        preflight.validate_plan(plan, root)
    assert _tree(root) == before


@pytest.mark.parametrize("review_state", ["missing", "blocker"])
def test_missing_or_blocking_review_prevents_full_driver_execution(planned_project, monkeypatch, review_state):
    from release import preflight_runner

    root, plan_path, original = planned_project
    if review_state == "blocker":
        review = root / "private" / "release-review.json"
        record = _review_record(original["candidate_sha"])
        record["dispositions"][0]["decision"] = "blocker"
        preflight.write_document(review, record, root=root)
        plan = preflight.create_plan(root, original["candidate_sha"], review_file=review)
        assert plan["readiness"]["review"]["status"] == "blocked"
        plan_path = root / "private" / "blocked-plan.json"
        preflight.write_document(plan_path, plan, root=root)
    calls = []
    monkeypatch.setattr(preflight_runner, "execute_stage", lambda *a, **kw: calls.append((a, kw)))
    result = preflight.run_plan(plan_path, root / "private" / "review-blocked-work")
    assert result["status"] == "blocked"
    assert calls == []
    assert result["attempts"][0]["stage"] == "readiness"
    assert all(row["release_pending"] for row in result["plan"]["gates"])
