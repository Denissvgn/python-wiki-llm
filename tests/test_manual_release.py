"""Release-session authority, interruption and literal public-byte boundaries."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
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
    monkeypatch.setattr(api, "_tag", lambda *a, **k: {"source_sha": "1" * 40})
    monkeypatch.setattr(api, "_assets", lambda state: {"wheel.whl": "a" * 64, "source.tar.gz": "b" * 64, "SHA256SUMS": "c" * 64})
    monkeypatch.setattr(api, "_release", lambda tag: {"id": 1, "assets": [
        {"name": "wheel.whl", "state": "uploaded", "digest": "sha256:" + "f" * 64}]})
    writes = []
    monkeypatch.setattr(manual.subprocess, "run", lambda *a, **k: writes.append(a))
    with pytest.raises(manual.SessionError, match="digest differs"):
        api.perform({"candidate_sha": "1" * 40, "qualification": {"bundle": str(api.work)}}, {"action": "github-release"})
    assert not writes


def test_interrupted_notes_materialization_resumes_without_accepting_changed_notes(project, monkeypatch):
    api = backend(project, None)
    state = {"candidate_sha": git(project, "rev-parse", "HEAD"), "version": "9.0.0"}
    target = api.work / "product-notes.md"
    original = Path.open

    class Interrupted:
        def __init__(self, path, mode, args, kwargs):
            self.path, self.mode, self.args, self.kwargs = path, mode, args, kwargs

        def __enter__(self):
            self.stream = original(self.path, self.mode, *self.args, **self.kwargs)
            return self

        def write(self, data):
            self.stream.write(data[:5])
            self.stream.flush()
            raise OSError("Notes write interrupted")

        def __exit__(self, *args):
            self.stream.close()

    def partial(path, mode="r", *args, **kwargs):
        if path.parent == target.parent and path.name.startswith(target.name) and mode in {"w", "xb"}:
            return Interrupted(path, mode, args, kwargs)
        return original(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", partial)
    with pytest.raises(OSError, match="Notes write interrupted"):
        api._notes(state)
    assert not target.exists()
    monkeypatch.setattr(Path, "open", original)
    assert api._notes(state).read_bytes() == b"Product behavior.\n"
    target.write_text("Unreviewed changes\n", encoding="utf-8")
    with pytest.raises(manual.SessionError, match="Release notes changed"):
        api._notes(state)
    assert target.read_bytes() == b"Unreviewed changes\n"


def test_utf8_committed_notes_survive_a_non_utf8_process_locale(project):
    expected = "Café – public notes.\n"
    (project / "CHANGELOG.md").write_text("## [9.0.0] - 2026-11-05\n\n" + expected, encoding="utf-8")
    git(project, "add", "CHANGELOG.md")
    git(project, "commit", "-qm", "Unicode product notes")
    script = """import json,locale,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from release import manual_release as manual
api=manual.GitHubBackend.__new__(manual.GitHubBackend)
api.root=Path(sys.argv[2]);api.work=api.root/'private/locale-notes';api.work.mkdir(parents=True)
state={'candidate_sha':sys.argv[3],'version':'9.0.0'}
notes=api._notes(state).read_text(encoding='utf-8')
api._release_metadata(state,{'tag_name':'v9.0.0','draft':False,'prerelease':False,'body':notes})
print(json.dumps({'notes':notes,'utf8_mode':sys.flags.utf8_mode,'locale_encoding':locale.getencoding()}))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8=0", "-c", script,
         str(Path(manual.__file__).parents[1]), str(project), git(project, "rev-parse", "HEAD")],
        env={**manual.os.environ, "LC_ALL": "C", "LANG": "C", "PYTHONCOERCECLOCALE": "0"},
        capture_output=True, text=True, encoding="utf-8", timeout=30, check=False,
    )
    assert result.returncode == 0, result.stderr
    observed = json.loads(result.stdout)
    assert observed["utf8_mode"] == 0 and observed["notes"] == expected


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


def test_single_selected_push_destination_is_validated_without_changing_configuration(project):
    url = "git@github.com:example/agent-wiki.git"
    git(project, "remote", "add", "origin", url)
    api = backend(project, None)
    assert api._origin() == url
    assert git(project, "remote", "get-url", "--push", "--all", "origin") == url


def test_single_https_to_ssh_expansion_remains_supported_without_config_changes(project):
    selected = "git@github.com:example/agent-wiki.git"
    git(project, "remote", "add", "origin", "https://github.com/example/agent-wiki.git")
    git(project, "config", "url.git@github.com:.insteadOf", "https://github.com/")
    before = git(project, "config", "--local", "--list")
    assert backend(project, None)._origin() == selected
    assert git(project, "config", "--local", "--list") == before


@pytest.mark.parametrize("variable", ["insteadOf", "pushInsteadOf"])
def test_captured_explicit_push_cannot_apply_another_url_rewrite(project, monkeypatch, variable):
    selected = "git@github.com:example/agent-wiki.git"
    git(project, "remote", "add", "origin", "review-start")
    git(project, "config", "url." + selected + "." + variable, "review-start")
    git(project, "config", "url.git@github.com:unrelated/repository.git." + variable, selected)
    assert git(project, "remote", "get-url", "--push", "--all", "origin") == selected
    before = git(project, "config", "--local", "--list")
    real_git = manual.git
    writes = []

    def observed(root, *args, **kwargs):
        if args[0] in {"tag", "push"}:
            writes.append(args)
            raise AssertionError("Rewriting must be refused before tag mutation")
        return real_git(root, *args, **kwargs)

    monkeypatch.setattr(manual, "git", observed)
    with pytest.raises(manual.SessionError, match="matching URL rewrite"):
        backend(project, None).perform({"version": "9.0.0", "candidate_sha": "a" * 40}, {"action": "tag"})
    assert writes == [] and git(project, "config", "--local", "--list") == before


@pytest.mark.parametrize("second", ["git@github.com:unrelated/repository.git", "git@github.com:example/agent-wiki.git"])
def test_multiple_push_urls_are_rejected_before_tag_mutation(project, monkeypatch, second):
    selected = "git@github.com:example/agent-wiki.git"
    calls = []

    def configured(root, *args, **kwargs):
        calls.append(args)
        assert args == ("remote", "get-url", "--push", "--all", "origin"), "No tag mutation or push is allowed"
        return type("Completed", (), {"stdout": selected + "\n" + second + "\n"})()

    monkeypatch.setattr(manual, "git", configured)
    api = backend(project, None)
    with pytest.raises(manual.SessionError, match="exactly one"):
        api.perform({"version": "9.0.0", "candidate_sha": "a" * 40}, {"action": "tag"})
    assert calls == [("remote", "get-url", "--push", "--all", "origin")]


def test_tag_push_cannot_follow_origin_changes_after_its_final_validation(project, monkeypatch):
    selected = "git@github.com:example/agent-wiki.git"
    aliases = {"origin": selected}
    reads = 0
    pushes = []
    source_sha = "a" * 40

    def configured(root, *args, **kwargs):
        nonlocal reads
        if args == ("remote", "get-url", "--push", "--all", "origin"):
            reads += 1
            value = aliases["origin"]
            if reads == 2:
                # A concurrent local process changes the alias immediately
                # after its final validated value has been returned.
                aliases["origin"] = "git@github.com:unrelated/repository.git"
            return subprocess.CompletedProcess(args, 0, value + "\n")
        if args[:3] == ("config", "--null", "--get-regexp"):
            return subprocess.CompletedProcess(args, 1, "")
        if args[:2] == ("show-ref", "--verify"):
            return subprocess.CompletedProcess(args, 0, "")
        if args[:2] == ("cat-file", "-t"):
            return subprocess.CompletedProcess(args, 0, "tag\n")
        if args[:2] == ("rev-list", "-n"):
            return subprocess.CompletedProcess(args, 0, source_sha + "\n")
        assert args[0] == "push"
        pushes.append(args)
        assert args[1] == "--no-follow-tags"
        actual_destination = aliases.get(args[2], args[2])
        assert actual_destination == selected, "The write followed a changed alias"
        return subprocess.CompletedProcess(args, 0, "")

    monkeypatch.setattr(manual, "git", configured)
    api = backend(project, None)
    api.perform({"version": "9.0.0", "candidate_sha": source_sha}, {"action": "tag"})
    assert reads == 2 and aliases["origin"] != selected
    assert pushes == [("push", "--no-follow-tags", selected, "refs/tags/v9.0.0:refs/tags/v9.0.0")]


def test_tag_push_does_not_publish_unrelated_annotations_from_git_configuration(project, tmp_path, monkeypatch):
    git(project, "tag", "--annotate", "unrelated-version", "--message", "Other annotation")
    (project / "next.txt").write_text("Release source")
    git(project, "add", "next.txt")
    git(project, "commit", "-qm", "Release candidate")
    git(project, "tag", "--annotate", "v9.0.0", "--message", "Release annotation")
    git(project, "config", "push.followTags", "true")
    original_tags = git(project, "for-each-ref", "--format=%(refname) %(objectname)", "refs/tags")
    destination = tmp_path / "selected-repository.git"
    git(project, "init", "--bare", "-q", str(destination))
    api = backend(project, None)
    # Exercise real Git against a disposable local remote after destination
    # admission, without contacting the selected hosted repository.
    monkeypatch.setattr(api, "_origin", lambda: str(destination))
    api.perform({"version": "9.0.0", "candidate_sha": git(project, "rev-parse", "HEAD")}, {"action": "tag"})
    assert git(destination, "for-each-ref", "--format=%(refname)") == "refs/tags/v9.0.0"
    assert git(project, "for-each-ref", "--format=%(refname) %(objectname)", "refs/tags") == original_tags
    assert git(project, "config", "push.followTags") == "true"


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


@pytest.fixture
def artifact_cache(project):
    raw = artifact_zip("nested/decision.json")
    sha = git(project, "rev-parse", "HEAD")
    run = {"id": 42, "run_attempt": 1, "repository": {"id": 7}, "head_repository": {"id": 7}}
    artifact = {"id": 11, "name": "promotion-decision", "expired": False, "size_in_bytes": len(raw),
                "digest": "sha256:" + hashlib.sha256(raw).hexdigest(), "created_at": "2026-11-05T01:01:00Z",
                "updated_at": "2026-11-05T01:01:00Z", "workflow_run": {"id": 42, "head_sha": sha, "repository_id": 7, "head_repository_id": 7}}
    producer = {"name": "Verify qualified promotion input", "conclusion": "success", "head_sha": sha,
                "run_id": 42, "run_attempt": 1, "started_at": "2026-11-05T01:00:00Z", "completed_at": "2026-11-05T01:02:00Z"}

    class Client:
        downloads = 0

        def list(self, path, key):
            return [artifact] if key == "artifacts" else [producer]

        def archive(self, identity):
            assert identity == 11
            self.downloads += 1
            return raw

    return backend(project, Client()), {"candidate_sha": sha}, run, producer["name"]


def test_artifact_cache_payload_is_durable_before_final_name_and_retained_reuse(artifact_cache, monkeypatch):
    api, state, run, producer = artifact_cache
    events = []
    original_fsync, original_rename = manual.os.fsync, manual.os.rename

    def synchronized(descriptor):
        info = manual.os.fstat(descriptor)
        for path in [api.work, *api.work.rglob("*")]:
            observed = path.stat()
            if (observed.st_dev, observed.st_ino) == (info.st_dev, info.st_ino):
                events.append(("directory" if stat.S_ISDIR(info.st_mode) else "file", path))
                break
        return original_fsync(descriptor)

    def renamed(before, after):
        if manual.os.name != "nt":
            for path in before.rglob("*"):
                if path.is_file():
                    assert ("file", path) in events, path
            directories = [before / "files/nested", before / "files", before]
            indexes = [max(i for i, event in enumerate(events) if event == ("directory", path))
                       for path in directories]
            assert indexes == sorted(indexes), "Nested directories must become durable before their parents"
        events.append(("rename", after))
        return original_rename(before, after)

    monkeypatch.setattr(manual.os, "fsync", synchronized)
    monkeypatch.setattr(manual.os, "rename", renamed)
    files = api._artifact(state, run, "promotion-decision", producer)
    assert (files / "nested/decision.json").read_bytes() == b"{}"
    if manual.os.name != "nt":
        assert events.index(("rename", files.parent)) < max(
            i for i, event in enumerate(events) if event == ("directory", api.work)
        )
    events.clear()
    assert api._artifact(state, run, "promotion-decision", producer) == files
    assert api.client.downloads == 1
    if manual.os.name != "nt":
        assert all(("file", path) in events for path in files.parent.rglob("*") if path.is_file())
        assert events[-1] == ("directory", api.work)


@pytest.mark.parametrize("failure", ["payload", "parent-directory"])
def test_artifact_flush_failure_keeps_pending_intent_and_resumes_without_redispatch(
    project, artifact_cache, monkeypatch, failure,
):
    api, _, run, producer = artifact_cache

    class ArtifactRemote(Remote):
        def reconcile(self, state, pending):
            files = api._artifact(state, run, "promotion-decision", producer)
            return {**self.results[pending["action"]], "bundle": str(files)}

    remote = ArtifactRemote()
    controller, _ = session(project, remote, scopes=("qualify",))
    api.work = controller.store.work
    controller.advance()
    pending = controller.store.load()["pending"]
    sync_cache, sync_directory = manual.sync_artifact_cache, manual.sync_directory
    final = api.work / "promotion-decision-42-1"

    def fail_cache(folder, inventory):
        raise OSError("Artifact payload flush interrupted")

    def fail_directory(path):
        if path == api.work and final.exists():
            raise OSError("Artifact parent directory flush interrupted")
        return sync_directory(path)

    monkeypatch.setattr(manual, "sync_artifact_cache", fail_cache if failure == "payload" else sync_cache)
    monkeypatch.setattr(manual, "sync_directory", fail_directory if failure == "parent-directory" else sync_directory)
    with pytest.raises(OSError, match="flush interrupted"):
        controller.advance()
    failed = controller.store.load()
    assert failed["phase"] == "prepared" and failed["pending"] == pending
    assert len(remote.writes) == 1
    assert final.exists() is (failure == "parent-directory")
    attempts = list(api.work.glob("promotion-decision-42-1.incomplete-*"))
    retained = {path: path.read_bytes() for attempt in attempts for path in attempt.rglob("*") if path.is_file()}
    monkeypatch.setattr(manual, "sync_artifact_cache", sync_cache)
    monkeypatch.setattr(manual, "sync_directory", sync_directory)
    complete = controller.advance()
    assert complete["phase"] == "qualified" and complete["pending"] is None
    assert len(remote.writes) == 1
    assert (final / "files/nested/decision.json").read_bytes() == b"{}"
    assert all(path.read_bytes() == raw for path, raw in retained.items())
    assert api.client.downloads == (2 if failure == "payload" else 1)


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


@pytest.mark.parametrize("when", ["prepare", "after-intent"])
def test_candidate_change_during_preparation_cannot_reach_external_submission(project, monkeypatch, when):
    remote = Remote()
    controller, _ = session(project, remote)
    if when == "prepare":
        original = remote.prepare

        def prepare(state, action):
            (project / "concurrent-change.py").write_text("VALUE = 2\n")
            return original(state, action)

        monkeypatch.setattr(remote, "prepare", prepare)
    else:
        original = controller.store.save

        def save(state, event):
            value = original(state, event)
            if event == "intent-qualify":
                (project / "concurrent-change.py").write_text("VALUE = 2\n")
            return value

        monkeypatch.setattr(controller.store, "save", save)
    with pytest.raises(manual.SessionError, match="Commit source changes"):
        controller.advance()
    assert remote.writes == []
    assert controller.store.load()["pending"] is None


class TagClient:
    def __init__(self, *, source="a" * 40, kind="tag", absent=False, object_source="c" * 40):
        self.source, self.kind, self.absent, self.object_source = source, kind, absent, object_source
        self.calls = []

    def get(self, path):
        self.calls.append(path)
        if path == "/git/ref/tags/v9.0.0":
            if self.absent:
                raise manual.automation.APIError(404, "Tag is absent")
            return {"ref": "refs/tags/v9.0.0", "object": {"type": self.kind, "sha": self.object_source}}
        if path == "/git/tags/" + self.object_source:
            return {"sha": self.object_source, "tag": "v9.0.0", "object": {"type": "commit", "sha": self.source}}
        raise AssertionError("Unexpected selected-repository lookup: " + path)


def test_tag_reconciliation_uses_selected_repository_not_git_fetch_origin(project, monkeypatch):
    client = TagClient(source="b" * 40)
    api = backend(project, client)
    reads = []

    def fork_git(root, *args, **kwargs):
        reads.append(args)
        return type("Completed", (), {"stdout": "a" * 40 + "\trefs/tags/v9.0.0^{}\n"})()

    monkeypatch.setattr(manual, "git", fork_git)
    with pytest.raises(manual.SessionError, match="qualified commit"):
        api.reconcile({"version": "9.0.0", "candidate_sha": "a" * 40}, {"action": "tag"})
    assert reads == []
    assert client.calls == ["/git/ref/tags/v9.0.0", "/git/tags/" + "c" * 40]
    client.source = "a" * 40
    result = api.reconcile({"version": "9.0.0", "candidate_sha": "a" * 40}, {"action": "tag"})
    assert result is not None
    assert result["verified"] and result["refs"] == {
        "refs/tags/v9.0.0": "c" * 40, "refs/tags/v9.0.0^{}": "a" * 40}


@pytest.mark.parametrize("case", ["absent", "lightweight", "wrong-source", "retargeted-object"])
def test_wrong_selected_repository_tag_blocks_release_create_repair_and_completion(project, monkeypatch, case):
    client = TagClient(absent=case == "absent", kind="commit" if case == "lightweight" else "tag",
                       source="b" * 40 if case == "wrong-source" else "a" * 40)
    api = backend(project, client)
    state = {"version": "9.0.0", "candidate_sha": "a" * 40,
             "tag": {"refs": {"refs/tags/v9.0.0": "d" * 40 if case == "retargeted-object" else "c" * 40}}}
    monkeypatch.setattr(api, "check_bundle", lambda state: {"tag": "v9.0.0", "artifacts": []})
    writes = []
    monkeypatch.setattr(manual.subprocess, "run", lambda *args, **kwargs: writes.append(args))
    for operation in (lambda: api.perform(state, {"action": "github-release"}),
                      lambda: api.reconcile(state, {"action": "github-release"}),
                      lambda: api.verify_public(state)):
        with pytest.raises(manual.SessionError):
            operation()
    assert writes == []
    if case == "absent":
        assert api.reconcile(state, {"action": "tag"}) == {"retry_safe": True}


def test_public_cache_interrupted_write_retains_partial_attempt_and_resumes(project, monkeypatch):
    api = backend(project, None)
    raw = b"all qualified public bytes must survive"
    expected = hashlib.sha256(raw).hexdigest()
    monkeypatch.setattr(manual.hosted, "_http", lambda *args, **kwargs: (200, {}, raw))
    target = api.work / "public-downloads/pypi/wheel.whl"
    original = Path.open

    class Interrupted:
        def __init__(self, path):
            self.path = path

        def __enter__(self):
            self.stream = original(self.path, "xb")
            return self

        def write(self, data):
            self.stream.write(data[:7])
            self.stream.flush()
            raise OSError("Storage interrupted")

        def __exit__(self, *args):
            self.stream.close()

    def partial(path, mode="r", *args, **kwargs):
        if path.parent == target.parent and path.name.startswith("wheel.whl.incomplete-") and mode == "xb":
            return Interrupted(path)
        return original(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", partial)
    with pytest.raises(OSError, match="Storage interrupted"):
        api._public_bytes("pypi", "wheel.whl", "https://files.pythonhosted.org/wheel.whl", len(raw), expected)
    assert not target.exists()
    fragments = list(target.parent.glob("wheel.whl.incomplete-*"))
    assert len(fragments) == 1 and fragments[0].read_bytes() == raw[:7]
    monkeypatch.setattr(Path, "open", original)
    api._public_bytes("pypi", "wheel.whl", "https://files.pythonhosted.org/wheel.whl", len(raw), expected)
    assert target.read_bytes() == raw and fragments[0].read_bytes() == raw[:7]


def test_intent_file_and_supported_directory_flush_precede_external_effect(project, monkeypatch):
    import os
    import stat
    remote = Remote()
    controller, _ = session(project, remote)
    events = []
    fsync, replace, perform = os.fsync, os.replace, remote.perform

    def synchronized(descriptor):
        events.append("directory-flushed" if stat.S_ISDIR(os.fstat(descriptor).st_mode) else "file-flushed")
        return fsync(descriptor)

    def replaced(before, after):
        events.append("state-replaced" if after == controller.store.work / "state.json" else "other-replaced")
        return replace(before, after)

    def submitted(state, pending):
        events.append("effect")
        return perform(state, pending)

    monkeypatch.setattr(os, "fsync", synchronized)
    monkeypatch.setattr(os, "replace", replaced)
    monkeypatch.setattr(remote, "perform", submitted)
    controller.advance()
    assert events.index("file-flushed") < events.index("state-replaced") < events.index("effect")
    if os.name == "nt":
        # Windows retains flushed-file/atomic-replacement process recovery;
        # the controller deliberately does not claim a directory-flush API.
        assert "directory-flushed" not in events
    else:
        assert events.index("state-replaced") < events.index("directory-flushed") < events.index("effect")


def test_intent_directory_flush_failure_prevents_external_effect(project, monkeypatch):
    remote = Remote()
    controller, _ = session(project, remote)

    def fail(path):
        if path == controller.store.work:
            raise OSError("Intent directory did not become durable")

    monkeypatch.setattr(manual, "sync_directory", fail)
    with pytest.raises(OSError, match="did not become durable"):
        controller.advance()
    assert remote.writes == []
    assert controller.store.load()["pending"]["action"] == "qualify"


def test_new_session_directory_ancestors_are_flushed(project, monkeypatch):
    calls = []
    original = manual.sync_directory

    def record(path):
        calls.append(path)
        return original(path)

    monkeypatch.setattr(manual, "sync_directory", record)
    store = manual.Store(project, project / "private/nested/session")
    manual.Controller(store).initialize("example/agent-wiki", git(project, "rev-parse", "HEAD"))
    assert project in calls and project / "private" in calls and project / "private/nested" in calls
