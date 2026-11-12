"""Hosted authentication and guarded, resumable complete-snapshot import."""

from copy import deepcopy
import io
import json
from pathlib import Path
import subprocess
import tarfile
import zipfile

import pytest

from release import wiki_capture as capture
from tests.test_preflight import _git


def _tar(files, epoch):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w") as stream:
        for name, raw in files.items():
            member = tarfile.TarInfo(name)
            member.mode, member.mtime, member.size = 0o644, epoch, len(raw)
            stream.addfile(member, io.BytesIO(raw))
    return output.getvalue()


class Producer:
    def __init__(self, root):
        self.root = root
        self.sha = _git(root, "rev-parse", "HEAD")
        basis = capture._basis(root, self.sha)
        context = {
            k: basis[k]
            for k in (
                "source_sha",
                "source_tree",
                "wiki_tree",
                "version",
                "package_files_sha256",
                "platform",
                "tool_versions",
            )
        }
        context.update(
            python="3.13.18 (fixture)",
            helper={"status": "ready", "copies": basis["helper_copies"]},
        )
        stdout = b"Sync dry-run plan:\nRefresh wiki\nDRY-RUN: no files modified.\n"
        self.approved = capture.sha(capture.canonical(context) + b"\n" + stdout)
        self.request = {
            "repository": "Denissvgn/python-wiki-llm",
            "source_sha": self.sha,
            "run_id": 123,
            "attempt": 1,
            "operation": "apply",
            "approved_preview_sha256": self.approved,
        }
        self.run = {
            "id": 123,
            "run_attempt": 1,
            "workflow_id": 10,
            "head_sha": self.sha,
            "head_branch": "main",
            "event": "workflow_dispatch",
            "path": capture.WORKFLOW,
            "status": "completed",
            "conclusion": "failure",
            "repository": {"id": 7, "full_name": self.request["repository"]},
            "head_repository": {"id": 7, "full_name": self.request["repository"]},
        }
        self.job = {
            "id": 100,
            "run_id": 123,
            "head_sha": self.sha,
            "run_attempt": 1,
            "name": "capture",
            "status": "completed",
            "conclusion": "failure",
            "started_at": "2026-11-10T10:00:00Z",
            "completed_at": "2026-11-10T10:10:00Z",
            "steps": [
                {
                    "name": "Capture complete successful writer output",
                    "conclusion": "success",
                }
            ],
        }
        self.artifact = {
            "id": 200,
            "expired": False,
            "name": "reviewed-wiki-capture-apply-123-1",
            "created_at": "2026-11-10T10:05:00Z",
            "updated_at": "2026-11-10T10:05:00Z",
            "workflow_run": {
                "id": 123,
                "head_sha": self.sha,
                "head_branch": "main",
                "repository_id": 7,
                "head_repository_id": 7,
            },
        }
        self.snapshot = {"index.md": b"refreshed\n", "created.md": b"new\n"}
        archive = _tar(self.snapshot, basis["epoch"])
        manifest = {
            "schema_version": "llm-wiki-review-snapshot/v1",
            "candidate_sha": self.sha,
            "candidate_tree": basis["source_tree"],
            "workflow_run_id": 123,
            "run_attempt": 1,
            "wiki_dir": capture.WIKI,
            "limits": capture.LIMITS,
            "archive": {
                "filename": "wiki-review-snapshot.tar",
                "bytes": len(archive),
                "sha256": capture.sha(archive),
            },
            "entries": [
                {
                    "path": n,
                    "bytes": len(raw),
                    "sha256": capture.sha(raw),
                    "mode": 0o644,
                }
                for n, raw in self.snapshot.items()
            ],
            "content_bytes": sum(map(len, self.snapshot.values())),
        }
        preview = {
            "schema_version": capture.PREVIEW_SCHEMA,
            "candidate_sha": self.sha,
            "workflow_run_id": 123,
            "run_attempt": 1,
            "operation": "apply",
            "context": context,
            "preview_sha256": self.approved,
            "preview_stdout_sha256": capture.sha(stdout),
            "approved_preview_sha256": self.approved,
        }
        self.files = {
            "preview.json": capture.canonical(preview),
            "preview.stdout": stdout,
            "preview.stderr": b"",
            "sync.stdout": b"writer done\n",
            "sync.stderr": b"",
            "sync.log": b"writer done\n",
            "wiki-status-before.txt": b"",
            "wiki-status-after.txt": b" M docs/llm_wiki/index.md\n",
            "worktree-status-after.txt": b" M docs/llm_wiki/index.md\n",
            "wiki-diff.patch": b"review patch\n",
            "wiki-review-snapshot.json": capture.canonical(manifest),
            "wiki-review-snapshot.tar": archive,
        }
        convergence = {
            "schema_version": "llm-wiki-convergence/v1",
            "candidate_sha": self.sha,
            "wiki_dir": capture.WIKI,
            "sync": {"exit_code": 0, "plugins_enabled": False, "started": True},
            "checks": {
                n: True
                for n in (
                    "pre_sync_status_available",
                    "pre_sync_wiki_clean",
                    "pre_sync_worktree_clean",
                    "post_sync_status_available",
                    "post_sync_diff_available",
                    "worktree_changes_scoped_to_wiki",
                )
            },
            "evidence": {
                n: {"bytes": len(self.files[n]), "sha256": capture.sha(self.files[n])}
                for n in capture.CONVERGENCE_FILES
            },
        }
        self.files["convergence-result.json"] = capture.canonical(convergence)
        self.downloads = 0
        self.replace()

    def replace(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as stream:
            for name, raw in self.files.items():
                stream.writestr(name, raw)
        self.raw = output.getvalue()
        self.artifact.update(
            digest="sha256:" + capture.sha(self.raw), size_in_bytes=len(self.raw)
        )

    def get(self, path):
        assert path in {"/actions/workflows/10", "/actions/runs/123"}
        return {"path": capture.WORKFLOW} if "workflows" in path else deepcopy(self.run)

    def list(self, path, key):
        assert path in {
            "/actions/runs/123/attempts/1/jobs",
            "/actions/runs/123/artifacts",
        }
        return [deepcopy(self.job if key == "jobs" else self.artifact)]

    def archive(self, identifier):
        assert identifier == 200
        self.downloads += 1
        return self.raw


@pytest.fixture
def producer(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    files = {
        ".gitignore": "reports/\ndocs/llm_wiki/private/\n",
        "pyproject.toml": '[project]\nname="agent-wiki-cli"\nversion="9.0.0"\n[tool.setuptools.package-data]\nllm_wiki_cli=["extractors/ts_scripts/*"]\n',
        "src/llm_wiki_cli/__init__.py": "VALUE = 1\n",
        "src/llm_wiki_cli/extractors/ts_scripts/extract.js": "// fixture\n",
        "src/llm_wiki_cli/extractors/ts_scripts/package.json": "{}",
        "src/llm_wiki_cli/extractors/ts_scripts/package-lock.json": "{}",
        "release/runtime-policy.json": json.dumps(
            {
                "profiles": {
                    "knowledge-linux": {
                        "platform": "linux",
                        "arch": "x64",
                        "python": ["3.13.18"],
                    }
                }
            }
        ),
        "release/toolchain-lock.json": json.dumps(
            {
                "toolchains": {
                    "node": {"version_output": "v24.18.0"},
                    "npm": {"version_output": "11.16.0"},
                }
            }
        ),
        "release/knowledge-maintenance.json": json.dumps(
            {
                "wiki_dir": capture.WIKI,
                "src_dir": ".",
                "selection": ".llm-wiki/source-selection.json",
            }
        ),
        ".llm-wiki/source-selection.json": json.dumps(
            {
                "schema_version": "llm-wiki-source-selection/v1",
                "include": ["src", "pyproject.toml"],
                "exclude": [],
            }
        ),
        "docs/llm_wiki/index.md": "original\n",
        "docs/llm_wiki/removed.md": "remove me\n",
    }
    for name, text in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    _git(root, "init", "-q")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "capture source")
    return Producer(root)


def test_authentication_accepts_scoped_writer_drift_without_granting_release_authority(
    producer,
):
    result = capture.authenticate(producer.root, producer.request, client=producer)
    assert result["snapshot"] == producer.snapshot
    assert result["report"]["publication_authority"] is False
    assert producer.downloads == 1


@pytest.mark.parametrize(
    "fault",
    [
        "attempt",
        "fork",
        "expired",
        "producer",
        "timestamp",
        "digest",
        "size",
        "unexpected",
        "preview",
        "namespace",
        "helper",
        "snapshot",
    ],
)
def test_hosted_identity_or_content_faults_are_rejected(producer, fault):
    if fault == "attempt":
        producer.run["run_attempt"] = 2
    elif fault == "fork":
        producer.run["head_repository"]["id"] = 8
    elif fault == "expired":
        producer.artifact["expired"] = True
    elif fault == "producer":
        producer.job["steps"] = []
    elif fault == "timestamp":
        producer.artifact["updated_at"] = "2026-11-10T11:00:00Z"
    elif fault == "digest":
        producer.artifact["digest"] = "sha256:" + "0" * 64
    elif fault == "size":
        producer.artifact["size_in_bytes"] += 1
    else:
        if fault == "unexpected":
            producer.files["unexpected.py"] = b"raise Exception('do not execute')"
        elif fault == "preview":
            producer.files["preview.stdout"] += b"different plan"
        elif fault in {"namespace", "helper"}:
            preview = json.loads(producer.files["preview.json"])
            if fault == "namespace":
                preview["context"]["package_files_sha256"] = "0" * 64
            else:
                preview["context"]["helper"]["copies"]["extract.js"] = "0" * 64
            producer.files["preview.json"] = capture.canonical(preview)
        elif fault == "snapshot":
            producer.files["wiki-review-snapshot.tar"] += b"changed"
        producer.replace()
    with pytest.raises(ValueError):
        capture.authenticate(producer.root, producer.request, client=producer)
    assert not (producer.root / "unexpected.py").exists()


@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        "/absolute",
        "a/../b",
        "a\\b",
        "C:foo",
        "a//b",
        ".git/config",
        "a/.git/config",
        "AUX.txt",
        "trailing.",
    ],
)
def test_nonportable_and_escaping_names_are_rejected(name):
    with pytest.raises(ValueError):
        capture._name(name)


@pytest.mark.parametrize(
    "fault", ["duplicate", "case", "parent", "link", "mode", "content", "missing"]
)
def test_snapshot_decoder_rejects_conflicts_links_and_changed_members(producer, fault):
    manifest = json.loads(producer.files["wiki-review-snapshot.json"])
    raw = producer.files["wiki-review-snapshot.tar"]
    row = manifest["entries"][0]
    if fault in {"duplicate", "case", "parent"}:
        manifest["entries"].append(
            {
                **row,
                "path": row["path"]
                if fault == "duplicate"
                else row["path"].upper()
                if fault == "case"
                else row["path"] + "/child",
            }
        )
        manifest["content_bytes"] += row["bytes"]
    else:
        output = io.BytesIO()
        with (
            tarfile.open(fileobj=io.BytesIO(raw)) as original,
            tarfile.open(fileobj=output, mode="w") as changed,
        ):
            for index, member in enumerate(original):
                stream = original.extractfile(member)
                assert stream is not None
                data = stream.read()
                if index == 0:
                    if fault == "link":
                        member.type, member.linkname, member.size = (
                            tarfile.SYMTYPE,
                            "../outside",
                            0,
                        )
                    elif fault == "mode":
                        member.mode = 0o4644
                    elif fault == "content":
                        data = b"X" * len(data)
                    elif fault == "missing":
                        continue
                changed.addfile(member, io.BytesIO(data))
        raw = output.getvalue()
        manifest["archive"].update(bytes=len(raw), sha256=capture.sha(raw))
    basis = capture._basis(producer.root, producer.sha)
    with pytest.raises(ValueError):
        capture.snapshot_files(
            raw,
            manifest,
            source=producer.sha,
            tree=basis["source_tree"],
            run_id=123,
            attempt=1,
            epoch=basis["epoch"],
        )


def reviewed_plan(producer, monkeypatch):
    # Synthetic wiki isolates filesystem controls. Retained real capture replays
    # independently exercise the complete native storage audit.
    monkeypatch.setattr(capture, "storage_audit", lambda *_: {"ok": True})
    monkeypatch.setattr(capture, "audit_wiki", lambda *_: {"ok": True})
    folder = producer.root / "reports/capture"
    capture.fetch(producer.root, producer.request, folder, client=producer)
    return capture.preview_import(producer.root, folder, client=producer)


def test_preview_is_read_only_and_apply_preserves_complete_recovery_and_ignored_files(
    producer, monkeypatch
):
    private = producer.root / capture.WIKI / "private/notes.md"
    private.parent.mkdir()
    private.write_bytes(b"private preimage\n")
    plan = reviewed_plan(producer, monkeypatch)
    assert [r["operation"] for r in plan["operations"]] == [
        "create",
        "update",
        "remove",
    ]
    assert (producer.root / capture.WIKI / "index.md").read_bytes() == b"original\n"
    recovery = producer.root / "reports/recovery"
    result = capture.apply_import(
        producer.root, plan, plan["plan_sha256"], recovery, client=producer
    )
    assert result["status"] == "imported-review-required"
    assert private.read_bytes() == b"private preimage\n"
    assert not (producer.root / capture.WIKI / "removed.md").exists()
    journal = json.loads((recovery / "journal.json").read_bytes())
    before = capture.load_preimage(recovery / "preimage", journal["preimage"])
    assert (
        before["index.md"] == b"original\n" and before["removed.md"] == b"remove me\n"
    )
    assert before["private/notes.md"] == b"private preimage\n"
    assert (
        capture.apply_import(
            producer.root, plan, plan["plan_sha256"], recovery, client=producer
        )
        == result
    )
    assert producer.downloads == 1


@pytest.mark.parametrize(
    "fault",
    [
        "approval",
        "plan",
        "wiki",
        "source",
        "ignored-occupied",
        "new-file",
        "artifact",
        "lease",
    ],
)
def test_stale_review_and_foreign_edits_never_start_import(
    producer, monkeypatch, fault
):
    plan = reviewed_plan(producer, monkeypatch)
    approved = plan["plan_sha256"]
    wiki = producer.root / capture.WIKI
    if fault == "approval":
        approved = "0" * 64
    elif fault == "plan":
        plan["operations"] = []
    elif fault == "wiki":
        (wiki / "index.md").write_bytes(b"foreign edit")
    elif fault == "source":
        (producer.root / "src/llm_wiki_cli/__init__.py").write_bytes(b"CHANGED = 1\n")
    elif fault == "ignored-occupied":
        (producer.root / ".git/info/exclude").write_text("docs/llm_wiki/created.md\n")
        (wiki / "created.md").write_bytes(b"occupied")
    elif fault == "new-file":
        (wiki / "foreign.md").write_bytes(b"foreign")
    elif fault == "artifact":
        producer.artifact["digest"] = "sha256:" + "0" * 64
    elif fault == "lease":
        (producer.root / ".git/manual-release-active.json").write_text("{}")
    before = {
        p.relative_to(wiki).as_posix(): p.read_bytes()
        for p in wiki.rglob("*")
        if p.is_file()
    }
    with pytest.raises(ValueError):
        capture.apply_import(
            producer.root,
            plan,
            approved,
            producer.root / "reports/recovery",
            client=producer,
        )
    after = {
        p.relative_to(wiki).as_posix(): p.read_bytes()
        for p in wiki.rglob("*")
        if p.is_file() and not p.name.endswith(".lock")
    }
    assert after == before
    assert not (producer.root / "reports/recovery/journal.json").exists()


def test_interrupted_import_resumes_only_its_expected_images(producer, monkeypatch):
    from llm_wiki_cli.services import filesystem_guard

    plan = reviewed_plan(producer, monkeypatch)
    recovery = producer.root / "reports/recovery"
    original = filesystem_guard.atomic_write_guarded_bytes

    def interrupt(path, data, **kwargs):
        if path.name == "index.md":
            raise OSError("interrupted after creation")
        return original(path, data, **kwargs)

    monkeypatch.setattr(filesystem_guard, "atomic_write_guarded_bytes", interrupt)
    with pytest.raises(OSError, match="interrupted"):
        capture.apply_import(
            producer.root, plan, plan["plan_sha256"], recovery, client=producer
        )
    assert (producer.root / capture.WIKI / "created.md").read_bytes() == b"new\n"
    monkeypatch.setattr(filesystem_guard, "atomic_write_guarded_bytes", original)
    assert (
        capture.apply_import(
            producer.root, plan, plan["plan_sha256"], recovery, client=producer
        )["status"]
        == "imported-review-required"
    )


def test_later_harness_commit_keeps_capture_usable_and_selected_source_change_requires_new_preview(
    producer, monkeypatch
):
    (producer.root / "release/harness.py").write_text("# harmless harness change\n")
    _git(producer.root, "add", ".")
    _git(producer.root, "commit", "-qm", "later harness")
    plan = reviewed_plan(producer, monkeypatch)
    assert plan["candidate_sha"] != producer.sha
    (producer.root / "src/llm_wiki_cli/__init__.py").write_text(
        "# selected nonsemantic change\nVALUE = 1\n"
    )
    _git(producer.root, "add", ".")
    _git(producer.root, "commit", "-qm", "selected source")
    with pytest.raises(ValueError, match="selected source changed"):
        capture.preview_import(producer.root, Path(plan["capture"]), client=producer)


def test_occupied_fetch_destination_retains_previous_evidence(producer):
    folder = producer.root / "reports/capture"
    capture.fetch(producer.root, producer.request, folder, client=producer)
    before = (folder / "artifact.zip").read_bytes()
    with pytest.raises(ValueError, match="occupied"):
        capture.fetch(producer.root, producer.request, folder, client=producer)
    assert (folder / "artifact.zip").read_bytes() == before


def test_capture_namespace_uses_original_objects_despite_replace_refs(producer):
    before = capture._basis(producer.root, producer.sha)
    (producer.root / "src/llm_wiki_cli/__init__.py").write_text("changed\n")
    _git(producer.root, "add", ".")
    _git(producer.root, "commit", "-qm", "other source")
    replacement = _git(producer.root, "rev-parse", "HEAD")
    subprocess.run(
        ["git", "replace", producer.sha, replacement], cwd=producer.root, check=True
    )
    assert capture._basis(producer.root, producer.sha) == before


@pytest.mark.parametrize("kind", ["directory", "symlink"])
def test_occupied_creation_destination_is_rejected_during_preview(
    producer, monkeypatch, kind
):
    from llm_wiki_cli.services.filesystem_guard import ensure_guarded_directory

    path = producer.root / capture.WIKI / "created.md"
    if kind == "directory":
        ensure_guarded_directory(path)
    else:
        path.symlink_to(producer.root / capture.WIKI / "index.md")
    with pytest.raises(ValueError):
        reviewed_plan(producer, monkeypatch)
    assert (producer.root / capture.WIKI / "index.md").read_bytes() == b"original\n"


def test_foreign_edit_after_interruption_keeps_preimage_and_refuses_resume(
    producer, monkeypatch
):
    from llm_wiki_cli.services import filesystem_guard

    plan = reviewed_plan(producer, monkeypatch)
    recovery = producer.root / "reports/recovery"
    original = filesystem_guard.atomic_write_guarded_bytes

    def interrupt(path, data, **kwargs):
        if path.name == "index.md":
            raise OSError("interrupted")
        return original(path, data, **kwargs)

    monkeypatch.setattr(filesystem_guard, "atomic_write_guarded_bytes", interrupt)
    with pytest.raises(OSError):
        capture.apply_import(
            producer.root, plan, plan["plan_sha256"], recovery, client=producer
        )
    monkeypatch.setattr(filesystem_guard, "atomic_write_guarded_bytes", original)
    created = producer.root / capture.WIKI / "created.md"
    created.write_bytes(b"foreign edit")
    with pytest.raises(ValueError, match="foreign edits"):
        capture.apply_import(
            producer.root, plan, plan["plan_sha256"], recovery, client=producer
        )
    journal = json.loads((recovery / "journal.json").read_bytes())
    assert (
        capture.load_preimage(recovery / "preimage", journal["preimage"])["index.md"]
        == b"original\n"
    )
    assert created.read_bytes() == b"foreign edit"


def test_selected_source_comparison_ignores_replaced_capture_history(
    producer, monkeypatch
):
    root = producer.root
    (root / "src/llm_wiki_cli/__init__.py").write_text("# selected change\nVALUE = 1\n")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "selected source")
    target = _git(root, "rev-parse", "HEAD")
    # A replacement tree hides the selected change and leaves a harmless path
    # difference. Reading the replaced history would admit this stale capture.
    (root / "release/extra.py").write_text("# unrelated tree difference\n")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "replacement tree")
    replacement = _git(root, "rev-parse", "HEAD")
    _git(root, "checkout", "--detach", target)
    subprocess.run(["git", "replace", producer.sha, replacement], cwd=root, check=True)
    monkeypatch.setattr(capture, "storage_audit", lambda *_: {"ok": True})
    folder = root / "reports/capture"
    capture.fetch(root, producer.request, folder, client=producer)
    with pytest.raises(ValueError, match="selected source changed"):
        capture.preview_import(root, folder, client=producer)


def test_later_wiki_changes_require_fresh_preview_and_preserve_newer_ownership(
    producer, monkeypatch
):
    root = producer.root
    (root / capture.WIKI / "index.md").write_text("new authored prose\n")
    (root / capture.WIKI / ".llm-wiki-maintenance-adoption.json").write_text(
        "new owner sentinel\n"
    )
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "newer wiki owner and prose")
    folder = root / "reports/capture"
    capture.fetch(root, producer.request, folder, client=producer)
    calls = []
    monkeypatch.setattr(capture, "storage_audit", lambda *_: calls.append("audit"))
    with pytest.raises(ValueError, match="wiki baseline changed"):
        capture.preview_import(root, folder, client=producer)
    assert calls == []
    assert (root / capture.WIKI / "index.md").read_text() == "new authored prose\n"
    assert (
        root / capture.WIKI / ".llm-wiki-maintenance-adoption.json"
    ).read_text() == "new owner sentinel\n"
