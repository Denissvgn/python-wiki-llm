"""Release-session authority, interruption and literal public-byte boundaries."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import zipfile

import pytest
import yaml

from release import manual_release as manual


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), "-c", "user.name=Release control",
        "-c", "user.email=release@example.invalid", *args], text=True).strip()


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "candidate"
    root.mkdir()
    git(root, "init", "-q")
    (root / ".gitignore").write_text("private/\n")
    (root / "pyproject.toml").write_text('[project]\nname="agent-wiki-cli"\nversion="9.0.0"\n')
    (root / "CHANGELOG.md").write_text("## [9.0.0] - 2026-11-05\n\nProduct behavior.\n")
    git(root, "add", ".")
    git(root, "commit", "-qm", "Candidate")
    return root


class Remote:
    def __init__(self):
        self.writes = []
        self.results = {}
        self.lose_after_accept = None
        self.lose_before_accept = False
        self.public_ready = True
        self.admitted = True

    def admit(self, state):
        return {"admitted": self.admitted, "blockers": [] if self.admitted else ["tool one", "tool two"]}

    def prepare(self, state, action):
        return {"run_ids": []}

    def perform(self, state, pending):
        action = pending["action"]
        self.writes.append((action, state["candidate_sha"]))
        if self.lose_before_accept:
            raise TimeoutError("Response unavailable")
        self.results[action] = {"verified": True, "candidate_sha": state["candidate_sha"],
                                "version": state["version"], "run_id": 42}
        if self.lose_after_accept == action:
            raise TimeoutError("Server accepted but response was lost")
        return {"run_id": 42}

    def reconcile(self, state, pending):
        return self.results.get(pending["action"])

    def check_bundle(self, state):
        return {}

    def verify_public(self, state):
        return {"verified": self.public_ready}


def session(root, remote, scopes=manual.ACTIONS, name="one"):
    store = manual.Store(root, root / "private" / name)
    controller = manual.Controller(store, remote)
    state = controller.initialize("example/agent-wiki", git(root, "rev-parse", "HEAD"), authorize=tuple(scopes))
    return controller, state


def test_complete_release_performs_each_authorized_operation_once(project):
    remote = Remote()
    controller, initial = session(project, remote)
    phases = []
    for _ in range(11):
        phases.append(controller.advance()["phase"])
    assert phases == ["prepared", "qualified", "qualified", "dry-run-verified", "dry-run-verified",
                      "tagged", "tagged", "published", "published", "github-released", "complete"]
    assert remote.writes == [(action, initial["candidate_sha"]) for action in manual.ACTIONS]
    assert controller.advance()["phase"] == "complete"
    assert len(remote.writes) == 5
    assert not controller.store.lease.exists()


@pytest.mark.parametrize("action", ["qualify", "dry-run", "publish"])
def test_lost_dispatch_response_is_adopted_without_another_post(project, action):
    remote = Remote()
    controller, _ = session(project, remote)
    while manual.NEXT[controller.store.load()["phase"]] != action:
        controller.advance()
        controller.advance()
    remote.lose_after_accept = action
    uncertain = controller.advance()
    assert uncertain["pending"]["outcome_unknown"]
    assert controller.advance()["pending"] is None
    assert [a for a, _ in remote.writes].count(action) == 1


def test_absent_dispatch_remains_pending_without_retries(project):
    remote = Remote()
    remote.lose_before_accept = True
    controller, _ = session(project, remote)
    controller.advance()
    for _ in range(4):
        state = controller.advance()
        assert state["observation"] == "awaiting_remote_visibility_or_completion"
    assert len(remote.writes) == 1
    assert state["pending"]["outcome_unknown"]


def test_qualification_authority_does_not_authorize_tag_or_publication(project):
    remote = Remote()
    controller, _ = session(project, remote, scopes=("qualify",))
    controller.advance()
    controller.advance()
    state = controller.advance()
    assert state["observation"] == "authorized-scope-complete" and state["next_action"] == "dry-run"
    assert [a for a, _ in remote.writes] == ["qualify"]
    controller.advance(authorize=("dry-run",))
    controller.advance()
    assert controller.advance()["next_action"] == "tag"
    assert [a for a, _ in remote.writes] == ["qualify", "dry-run"]


def test_source_change_invalidates_session_before_any_remote_write(project):
    remote = Remote()
    controller, _ = session(project, remote)
    (project / "changed.txt").write_text("new source")
    git(project, "add", ".")
    git(project, "commit", "-qm", "New candidate")
    with pytest.raises(manual.SessionError, match="source changed"):
        controller.advance()
    assert not remote.writes


def test_raw_index_metadata_is_not_the_source_identity(project):
    remote = Remote()
    controller, _ = session(project, remote)
    git(project, "update-index", "--index-version=4")
    assert controller.advance()["pending"]["action"] == "qualify"


def test_new_candidate_requires_explicit_old_session_supersession(project):
    remote = Remote()
    first, _ = session(project, remote)
    (project / "next.txt").write_text("new")
    git(project, "add", ".")
    git(project, "commit", "-qm", "Next source")
    with pytest.raises(manual.SessionError, match="Another release candidate"):
        session(project, remote, name="two")
    first.supersede("Candidate corrected before qualification")
    second, _ = session(project, remote, name="two")
    assert second.advance()["pending"]["action"] == "qualify"
    assert first.advance()["phase"] == "superseded"


def test_irreversible_unknown_operation_cannot_be_superseded(project):
    remote = Remote()
    controller, _ = session(project, remote)
    for _ in range(4):
        controller.advance()
    remote.lose_before_accept = True
    controller.advance()
    with pytest.raises(manual.SessionError, match="irreversible"):
        controller.supersede("Do not hide unresolved tag write")


def test_failed_remote_run_is_recorded_and_never_replayed(project):
    remote = Remote()
    controller, _ = session(project, remote)
    controller.advance()
    remote.results["qualify"] = {"failed": True, "run_id": 42, "conclusion": "failure"}
    failed = controller.advance()
    assert failed["observation"] == "remote-failed"
    assert failed["pending"]["failure"]["run_id"] == 42
    assert controller.advance()["revision"] == failed["revision"]
    assert len(remote.writes) == 1


def test_public_verification_failure_does_not_repeat_upload(project):
    remote = Remote()
    controller, _ = session(project, remote)
    for _ in range(10):
        controller.advance()
    remote.public_ready = False
    with pytest.raises(manual.SessionError, match="Public release verification"):
        controller.advance()
    assert controller.store.load()["phase"] == "github-released"
    remote.public_ready = True
    assert controller.advance()["phase"] == "complete"
    assert [a for a, _ in remote.writes].count("publish") == 1


def test_missing_preparation_admission_blocks_expensive_dispatch(project):
    remote = Remote()
    remote.admitted = False
    controller, _ = session(project, remote)
    blocked = controller.advance()
    assert blocked["observation"] == "preparation-blocked"
    assert blocked["admission"]["blockers"] == ["tool one", "tool two"]
    assert controller.store.load()["admission"] == blocked["admission"]
    assert not remote.writes


@pytest.mark.parametrize("finished", ["complete", "superseded"])
def test_crash_after_terminal_state_save_releases_owned_lease_on_resume(project, monkeypatch, finished):
    remote = Remote()
    controller, _ = session(project, remote)
    release = controller.store.release

    def crash(_):
        raise OSError("Interrupted after terminal state was saved")

    monkeypatch.setattr(controller.store, "release", crash)
    if finished == "complete":
        for _ in range(10):
            controller.advance()
        operation = controller.advance
    else:
        def operation():
            return controller.supersede("Another candidate")
    with pytest.raises(OSError, match="Interrupted"):
        operation()
    assert controller.store.load()["phase"] == finished and controller.store.lease.exists()
    monkeypatch.setattr(controller.store, "release", release)
    assert controller.advance()["phase"] == finished
    assert not controller.store.lease.exists()
    session(project, remote, name="next")


def test_partial_release_repair_validates_existing_assets_before_upload(project, monkeypatch):
    api = backend(project, None)
    notes = api.work / "notes.md"
    notes.write_text("Product behavior.\n")
    monkeypatch.setattr(api, "check_bundle", lambda state: {"tag": "v9.0.0", "artifacts": [
        {"filename": "wheel.whl", "sha256": "a" * 64}, {"filename": "source.tar.gz", "sha256": "b" * 64}]})
    monkeypatch.setattr(api, "_notes", lambda state: notes)
    monkeypatch.setattr(api, "_release_metadata", lambda *a: None)
    monkeypatch.setattr(api, "_assets", lambda state: {"wheel.whl": "a" * 64, "source.tar.gz": "b" * 64, "SHA256SUMS": "c" * 64})
    monkeypatch.setattr(api, "_release", lambda tag: {"id": 1, "assets": [
        {"name": "wheel.whl", "state": "uploaded", "digest": "sha256:" + "f" * 64}]})
    writes = []
    monkeypatch.setattr(manual.subprocess, "run", lambda *a, **k: writes.append(a))
    with pytest.raises(manual.SessionError, match="digest differs"):
        api.perform({"candidate_sha": "1" * 40, "qualification": {"bundle": str(api.work)}}, {"action": "github-release"})
    assert not writes


def test_session_tampering_and_linked_work_are_rejected(project, tmp_path):
    remote = Remote()
    controller, _ = session(project, remote)
    path = controller.store.work / "state.json"
    value = json.loads(path.read_text())
    value["phase"] = "tagged"
    path.write_text(json.dumps(value))
    with pytest.raises(manual.SessionError, match="state changed"):
        controller.advance()
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(manual.SessionError, match="links"):
        manual.Store(project, project / "linked" / "work")
    assert list(outside.iterdir()) == []


def test_cross_process_lock_is_released_by_close(project):
    one = manual.Store(project, project / "private/one")
    two = manual.Store(project, project / "private/two")
    with one.lock():
        with pytest.raises(manual.SessionError, match="transition is active"):
            with two.lock():
                raise AssertionError("Second writer acquired the lease")
    with two.lock():
        pass


def backend(root, remote):
    value = manual.GitHubBackend.__new__(manual.GitHubBackend)
    value.root, value.work, value.repository, value.token = root, root / "private/download", "example/agent-wiki", "secret"
    value.work.mkdir(parents=True)
    value.client = remote
    return value


def test_public_download_uses_octets_and_never_forwards_credentials(project, monkeypatch):
    api = backend(project, None)
    calls = []
    raw = b"actual public artifact"

    def transport(url, token, limit, *, media_type):
        calls.append((url, token, limit, media_type))
        if len(calls) == 1:
            return 302, {"Location": "https://release-assets.githubusercontent.com/signed"}, b""
        return 200, {}, raw

    monkeypatch.setattr(manual.hosted, "_http", transport)
    api._public_bytes("github", "distribution.whl", "https://api.github.com/repos/example/agent-wiki/releases/assets/1",
                      len(raw), hashlib.sha256(raw).hexdigest(), authenticated=True)
    assert calls[0][1] == "secret" and calls[1][1] is None
    assert all(c[3] == "application/octet-stream" for c in calls)
    assert (api.work / "public-downloads/github/distribution.whl").read_bytes() == raw


def test_public_download_rejects_bad_hash_and_official_host_redirect_escape(project, monkeypatch):
    api = backend(project, None)
    monkeypatch.setattr(manual.hosted, "_http", lambda *a, **k: (200, {}, b"bad"))
    with pytest.raises(manual.SessionError, match="bytes differ"):
        api._public_bytes("pypi", "source.tar.gz", "https://files.pythonhosted.org/source", 3, "a" * 64)
    monkeypatch.setattr(manual.hosted, "_http", lambda *a, **k: (302, {"Location": "https://unrelated.invalid/file"}, b""))
    with pytest.raises(manual.SessionError, match="redirect"):
        api._public_bytes("pypi", "source.tar.gz", "https://files.pythonhosted.org/source", 3, "a" * 64)
    assert not (api.work / "public-downloads").exists()


def test_tag_push_destination_must_equal_session_repository(project):
    git(project, "remote", "add", "origin", "git@github.com:unrelated/repository.git")
    api = backend(project, None)
    with pytest.raises(manual.SessionError, match="push destination"):
        api._origin()


def test_reader_must_execute_from_candidate_checkout(project):
    with pytest.raises(manual.SessionError, match="maintained readers"):
        manual.GitHubBackend(project, project / "private/readers", "example/agent-wiki", "secret")


def artifact_zip(name="decision.json"):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        info = zipfile.ZipInfo(name)
        info.create_system = 3
        info.external_attr = (stat.S_IFREG | 0o644) << 16
        archive.writestr(info, b"{}")
    return stream.getvalue()


@pytest.mark.parametrize("unsafe", [False, True], ids=["complete", "traversal"])
def test_artifact_materialization_is_canonical_and_ignores_incomplete_attempts(project, unsafe):
    raw = artifact_zip("../escape.json" if unsafe else "decision.json")
    sha = git(project, "rev-parse", "HEAD")
    run = {"id": 42, "run_attempt": 1, "repository": {"id": 7}, "head_repository": {"id": 7}}
    artifact = {"id": 11, "name": "promotion-decision", "expired": False, "size_in_bytes": len(raw),
                "digest": "sha256:" + hashlib.sha256(raw).hexdigest(), "created_at": "2026-11-05T01:01:00Z",
                "updated_at": "2026-11-05T01:01:00Z", "workflow_run": {"id": 42, "head_sha": sha, "repository_id": 7, "head_repository_id": 7}}
    producer = {"name": "Verify qualified promotion input", "conclusion": "success", "head_sha": sha,
                "run_id": 42, "run_attempt": 1, "started_at": "2026-11-05T01:00:00Z", "completed_at": "2026-11-05T01:02:00Z"}

    class Client:
        def list(self, path, key):
            return [artifact] if key == "artifacts" else [producer]

        def archive(self, identity):
            assert identity == 11
            return raw

    api = backend(project, Client())
    incomplete = api.work / "promotion-decision-42-1.incomplete-retained"
    incomplete.mkdir()
    (incomplete / "partial").write_text("preserve failure")
    if unsafe:
        with pytest.raises(ValueError):
            api._artifact({"candidate_sha": sha}, run, "promotion-decision", producer["name"])
        assert not (api.work / "escape.json").exists()
    else:
        folder = api._artifact({"candidate_sha": sha}, run, "promotion-decision", producer["name"])
        assert (folder / "decision.json").read_bytes() == b"{}"
        assert api._artifact({"candidate_sha": sha}, run, "promotion-decision", producer["name"]) == folder
        archive_path = folder.parent / "artifact.zip"
        archive_path.write_bytes(raw + b"oversized")
        with pytest.raises(manual.SessionError, match="transport identity"):
            api._artifact({"candidate_sha": sha}, run, "promotion-decision", producer["name"])
        archive_path.unlink()
        external = api.work / "external.zip"
        external.write_bytes(raw)
        archive_path.symlink_to(external)
        with pytest.raises(manual.SessionError, match="links"):
            api._artifact({"candidate_sha": sha}, run, "promotion-decision", producer["name"])
        assert external.read_bytes() == raw
    assert (incomplete / "partial").read_text() == "preserve failure"


def test_publication_is_serialized_without_cancelling_an_inflight_upload():
    workflow = yaml.safe_load((Path(__file__).parents[1] / ".github/workflows/publish.yml").read_text())
    assert workflow["concurrency"] == {"group": "publish-agent-wiki-cli-${{ github.repository }}", "cancel-in-progress": False}


def test_no_remote_side_effect_from_init_status_or_ungranted_advance(project):
    remote = Remote()
    controller, initial = session(project, remote, scopes=())
    assert controller.store.load()["session_id"] == initial["session_id"]
    assert controller.advance()["observation"] == "awaiting_authorization"
    assert not remote.writes


def test_pending_stage_cannot_adopt_another_candidates_result(project):
    remote = Remote()
    controller, _ = session(project, remote)
    controller.advance()
    wrong = deepcopy(remote.results["qualify"])
    wrong["candidate_sha"] = "f" * 40
    remote.results["qualify"] = wrong
    with pytest.raises(manual.SessionError, match="not verified"):
        controller.advance()
    assert controller.store.load()["pending"]["action"] == "qualify"


def test_tag_repair_revalidates_bundle_before_another_push(project, monkeypatch):
    remote = Remote()
    controller, _ = session(project, remote)
    for _ in range(5):
        controller.advance()
    remote.results["tag"] = {"retry_safe": True}

    def invalid(_):
        raise manual.SessionError("Qualification attempt was superseded")

    monkeypatch.setattr(remote, "check_bundle", invalid)
    with pytest.raises(manual.SessionError, match="superseded"):
        controller.advance()
    assert [a for a, _ in remote.writes].count("tag") == 1


def test_modified_checksum_file_is_not_promoted_as_qualified(project, monkeypatch):
    from tests.test_release_qualification import _qualified_bundle
    api = backend(project, None)
    bundle, manifest = _qualified_bundle(api.work, monkeypatch, "legacy")
    api.repository = manifest["repository"]
    state = {"candidate_sha": manifest["source"]["sha"], "candidate_tree": manifest["source"]["tree"],
             "version": manifest["version"], "qualification": {"bundle": str(bundle),
             "manifest_sha256": manual.q.sha256_file(bundle / "qualification-manifest.json"),
             "run_id": manifest["workflow_run_id"], "attempt": 1,
             "artifacts": {a["kind"]: a for a in manifest["artifacts"]}}}

    class Client:
        def get(self, path):
            return {"id": state["qualification"]["run_id"], "run_attempt": 1,
                    "conclusion": "success", "status": "completed", "head_sha": state["candidate_sha"],
                    "head_branch": "main", "name": "Release qualification", "event": "workflow_dispatch",
                    "path": ".github/workflows/release-qualification.yml", "repository": {"full_name": api.repository},
                    "head_repository": {"full_name": api.repository}}

    monkeypatch.setattr(api, "client", Client())
    assert api.check_bundle(state)["version"] == manifest["version"]
    (bundle / "SHA256SUMS").write_text("mutated local checksum file\n")
    with pytest.raises(manual.SessionError, match="checksum file"):
        api.check_bundle(state)


def test_server_dispatch_id_survives_list_invisibility_without_guessing(project):
    sha = git(project, "rev-parse", "HEAD")
    created = manual.now()
    run = {"id": 42, "created_at": created, "run_attempt": 1, "head_sha": sha, "head_branch": "main",
           "event": "workflow_dispatch", "path": ".github/workflows/release-qualification.yml",
           "name": "Release qualification", "status": "in_progress", "repository": {"full_name": "example/agent-wiki"},
           "head_repository": {"full_name": "example/agent-wiki"}}

    class Client:
        def get(self, path):
            assert path == "/actions/runs/42"
            return run

        def list(self, *args):
            raise AssertionError("Exact returned run identity does not depend on listing visibility")

    api = backend(project, Client())
    pending = {"started_at": created, "before": {"run_ids": []}, "response": {"workflow_run_id": 42}}
    assert api._run({"candidate_sha": sha}, "qualify", pending) == run
    run["head_sha"] = "f" * 40
    with pytest.raises(manual.SessionError, match="identity differs"):
        api._run({"candidate_sha": sha}, "qualify", pending)


def test_ambiguous_dispatch_listing_and_future_metadata_cannot_be_adopted(project):
    sha = git(project, "rev-parse", "HEAD")
    created = manual.now()
    rows = [{"id": identity, "created_at": created, "head_sha": sha, "head_branch": "main"} for identity in (42, 43)]

    class Client:
        def list(self, *args):
            return rows

        def get(self, path):
            return {**rows[0], "created_at": "2099-01-01T00:00:00Z"}

    api = backend(project, Client())
    pending = {"started_at": created, "before": {"run_ids": []}}
    with pytest.raises(manual.SessionError, match="Ambiguous"):
        api._run({"candidate_sha": sha}, "qualify", pending)
    rows.pop()
    with pytest.raises(manual.SessionError, match="timestamp"):
        api._run({"candidate_sha": sha}, "qualify", pending)


def test_initialization_does_not_append_unrelated_work_directory_records(project):
    work = project / "private/existing"
    work.mkdir(parents=True)
    (work / "events.jsonl").write_text("unrelated retained evidence\n")
    controller = manual.Controller(manual.Store(project, work), Remote())
    with pytest.raises(manual.SessionError, match="fresh ignored"):
        controller.initialize("example/agent-wiki", git(project, "rev-parse", "HEAD"))
    assert (work / "events.jsonl").read_text() == "unrelated retained evidence\n"
    assert not (work / "state.json").exists()


def test_invalid_watch_bounds_and_ungranted_scope_do_not_read_credentials(project, monkeypatch, capsys):
    remote = Remote()
    controller, _ = session(project, remote, scopes=())

    def forbidden(*args, **kwargs):
        raise AssertionError("No credential lookup is needed")

    monkeypatch.setattr(manual.subprocess, "check_output", forbidden)
    with pytest.raises(SystemExit) as invalid:
        manual.main(["watch", "--root", str(project), "--work", str(controller.store.work), "--interval", "1"])
    assert invalid.value.code == 2
    assert manual.main(["advance", "--root", str(project), "--work", str(controller.store.work)]) == 0
    assert json.loads(capsys.readouterr().out)["observation"] == "awaiting_authorization"
    assert not remote.writes
