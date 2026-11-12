"""Cleanup owns exact allocated trees and preserves proof and live consumers."""

import json
from types import SimpleNamespace
import uuid

import pytest

from release import release_resources as r
from tests.test_manual_release import Remote, session
from tests.test_manual_release import project as project


def inactive(paths):
    return {
        "host": {str(p): {"status": "inactive", "pids": []} for p in paths},
        "docker": {"status": "observed", "containers": [], "mounts": []},
    }


@pytest.fixture
def resources(project):
    controller, state = session(project, Remote())
    for _ in range(11):
        controller.advance()
    state = controller.store.load()
    identifier = uuid.uuid4().hex
    work = controller.store.work / ("preflight-" + identifier)
    work.mkdir()
    state["preparation"] = {
        "status": "verified",
        "plan": str(project / "private/plan.json"),
        "plan_hash": "a" * 64,
        "attempts": [{"id": identifier, "work": str(work), "status": "verified"}],
    }
    controller.store.save(state, "local-fixture-catalog")
    attempt_id = str(uuid.uuid4())
    scratch = work / ("attempt-" + attempt_id)
    scratch.mkdir()
    (scratch / "attempt.json").write_text(json.dumps({"status": "passed"}))
    paths = []
    external = project / "private/base-runtime"
    external.write_bytes(b"reusable runtime must survive")
    for index in range(2):
        path = scratch / ("environment-" + str(index))
        ticket = r.begin_allocation(
            scratch,
            work=work,
            binding={"root": str(project)},
            candidate_sha=state["candidate_sha"],
            attempt_id=attempt_id,
            role="create-environment",
            path=path,
        )
        path.mkdir()
        (path / "pyvenv.cfg").write_text("home = immutable-runtime\n")
        (path / "bin").mkdir()
        (path / "bin/python").symlink_to(external)
        (path / "provider.py").write_bytes(b"exact installed candidate\n")
        r.finish_allocation(ticket, outcome="passed", runtime={"python": "3.14"})
        paths.append(path)
    return controller, paths, scratch, external


def test_preview_is_read_only_and_apply_preserves_receipts_catalog_and_link_target(
    resources,
):
    controller, paths, scratch, external = resources
    before = {
        p: p.read_bytes()
        for p in [
            controller.store.work / "state.json",
            controller.store.work / "events.jsonl",
            scratch / "resources.json",
        ]
    }
    plan = r.preview(controller.store, scanner=inactive)
    assert [row["status"] for row in plan["resources"]] == ["remove", "remove"]
    assert all(p.exists() for p in paths)
    assert all(p.read_bytes() == raw for p, raw in before.items())
    result = r.apply(controller.store, plan, plan["plan_sha256"], scanner=inactive)
    assert result["status"] == "complete" and all(not p.exists() for p in paths)
    assert all(p.read_bytes() == raw for p, raw in before.items())
    assert external.read_bytes() == b"reusable runtime must survive"
    assert (
        r.apply(controller.store, plan, plan["plan_sha256"], scanner=inactive)["status"]
        == "complete"
    )


@pytest.mark.parametrize(
    "kind", ["host-active", "host-unknown", "docker-active", "docker-unknown"]
)
def test_active_or_inconclusive_consumers_are_retained(resources, kind):
    controller, paths, *_ = resources

    def scan(values):
        result = inactive(values)
        if kind.startswith("host"):
            for p in values:
                result["host"][str(p)]["status"] = (
                    "active" if kind.endswith("active") else "unknown"
                )
        elif kind == "docker-unknown":
            result["docker"]["status"] = "unknown"
        else:
            result["docker"]["mounts"] = [
                {
                    "container_id": "stopped-consumer",
                    "running": False,
                    "source": str(controller.store.root),
                }
            ]
        return result

    plan = r.preview(controller.store, scanner=scan)
    assert all(row["status"] == "retain" for row in plan["resources"])
    assert all(p.exists() for p in paths)


@pytest.mark.parametrize(
    "fault",
    [
        "edit",
        "extra",
        "replacement",
        "plan",
        "protected",
        "producer-lock",
        "release-lease",
        "late-consumer",
    ],
)
def test_stale_or_occupied_cleanup_is_refused_before_any_deletion(resources, fault):
    controller, paths, scratch, external = resources
    plan = r.preview(controller.store, scanner=inactive)
    approved = plan["plan_sha256"]
    scanner = inactive
    if fault == "edit":
        (paths[1] / "provider.py").write_bytes(b"foreign update")
    elif fault == "extra":
        (paths[1] / "unexpected").write_bytes(b"keep")
    elif fault == "replacement":
        paths[1].rename(paths[1].with_name("retained-old-root"))
        paths[1].mkdir()
        (paths[1] / "keep").write_bytes(b"different owner")
    elif fault == "plan":
        plan["resources"][0]["path"] = str(external.parent)
    elif fault == "protected":
        with (controller.store.work / "events.jsonl").open("ab") as stream:
            stream.write(b"changed evidence\n")
    elif fault == "producer-lock":
        (scratch.parent / ".execution-lock").write_text("active")
    elif fault == "release-lease":
        controller.store.claim(controller.store.load())
    else:

        def scanner(paths):
            result = inactive(paths)
            for p in paths:
                result["host"][str(p)] = {"status": "active", "pids": ["123"]}
            return result

    with pytest.raises(ValueError):
        r.apply(controller.store, plan, approved, scanner=scanner)
    assert all(p.exists() for p in paths)


def test_nonpassing_producer_is_retained_even_without_live_consumers(resources):
    controller, paths, scratch, _ = resources
    (scratch / "attempt.json").write_text(json.dumps({"status": "failed"}))
    value = r.preview(controller.store, scanner=inactive)
    assert all(
        row["status"] == "retain"
        and row["reason"] == "retention-pin-or-nonpassing-producer"
        for row in value["resources"]
    )
    assert all(p.exists() for p in paths)


def test_cleanup_cannot_start_before_recorded_public_verification(resources):
    controller, paths, *_ = resources
    state = controller.store.load()
    state["phase"] = "github-released"
    controller.store.save(state, "not-publicly-verified")
    with pytest.raises(ValueError, match="public verification"):
        r.preview(controller.store, scanner=inactive)
    assert all(p.exists() for p in paths)


def test_interrupted_cleanup_reconciles_only_its_recorded_removals(
    resources, monkeypatch
):
    from llm_wiki_cli.services import filesystem_guard

    controller, paths, *_ = resources
    plan = r.preview(controller.store, scanner=inactive)
    original = filesystem_guard.remove_guarded_tree
    calls = 0

    def interrupted(path, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("retained interrupted cleanup")
        return original(path, **kwargs)

    monkeypatch.setattr(filesystem_guard, "remove_guarded_tree", interrupted)
    with pytest.raises(OSError, match="interrupted"):
        r.apply(controller.store, plan, plan["plan_sha256"], scanner=inactive)
    assert not paths[0].exists() and paths[1].exists()
    monkeypatch.setattr(filesystem_guard, "remove_guarded_tree", original)
    assert (
        r.apply(controller.store, plan, plan["plan_sha256"], scanner=inactive)["status"]
        == "complete"
    )
    assert not paths[1].exists()


def test_unstarted_missing_destination_is_not_claimed_as_success(resources):
    from llm_wiki_cli.services.filesystem_guard import remove_guarded_tree

    controller, paths, *_ = resources
    plan = r.preview(controller.store, scanner=inactive)
    remove_guarded_tree(paths[1])
    with pytest.raises(ValueError, match="unstarted"):
        r.apply(controller.store, plan, plan["plan_sha256"], scanner=inactive)
    assert paths[0].exists()


def test_retention_changes_leave_sealed_catalog_unchanged_and_invalidate_old_plan(resources):
    controller, paths, scratch, _ = resources
    before = (scratch / "resources.json").read_bytes()
    plan = r.preview(controller.store, scanner=inactive)
    identifier = plan["resources"][0]["resource_id"]
    r.pin(controller.store, identifier, "Retain for review", keep=True)
    assert (scratch / "resources.json").read_bytes() == before
    with pytest.raises(ValueError, match="Protected evidence changed"):
        r.apply(controller.store, plan, plan["plan_sha256"], scanner=inactive)
    pinned = r.preview(controller.store, scanner=inactive)
    assert pinned["resources"][0]["status"] == "retain"
    r.pin(controller.store, identifier, "Review finished", keep=False)
    assert (scratch / "resources.json").read_bytes() == before
    assert r.preview(controller.store, scanner=inactive)["resources"][0]["status"] == "remove"
    assert all(p.exists() for p in paths)


def test_resealed_plan_cannot_invent_ownership_of_an_unregistered_tree(resources):
    from llm_wiki_cli.services.filesystem_guard import guarded_tree_manifest

    controller, paths, scratch, _ = resources
    plan = r.preview(controller.store, scanner=inactive)
    foreign = scratch / "unregistered"
    foreign.mkdir()
    (foreign / r.MARKER).write_bytes(b"not an allocation ticket")
    row = plan["resources"][0]
    row.update(path=str(foreign), identity=r._identity(foreign),
               marker_sha256=r.hosted.sha256((foreign / r.MARKER).read_bytes()),
               manifest=[list(entry) for entry in guarded_tree_manifest(foreign)])
    plan["plan_sha256"] = r.hosted.sha256(r.manual.canonical({k: v for k, v in plan.items() if k != "plan_sha256"}))
    with pytest.raises(ValueError, match="differs from the disposable allocation"):
        r.apply(controller.store, plan, plan["plan_sha256"], scanner=inactive)
    assert foreign.exists() and all(p.exists() for p in paths)


def test_legacy_unregistered_prefixes_are_visible_but_never_adopted(resources):
    controller, paths, scratch, _ = resources
    legacy = scratch / "older-environment"
    legacy.mkdir()
    (scratch / "attempt.json").write_text(json.dumps({"status": "passed", "candidate_sha": controller.store.load()["candidate_sha"],
        "commands": [{"name": "legacy", "argv": ["driver", "create-venv", "--path", str(legacy)]}]}))
    plan = r.preview(controller.store, scanner=inactive)
    retained = next(row for row in plan["resources"] if row["path"] == str(legacy))
    assert retained["status"] == "retain" and retained["reason"] == "unregistered-legacy-allocation"
    assert not (legacy / r.MARKER).exists() and all(p.exists() for p in paths)


@pytest.mark.parametrize("fault", ["missing-tools", "host-timeout", "docker-timeout"])
def test_consumer_scanner_does_not_turn_unavailable_tools_into_inactivity(resources, monkeypatch, fault):
    _, paths, *_ = resources
    monkeypatch.setattr(r.shutil, "which", lambda tool: None if fault == "missing-tools" else tool)

    def command(argv, **_kwargs):
        if argv[0] == "lsof":
            return None if fault == "host-timeout" else SimpleNamespace(returncode=1, stdout="", stderr="")
        return None if fault == "docker-timeout" else SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(r, "_command", command)
    observed = r.scan_consumers(paths)
    assert all(not r._inactive(path, observed) for path in paths)


@pytest.mark.parametrize("prefix", ["/host_mnt", "/run/desktop/mnt/host", ""])
def test_docker_desktop_alias_cannot_hide_a_stopped_host_bind_consumer(resources, prefix):
    controller, paths, *_ = resources

    def scan(values):
        result = inactive(values)
        result["docker"]["mounts"] = [{"container_id": "stopped-bind-consumer", "running": False,
                                        "source": prefix + str(controller.store.root)}]
        return result

    plan = r.preview(controller.store, scanner=scan)
    assert all(row["status"] == "retain" for row in plan["resources"])
    assert all(path.exists() for path in paths)


def test_host_filesystem_alias_is_resolved_before_mount_overlap(resources):
    controller, paths, scratch, _ = resources
    alias = controller.store.root / "private/mount-alias"
    alias.symlink_to(scratch, target_is_directory=True)
    observed = inactive(paths)
    observed["docker"]["mounts"] = [{"source": str(alias), "running": False}]
    assert all(not r._inactive(path, observed) for path in paths)
