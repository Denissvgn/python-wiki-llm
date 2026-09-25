"""Lock, fresh-environment, cache-save and nonqualification workflow boundaries."""

from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]


def workflow(name):
    return yaml.safe_load((ROOT / ".github/workflows" / name).read_text())


def named(job, name):
    return next(step for step in job["steps"] if step.get("name") == name)


def test_both_builders_use_identical_small_tools_before_separate_validation():
    value = workflow("release-qualification.yml")
    jobs = value["jobs"]
    job = jobs["build"]
    assert job["strategy"]["matrix"]["include"] == [
        {"copy": "a", "validate": True},
        {"copy": "b", "validate": False},
    ]
    steps = job["steps"]
    build = named(job, "Build both independent distributions")
    setup = named(job, "Install verified build tools into the fresh environment")
    assert setup.get("if") is None
    assert "--lock candidate/release/build-requirements.txt" in setup["run"]
    assert "candidate/release/requirements.txt" not in str(job)
    assert (
        steps.index(setup)
        < steps.index(build)
        < steps.index(named(job, "Create a separate fresh validation environment"))
    )
    validation = named(
        job, "Install verified validation tools into the fresh environment"
    )
    assert validation["if"] == "${{ matrix.validate }}"
    assert "--lock candidate/release/validation-requirements.txt" in validation["run"]
    check = named(job, "Validate the first independent build")["run"]
    assert (
        "twine check dist/*" in check
        and "verify_installed_knowledge_schema.py dist --no-build-isolation" in check
    )
    assert "release/dependency_downloads.py" in str(jobs["freeze"]["steps"])


def test_release_cache_is_opt_in_hash_checked_and_never_an_installed_environment():
    value = workflow("release-qualification.yml")
    events = value.get("on", value.get(True))
    assert (
        events["workflow_dispatch"]["inputs"]["third-party-download-cache"]["default"]
        is False
    )
    assert "inputs.third-party-download-cache" in value["concurrency"]["group"]
    job = value["jobs"]["build"]
    for profile in ("build", "validation"):
        restore = named(job, f"Restore {profile} third-party downloads")
        save = named(job, f"Save verified {profile} third-party downloads")
        assert (
            restore["continue-on-error"] is True and save["continue-on-error"] is True
        )
        assert restore["with"] == save["with"]
        assert "restore-keys" not in restore["with"]
        assert (
            restore["with"]["path"]
            == "${{ runner.temp }}/third-party-downloads/" + profile
        )
        assert (
            restore["with"]["key"]
            == "${{ steps." + profile + "-identity.outputs.cache-key }}"
        )
        assert "github.event_name == 'workflow_dispatch'" in save["if"]
        assert "github.ref_type == 'branch'" in save["if"]
        assert (
            "!github.event.repository.fork" in save["if"]
            and "matrix.copy == 'a'" in save["if"]
        )
        assert "cache-ready" in save["if"]
        setup = named(
            job, f"Install verified {profile} tools into the fresh environment"
        )
        assert "--no-cache-available" in setup["run"] and not setup.get(
            "continue-on-error", False
        )
    upload = named(job, "Retain dependency setup and cache diagnostics")
    assert "/wheels" not in upload["with"]["path"]
    assert "setup.json" in upload["with"]["path"] and upload["if"] == "${{ always() }}"


def test_probe_proves_all_cases_and_reserves_cache_service_writes_for_manual_runs():
    value = workflow("dependency-setup-check.yml")
    events = value.get("on", value.get(True))
    assert set(events) == {"pull_request", "workflow_dispatch"}
    assert value["permissions"] == {"contents": "read"}
    jobs = value["jobs"]
    controls = jobs["controls"]
    assert (
        "for mode in baseline cold warm stale corrupt unavailable"
        in named(controls, "Exercise full-lock baseline and every isolated cache path")[
            "run"
        ]
    )
    for step in controls["steps"]:
        if step.get("uses", "").startswith("actions/cache/save@"):
            assert "github.event_name == 'workflow_dispatch'" in step["if"]
            assert (
                "github.ref_type == 'branch'" in step["if"]
                and "!github.event.repository.fork" in step["if"]
            )
            assert "third-party-downloads/" in step["with"]["path"]
    warm = jobs["warm"]
    assert set(warm["needs"]) == {"freeze", "controls"}
    assert "github.event_name == 'workflow_dispatch'" in warm["if"]
    for step in warm["steps"]:
        if step.get("uses", "").startswith("actions/cache/restore@"):
            assert step["with"]["fail-on-cache-miss"] is True
    run = named(warm, "Require actual hits and compare fresh warm builders")["run"]
    assert (
        'test "${BUILD_HIT}" = "true"' in run
        and 'test "${VALIDATION_HIT}" = "true"' in run
    )
    assert "--cache-restore-seconds" in run
    assert "build-bundle" not in str(value) and "finalize-promotion" not in str(value)
